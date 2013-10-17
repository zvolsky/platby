#!/usr/bin/env python
# -*- coding: utf8 -*-

u'''
dočasně, pro prvotní import dat S.A.o.s. z FIO banky
trvale, pro import nových plateb
'''

import urllib2
from datetime import date, datetime
import vfp

import sys
addpath = 'site-packages/'
if not addpath in sys.path:
    sys.path.insert(1, addpath)

import import_fio_xml

token = vfp.filetostr(os.path.join(os.getcwd(),
                  'applications', 'platby', 'private', 'token.fio'))

# https://www.fio.cz/ib_api/rest/periods/<token>/2013-09-13/2013-09-14/transactions.xml
# https://www.fio.cz/ib_api/rest/last/<token>/transactions.xml

def import_obdobi(db, token, od, do):
    '''od,do jako date nebo ve formátu 2012-08-25
    '''
    if od and do:
        od = fix_date_str(od)
        do = fix_date_str(do)
        url = ('https://www.fio.cz/ib_api/rest/periods/%s/%s/%s/transactions.xml'
                % (token, od, do))
    else:
        url = ('https://www.fio.cz/ib_api/rest/last/%s/transactions.xml'
                % (token,))
    xml = urllib2.urlopen(url).read()
    vfp.strtofile(xml,'fio.xml')
    xml = unicode(xml, 'utf8')
        # jinak se utf8 dostane jako znaky do unicode,
        # takže např. len('Měna') bude =5
        # vypadávalo to potom chybou 2 (Měna!='CZK'), ale zajímavé je, že jen
        #  na localhostu, na alwaysdata se chovalo správně. Každopádně se zdá,
        #  že když je vstupní řetězec přímo v unicode, potíže nejsou ani
        #  na localhost, ani na alwaysdata
        # (bohužel jsem tento problém pochopil jen přibližně)
    return import_fio_xml.parse_fio_xml(
            xml,
            import_fio_xml.pohyb_save_to_w2,
            dict(db=db, tbl=db.pohyb)
            )

def fix_date_str(datum):
    if isinstance(datum, date):
        datum = datum.strftime('%Y-%m-%d')
    return datum

#----------------------------------------------------------------------------
# pro sa
#   python web2py.py -M -S platby
#   os.chdir() do modules, kde je potřebný soubor
def import_pohyby_sa(db, od=None, do=None):
    res_import_obdobi = import_obdobi(db, token, od, do)
    logfile = 'logs/import_uctu.log'
    if res_import_obdobi==(0,0,0):
        vfp.strtofile( '.', logfile, 1)
    else: 
        vfp.strtofile( "\n%s %s\n" % (
              datetime.now().strftime('%d.%m %H:%M'),
              res_import_obdobi),
              logfile, 1)

#----------------------------------------------------------------------------
# vývoj/ladění
def reset_pointer():
    url = ('https://www.fio.cz/ib_api/rest/set-last-id/%s/3539359519/'
                % (token,))
    xml = urllib2.urlopen(url).read()
