import httplib, urllib
import re
import logging
import json
import urlparse
import threading
from socket import timeout
from time import sleep
from bs4 import BeautifulSoup, SoupStrainer
from sqlalchemy.sql import exists
from classes.Compra import Compra
from random import shuffle

class UrlScraperThread(threading.Thread):
  """
  Scrapes pages for a category
  Parses compra_urls from scraped html and adds them to the Queue

  Maintains a copy of the har to keep track of pages
  Increments har file to increment pagination

  """

  def __init__(self, category, session, connection, update=False):
    threading.Thread.__init__(self)
    self.update = update
    self.data = dict(urlparse.parse_qsl(open('form.data').read()))
    self.category = category
    self.strainer = SoupStrainer('a')
    self.pages_regex = re.compile("(?:TotalPaginas\">)([0-9]*)")
    self.current_regex= re.compile("(?:PaginaActual\">)([0-9]*)")
    self.logger = logging.getLogger('UrlScraper')
    self.logger = logging.getLogger('UrlScraper')
    self.connection = connection
    self.session = session
    self.base_url = "/AmbientePublico/AP_Busquedaavanzada.aspx?BusquedaRubros=true&IdRubro="
    self.headers = {"Content-type": "application/x-www-form-urlencoded"}

  def reset_page(self):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = 1
  
  def increment_page(self):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = 1 + int(self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'])
  
  def set_page(self,page):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = int(page)

  def get_page(self):
    return int(self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'])

  def run(self):
    self.reset_page()
    self.parse_max_pages()
    shuffle(self.pages)
    self.logger.debug('starting category %s [%s pages]',self.category,len(self.pages))
    while self.pages:
      try:
        current_page = self.pages.pop()
        self.set_page(current_page)
        self.eat_urls_for_category(self.category)
      except Exception as e:
        self.pages.append(current_page)
        self.logger.debug('%s from %s', str(e),str(self))
        continue
    self.session.close()
    self.logger.info('%s dying', str(self))
    return

  def eat_urls_for_category(self,category):
    for url in self.parse_category_page(self.get_category_page()):
      self.session.add(Compra(url,category))
    self.session.commit()

  def get_category_page(self):
    response = self.connection.request("POST", str(self.base_url) + str(self.category), self.data, self.headers)
    return response.data

  def parse_category_page(self,html):
    soup = BeautifulSoup(html, "html.parser", parse_only=self.strainer)
    links = soup.find_all(href=re.compile("VistaPreviaCP.aspx\?NumLc"))
    remove_dupes = lambda x: not self.session.query(exists().where(Compra.url==(str(x)))).scalar()
    return filter(remove_dupes,[link.get('href') for link in links])

  def parse_max_pages(self):
    if self.update:
      pages = 1 
    else:
      html = self.get_category_page()
      pages = self.pages_regex.findall(html)[0].decode('latin-1', 'ignore')
    self.pages = [i + 1 for i in range(int(pages))]
  
  def __str__(self):
    return "<(UrlScraper: category[%i], pending[%i])>" % (int(self.category), (len(self.pages)))
