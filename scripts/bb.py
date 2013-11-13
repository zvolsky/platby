# -*- coding: utf8 -*-

'''
importuje zbylé zůstatky ze spolecneaktivity.cz po Jirkově výpovědi
'''

import os
from bs4 import BeautifulSoup
import vfp
from mz_wkasa_platby import vs2id
from spolecneaktivity_cz import unformat_castka

def index():
    htm = vfp.filetostr(os.path.join(os.getcwd(),
                  'applications', 'platby', 'zakaznici.htm'))
    htm = unicode(htm, 'utf8')
    soup = BeautifulSoup(htm)
    zakaznici = soup('table')[5].tbody('tr')
    for zakaznik in zakaznici:
        vs = str(int(zakaznik('td')[0].a.string))
        castka = unformat_castka(zakaznik('td')[3].string)
        if castka>0:
            if int(vs)<675:
                __init(vs, castka)
            else:
                print 'odklad -', vs
                  # 100. 694 Katarinka
                  # 500. 685 1Pawell
        # ručně převedeni
                  # 150. 102 josito
                  # 100. 111 Pepa 
    db.commit()        
'''                    
        elif castka:
            nick = zakaznik('td')[1].string.strip()
            #print vs, nick, castka
            dluznici += 1
                  # -20. 502 michaelanov
                  # -20. 414 derive_cz
                  # -20. 402 Elisa
                  # -20. 401 Javier
    print celkem, pocet, dluznici
'''
        
#        vs2id(db, vs)

def __init(vs, castka):
    zakaznik = db(db.auth_user.vs==vs).select().first()
    if zakaznik:
        db.pohyb.insert(
              idauth_user=zakaznik.id,
              castka=castka,
              idma_dati=Uc_sa.oz_sa,
              iddal=Uc_sa.oz,
              datum=datetime.datetime.now(),
              popis="převod ze spolecneaktivity.cz",
              zakaznik=vs,
              vs=vs,
              ss=vs,
              id_pokynu='z sa.cz'
              )
        zakaznik.update_record(zaloha=float(zakaznik.zaloha) + castka)
    else:
        print 'failed -', vs

if __name__=='__main__':
    index()
