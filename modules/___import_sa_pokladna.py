#!/usr/bin/env python
# -*- coding: utf8 -*-

u'''
prvotní import - načte pokladnu z Jirkova webu za všechna období
'''

#url_pokladna = 'C:\\Users\\Lenka\\Dropbox\\mz\\SA\\zalohy\\131009_pokladna\\'
url_pokladna = 'pok/'
url_zakaznici = 'http://www.spolecneaktivity.cz/administrace/komunity/980eb0fc-3a9d-43b6-8028-59bf28fbb67e/zakaznici' 

from datetime import datetime
from time import sleep
from bs4 import BeautifulSoup
from spolecneaktivity_cz import unformat_castka, sa_login
from mz_wkasa_platby import Uc_sa
import vfp

br = sa_login("Mirek Zv.", "miiirek1+1")
sleep(2)

def import_sa_pokladna(db):
    u'''prvotní import - načte pokladnu z Jirkova webu za všechna období
    '''
    dmoji = getmoji(db)  # dtto, ale z cílové databáze: d[nick] = (id, vs)
    dzakaznici = getzakaznici()   # slovník: d[nick] = ss
    for rok in xrange(2011,2014):
        for mesic in xrange(1,13):
            rrrrmm = str(rok)+str(100+mesic)[1:]
            if '201104'<=rrrrmm<='201309':
                html = vfp.filetostr(url_pokladna+rrrrmm+'.htm')
                html = unicode(html,'utf8')
                pokladna1(html, db, dzakaznici, dmoji)
                print rok, mesic   # vypisuje, co bylo commitnuto

def getmoji(db):
    'zákazníci podle aktuální wKasa databáze'
    dmoji = {}
    zakaznici = db(db.auth_user).select(
              db.auth_user.id, db.auth_user.vs, db.auth_user.nick)
    for zakaznik in zakaznici:
        dmoji[zakaznik.nick.decode('utf8')] = (zakaznik.id, zakaznik.vs)
    return dmoji
    
def getzakaznici():
    'zákazníci podle Jirkova webu'
    dzakaznici = {}
    html = br.open(url_zakaznici).read() 
    soup = BeautifulSoup(html)
    zakaznici = soup.table.tbody.find_all('tr')
    for zakaznik in zakaznici:
        udaje = zakaznik.find_all('td')
        dzakaznici[udaje[1].string.strip()] = int(udaje[0].a.string)
    return dzakaznici

def pokladna1(html, db, dzakaznici, dmoji):
    soup = BeautifulSoup(html)
    pohyby = soup.table.tbody.find_all('tr')
    for pohyb in pohyby:
        dpohyb = {}
        udaje = pohyb.find_all('td')
        dpohyb['ks'] = '??' if (u'unread' in pohyb.get('class', '')) else '3#'
        dpohyb['datum'] = datetime.strptime(udaje[1].string.strip(), '%d.%m.%Y')
        dpohyb['idorganizator'] = dmoji.get(string(udaje[2].a), [None])[0]
        dpohyb['id_pohybu'] = udaje[4].string.strip()   # číslo dokladu
        dpohyb['ss'] = string(udaje[6].a).strip().lstrip('0')
        dpohyb['popis'] = (udaje[8].string.strip() + '\n'
                          + udaje[9].string.strip()).strip()
        zakaznik = string(udaje[10].a)
        dpohyb['vs'] = dzakaznici.get(zakaznik, '')
        dpohyb['idauth_user'] = dmoji.get(zakaznik, [None])[0]
        typ = udaje[3].string.strip()
        castka = unformat_castka(udaje[5].string)
        if castka<0:
            dpohyb['castka'] = -castka
            if u'úhrada ' in typ and u' služby' in typ:
                dpohyb['idma_dati'] = Uc_sa.akce
            else:
                dpohyb['idma_dati'] = Uc_sa.provoz
            dpohyb['iddal'] = Uc_sa.pokladna
        elif typ==u'výběr z bankomatu':
            vfp.strtofile(
                    '%s %s\n'%(dpohyb['datum'].strftime('%d.%m.%Y'), castka),
                    'bankomat.log', 1)
            continue
        else:
            dpohyb['castka'] = castka
            dpohyb['idma_dati'] = Uc_sa.pokladna
            if typ==u'příjem příspěvku':
                dpohyb['iddal'] = Uc_sa.dary
            elif typ==u'příjem za službu od zákazníka':
                dpohyb['iddal'] = Uc_sa.oz_sa
            else:
                dpohyb['iddal'] = Uc_sa.vynos
        db.pohyb.insert(
                datum=dpohyb['datum'],
                id_pokynu='web SA',
                id_pohybu=dpohyb['id_pohybu'],
                ss=dpohyb['ss'],
                popis=dpohyb['popis'],
                vs=dpohyb['vs'],
                zakaznik=dpohyb['vs'],
                idauth_user=dpohyb['idauth_user'],
                castka=dpohyb['castka'],
                idma_dati=dpohyb['idma_dati'],
                iddal=dpohyb['iddal'],
                cislo_uctu=zakaznik,
                ks=dpohyb['ks']
                )   # idorganizator=dpohyb['idorganizator'], jinak nesmysly
    db.commit()  # uložit vždy 1 měsíc pokladny

def string(tag):
    if tag:
        return tag.string
    else:
        return u''
    
#----------------------------------------------------------------------------
# vývoj/ladění

#if __name__=='__main__':
#
