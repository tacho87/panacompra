import re
from sqlalchemy import or_
from sqlalchemy import func
import logging
from datetime import datetime
from time import sleep
from time import strptime
from time import strftime
from sqlalchemy.sql import exists
from sqlalchemy.orm import sessionmaker,undefer
from sqlalchemy import create_engine
from sqlalchemy import Date, cast
from sqlalchemy.exc import IntegrityError
from datetime import date
from classes.Compra import Compra,Base,Proveedor,Entidad,CompraHtml
from multiprocessing import Pool,cpu_count,Lock
from modules import parser
from math import ceil
import itertools
import os
import random

logger = logging.getLogger('db_worker')
CHUNK_SIZE=7000
CPU=2

db_url = os.environ['panadata_db']
logger.info('loading %s', db_url)
engine = create_engine(db_url, convert_unicode=True, echo=False)
Base.metadata.create_all(engine)
session_maker = sessionmaker(bind=engine)

def query_chunks(q, n):
  """ Yield successive n-sized chunks from query object."""
  for i in range(0, q.count(), n):
    yield list(itertools.islice(q, 0, n))

def chunks(l, n):
    """ return n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i+n]

def process_pending():
    session = session_maker()
    count_query = session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True)
    query = session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True).options(undefer('html')).limit(CHUNK_SIZE)
    pool = Pool(processes=CPU)
    while query.count() > 0:
        logger.info("%i compras pending", count_query.count())
#        results = [process_compra(c) for c in query.all()]
        cache = query.all()
        results = pool.map(process_compra, cache, int(ceil(len(cache)/CPU)))
        query.merge_result(results)
        session.commit()
    logger.info("compras added to db")

def process_compra(compra):
  modules = {
    'precio': parser.extract_precio,
    'description': parser.extract_description,
    'compra_type': parser.extract_compra_type,
    'dependencia': parser.extract_dependencia,
    'unidad': parser.extract_unidad,
    'objeto': parser.extract_objeto,
    'modalidad': parser.extract_modalidad,
    'provincia': parser.extract_provincia,
    'correo_contacto': parser.extract_correo_contacto,
    'nombre_contacto': parser.extract_nombre_contacto,
    'telefono_contacto': parser.extract_telefono_contacto,
    'fecha': parser.extract_fecha,
    'acto': parser.extract_acto,
    'entidad': parser.extract_entidad,
    'proponente': parser.extract_proponente
  }
  compra = parser.parse_html(compra,modules)
  return compra

def process_query(query,pool):
    cache = query.all()
    results = pool.imap_unordered(process_compra, cache, int(ceil(len(cache)/1)))
    return results

def reparse():
    session = session_maker()
    logger.info("Setting parsed to FALSE and parsing again")
    session.query(Compra).update({'parsed':False})
    session.commit()
    session.close()
    process_pending()

def query_not_visited():
    session = session_maker()
    cache = list(session.query(Compra).filter(Compra.visited == False).all())
    session.close()
    return cache

def count_not_visited():
    session = session_maker()
    count = session.query(Compra).filter(Compra.visited == False).count()
    session.close()
    return count

def reset_visited():
    session = session_maker()
    session.query(Compra.Compra).update({'visited':False})
    session.commit()
    session.close()

def find_or_create_proveedor(proveedor,session):
    instance = session.query(Proveedor).filter(Proveedor.nombre == proveedor).first()
    if instance:
       return instance
    else:
        p = Proveedor(proveedor)

        session.add(p)
        session.commit()
        return p

def find_or_create_entidad(entidad,session):
    instance = session.query(Entidad).filter(Entidad.nombre == entidad).first()
    if instance:
       return instance
    else:
        p = Entidad(entidad)
        session.add(p)
        session.commit()
        return p

def create_aquisitions(compra,aquisitions,session):
    for aq in aquisitions:
        aq.compra_id = compra.id
        session.add(aq)
        session.commit()
    return aquisitions


def create_compra_html(html,compra,session):
    ch = CompraHtml({'html':html,'compra_id':compra.id})
    session.add(ch)
    session.commit()
    return ch

def create_compra(compra,aquisitions):
    session = session_maker()
    html = compra.html
    try:
        if compra.proponente and compra.proponente != '':
            p = find_or_create_proveedor(compra.proveedor,session)
            compra.proveedor_id = p.id
        if compra.entidad and compra.entidad != '':
            e = find_or_create_entidad(compra.entidad,session)
            compra.entidad_id = e.id
        session.add(compra)
        session.commit()
        create_aquisitions(compra,aquisitions,session)
        create_compra_html(html,compra,session)
        logger.info('got new compra %s', compra.acto)
        session.expunge(compra)
    except IntegrityError as e:
        logger.debug('IntegrityError getting %s', compra.acto)
        session.rollback()
    except Exception as e:
        logger.error(e)
    finally:
        session.close()
    return compra

def del_compra(compra):
    session = session_maker()
    try:
        if session.query(Compra.url).filter(Compra.url == compra.url).filter(Compra.id != compra.id).first():
            session.delete(compra)
        session.commit()
        logger.info('deleted compra %s', compra.acto)
    except Exception as e:
        logger.error(e)
        session.rollback()
    finally:
        session.close()
    return compra

def get_all_urls():
    session = session_maker()
    try:
        urls = list(zip(*session.query(Compra.url).all()))[0]
        session.close()
        return {item.lower() for item in urls if item}
    except Exception as e:
        session.close()
        return set()

def query_all():
    session = session_maker()
    compras = session.query(Compra).filter(Compra.parsed == True).filter(Compra.precio > 0).filter(Compra.fecha != None).filter(Compra.proponente == "Editora Panamá América S.A.").all()
    session.close()
    return compras

def parse_acto(acto):
        return '-'.join(re.sub(r'\(|\)','',acto.lower()).split(','))

def build_url(year,acto,i):
    base = 'vistapreviacp.aspx?numlc=%s&esap=1&nnc=0&it=1'
    acto = '-'.join([str(year),parse_acto(acto),"%06d" % (i,)])
    return base % acto

def url_brute():
    visited = get_all_urls()
    session = session_maker()
    cache = session.execute("select distinct(split_part(acto,'-',2),split_part(acto,'-',3),split_part(acto,'-',4),split_part(acto,'-',5),split_part(acto,'-',6)) acto_ ,max(split_part(acto,'-',7)),min(split_part(acto,'-',7)) from compras where entidad like '%micro%'group by acto_")
    cache = cache.fetchall()
    session.close()
    random.shuffle(cache)
    for row in cache:
        try:
            for i in range(0,int(row[1])+1000):
                for year in [2012,2013,2014]:
                        url = build_url(year,row[0],i)
                        if url not in visited:
                                yield url
        except Exception as e:
            print(e)
            continue


def distinct_proponentes():
    session = session_maker()
    cache = session.execute("select distinct(proponente) from compras")
    cache = cache.fetchall()
    session.close()
    return { x[0] for x in cache }

def count_sum_per_day():
    session = session_maker()
    cache = session.execute("select count(*),sum(cast(precio as integer)),date(fecha) from compras group by date(fecha) order by date(fecha)")
    cache = cache.fetchall()
    session.close()
    return cache
