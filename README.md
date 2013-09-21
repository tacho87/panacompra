panacompra
==========

tool para recolectar data de panacompra


Dependencies
-------------
* BeautifulSoup
* sqlalchemy 
* pyyaml
* requests 
* python 2.7


To-Do
-------
* collect more data (more regex)

usage
------
```bash
python panacompra.py --help

usage: panacompra.py [-h] [--send] [--update] [--sync] [--revisit] [--reparse]
                     [--pending] [--url URL]

Dataminer for Panacompra

optional arguments:
  -h, --help  show this help message and exit
  --send      send db
  --update    update db
  --sync      sync db
  --revisit   revisit db
  --reparse   reparse db
  --pending   pending db
  --url URL
```


legal stuff
------------
Copyright (C) 2013  Ivan Barria

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
