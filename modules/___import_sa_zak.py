#!/usr/bin/env python
# -*- coding: utf8 -*-

u'''
načte zákazníky z uložené stránky spolecneaktivity.cz/administrace/zakaznici
'''

from datetime import datetime
from bs4 import BeautifulSoup, NavigableString

def import_sa_zak(html, db):
    u'''načte zákazníky z uložené spolecneaktivity.cz/administrace/zakaznici
    '''
    soup = BeautifulSoup(html)
    sloupce = soup.table.thead.tr.find_all('th')
    klice = []
    for sloupec in sloupce:
        klice.append(sloupec.string.strip())
    zakaznici = soup.table.tbody.find_all('tr')
    for zakaznik in zakaznici:
        udaje = zakaznik.find_all('td')
        zaznam = {}
        for kolikaty, udaj in enumerate(udaje):
            if udaj.a:
                udaj_lepe = udaj.a.string.strip().strip('0')
            else:
                udaj_lepe = udaj.string
                udaj_lepe = udaj_lepe.strip() if udaj_lepe else ''
                if udaj_lepe[-3:]==u' Kč':
                    udaj_lepe = float(udaj_lepe[:-3].replace(',', '.')
                                  .replace(u'\xa0', ''))  # &nbsp;
            zaznam[klice[kolikaty]] = udaj_lepe
        zakaznik_save_to_w2(zaznam, db)

def zakaznik_save_to_w2(zaznam, db):
    vs = zaznam.get(u'SS')
    nick = zaznam.get(u'Uživatel')
    ode_dne = zaznam.get(u'Založen')
    if ode_dne:
        ode_dne = datetime.strptime(ode_dne, '%d.%m.%Y')
    email=zaznam.get(u'E-mail')
    zaloha=zaznam.get(u'Částka na záloze')
    
    tbl = db.auth_user
    stavajici = db(tbl.vs==zaznam[u'SS']).select().first()
    if stavajici:
        if zaloha!=stavajici.zaloha:
            stavajici.update_record(zaloha=zaloha)
        # ostatní už asi nenastanou, ale lze to tu mít
        if email and email!=unicode(stavajici.email, 'utf8'):
            stavajici.update_record(email=email)
        if nick and nick!=unicode(stavajici.nick, 'utf8'):
            stavajici.update_record(nick=nick)
        if ode_dne!=stavajici.ode_dne:
            stavajici.update_record(ode_dne=ode_dne)
    else:
        tbl.insert(
              email=email,
              nick=nick,
              vs=vs,
              zaloha=zaloha,
              ode_dne=ode_dne,
              )
    db.commit()             

#----------------------------------------------------------------------------
# vývoj/ladění
#   python web2py.py -M -S platby
#   os.chdir() do modules, kde je potřebný soubor
def _import_sa_zak_file(db):
    import vfp
    html = vfp.filetostr('zakaznici.htm')
    import_sa_zak(html, db)

#if __name__=='__main__':
#    _import_sa_zak_file(db=???)
