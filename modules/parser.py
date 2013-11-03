import re
from decimal import Decimal
from datetime import datetime
from bs4 import BeautifulSoup,SoupStrainer

def is_error_page(soup):
    error = soup.find(text=re.compile("unhandled exception"))
    if error or len(soup) == 0:
        return True
    return False

def parse_html(compra,methods):
    soup = BeautifulSoup(compra.html,'html.parser',parse_only=SoupStrainer('tr'), from_encoding='ISO-8859-1')
    if not is_error_page(soup):
        for name,method in methods.items():
            val = method(soup)
            setattr(compra,name,val)
    compra.parsed = True
    return compra 

def parse_date(date):
  try:
    date = date.replace('.','').upper()
    date = datetime.strptime(date,"%d-%m-%Y %I:%M %p") 
  except Exception as e:
    print(e)
    date= None
  return date

def parse_precio(precio):
  precio = re.sub(r'[^\d.]', '',precio) #remove non digits
  precio = re.sub(r'^.', '',precio) #remove leading period
  if not precio == "":
    precio = Decimal(precio)
  else:
    precio = Decimal(0) 
  return precio

def sanitize(string):
  return str(re.sub(' +',' ', string)) #no repeated spaces

def parse_and_sanitize(string,name):
  string = sanitize(string)
  if name == "fecha":
    string = parse_date(string)
  elif name == 'precio' or name == 'precio_cd':
    string = parse_precio(string)
  elif name == 'proponente':
    string = sanitize(string[:199])
  elif name == 'telefono_contacto':
    string = string[:14]
  return string

def extract_precio(soup):
    try:
        precio = soup.find('td',text='Precio Referencia:').find_next_sibling('td').string
    except AttributeError:
        precio = soup.find('td',text=re.compile('Monto de la Contrataci.')).find_next_sibling('td').string 
    finally:
        return parse_precio(precio)
    
def extract_description(soup):
    a = sanitize(soup.find('td',text=re.compile('Descripci.')).find_next_sibling('td').string)
    return a

def extract_compra_type(soup):
    return sanitize(soup.find('td',text='Tipo de Procedimiento:').find_next_sibling('td').string)
    
def extract_dependencia(soup):
    return sanitize(soup.find('td',text='Dependencia:').find_next_sibling('td').string)

def extract_unidad(soup):
    return sanitize(soup.find('td',text='Unidad de Compra:').find_next_sibling('td').string)
    
def extract_objeto(soup):
    return sanitize(soup.find('td',text='Objeto Contractual:').find_next_sibling('td').string)
    
def extract_modalidad(soup):
    modalidad = soup.find('td',text=re.compile('Modalidad.'))
    if modalidad is not None:
        return sanitize(modalidad.find_next_sibling('td').string)
    return None
    
def extract_provincia(soup):
    provincia = soup.find('td',text='Provincia de Entrega:')
    if provincia is not None:
        return sanitize(provincia.find_next_sibling('td').string)
    return None
    
def extract_correo_contacto(soup):
    return sanitize(soup.find('td',text='Datos de Contacto').parent.find_next_sibling('tr').find_next_sibling('tr').find_next_sibling('tr').find_next_sibling('tr').find('td').find_next_sibling('td').string)
    
def extract_nombre_contacto(soup):
    return sanitize(soup.find('td',text='Datos de Contacto').parent.find_next_sibling('tr').find('td').find_next_sibling('td').string)
    
def extract_telefono_contacto(soup):
    return sanitize(soup.find('td',text='Datos de Contacto').parent.find_next_sibling('tr').find_next_sibling('tr').find_next_sibling('tr').find('td').find_next_sibling('td').string)

def extract_fecha(soup):
    return parse_date(soup.find('td',text=re.compile('Fecha de Pub.*')).find_next_sibling('td').string)
    
def extract_acto(soup):
    return sanitize(soup.find('td',text=re.compile('.Acto.')).find_next_sibling('td').string)

def extract_entidad(soup):
    return sanitize(soup.find('td',text='Entidad:').find_next_sibling('td').string)
    
def extract_proponente(soup):
    proponente = soup.find('td',text='Proponente Seleccionado')
    if proponente is not None:
        return sanitize(proponente.parent.find_next_sibling('tr').find('td').find_next_sibling('td').string)
    return None

