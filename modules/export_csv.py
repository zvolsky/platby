#!/usr/bin/env python
# -*- coding: utf8 -*-

u'''
export do csv pro předstírání Jirkovým Společným aktivitám, že načítají csv z banky

exportují se 2 typy záznamů:
"plánované"
  - příjem bankou s neznámým ss (možná dočasně, a později i toto budeme zadržovat)
  - zatím nepodporován příjem s neznámým ss na místě do pokladny (a asi ani nebude - musí se registrovat)
  - manuálně naplánované - k 13.10. sice naprogramováno, ale neodzkoušeno,
      a nebudeme to spouštět, nebude-li na to extra tlak.
      Pokud by se přece jen dodělávala možnost naplánování částky, nechť nemění
        zálohu. Zálohu totiž změní až samotný csv export. Je naprogramován tak,
        že zkontroluje stav zálohy v okamžiku exportu, a není-li dost peněz,
        částku sníží (k vynulování zálohy) nebo export stopne (při záloze <=0)
"dlužné"
  - má-li zůstatek na záloze a zjistí-li se, že Jirkovy aktivity mají pohledávku,
    exportuje se pohledávka, snížená o právě exportované plánované

db.systab musí obsahovat (viz fce csv.py: init_systab):
  kod: last_csv, hodnota: dd.mm.rrrr posledního exportu
  kod: csv_czk , hodnota: nnnnnn.nn zůstatek na účtu
'''

url_zakaznici = 'http://www.spolecneaktivity.cz/administrace/komunity/980eb0fc-3a9d-43b6-8028-59bf28fbb67e/zakaznici' 

import os
from datetime import datetime, date, timedelta, time
from time import sleep
from bs4 import BeautifulSoup
from spolecneaktivity_cz import sa_login, unformat_castka
from mz_wkasa_platby import Uc_sa
import vfp

def export_csv(db):
    rec_last_csv = db(db.systab.kod=='last_csv').select().first()
    datum_od = datetime.strptime(rec_last_csv.hodnota, '%d.%m.%Y'
                ).date()+timedelta(1)
    datum_do = date.today()-timedelta(1)
    csv_nejpozdeji = datetime.combine(datum_do, time(23,59,59))
    if datum_od>datum_do:
        print "Od posledního generování musí uplynout alespoň jeden den."
        return 0 

    vypis = ''
    sumplus = summinus = 0
    evidence = {}  # key je auth_user.id, value je celková částka z 379-11 záznamů
    pocet, vypis, sumplus, summinus = predej_planovane(
                    evidence, db, vypis, sumplus, summinus, csv_nejpozdeji)
    pocet, vypis, sumplus, summinus = predej_dluzne(
                    evidence, db, vypis, sumplus, summinus, pocet, csv_nejpozdeji)
    make_csv(db, vypis, sumplus, summinus, rec_last_csv, datum_od, datum_do)
    return pocet

def predej_planovane(evidence, db, vypis, sumplus, summinus, csv_nejpozdeji):
    '''podle stavu na 379-11 účtu (plánováno k převodu na jirkovo)'''
    predat = db((db.pohyb.iddal==Uc_sa.pro_sa)&(db.pohyb.id_pokynu==None)
              ).select()
        # protože naplánováním převodu u zákazníka se ještě nesmí měnit záloha,
        #  až zde, samotným převodem
    pocet = 0
    for predat1 in predat:
        vypis1, sumplus1, summinus1 = __predej1(
                                        predat1, evidence, db, csv_nejpozdeji)
        vypis += vypis1
        sumplus += sumplus1
        summinus += summinus1
        pocet += 1
    return pocet, vypis, sumplus, summinus

def __predej1(pohyb, evidence, db, csv_nejpozdeji):
    if pohyb.idauth_user:
        zakaznik = db(db.auth_user.id==pohyb.idauth_user).select(
                    db.auth_user.id, db.auth_user.ss).first()
        ss = zakaznik.ss or pohyb.ss
        evidence[zakaznik.id] = evidence.get(zakaznik.id, 0) + castka
    else:
        zakaznik = None
        ss = pohyb.ss
    if pohyb.iddal==Uc_sa.pro_sa:  # předem plánovaný převod na SA
        if zakaznik:
            castka = min(zakaznik.zaloha, pohyb.castka)
            if castka<=0:
                pohyb.update_record(castka=0, id_pokynu="nemá peníze")
                return '', 0, 0  # zrušeno pro nedostatek peněz na záloze
            if castka!=pohyb.castka:
                pohyb.update_record(castka=castka)
            zakaznik.update_record(zaloha=zakaznik.zaloha-castka)
        else:
            castka = pohyb.castka
        id_pohybu = db.pohyb.insert(
                idauth_user=pohyb.idauth_user, 
                idma_dati=Uc_sa.pro_sa,
                iddal=Uc_sa.oz_sa,
                datum=datetime.now(),
                castka=castka,
                cislo_uctu=pohyb.cislo_uctu,
                kod_banky=pohyb.kod_banky,
                nazev_banky=pohyb.nazev_banky,
                vs=pohyb.vs,
                ss=ss,
                ks=pohyb.ks,
                id_pokynu=str(pohyb.id)  
                )
        pohyb.update_record(id_pokynu=id_pohybu)
        vypis1, sumplus1, summinus1 = __add_csv(pohyb, csv_nejpozdeji)
        #db.commit() - commit je v kontroléru csv.py
        return vypis1, sumplus1, summinus1

def predej_dluzne(evidence, db, vypis, sumplus, summinus, pocet,
                    csv_nejpozdeji):
    #jirkovo = nacti_jirkovo_ze_souboru('jirkovo.html')
    br = sa_login("Mirek Zv.", "miiirek1+1")
    sleep(2)
    jirkovo = br.open(url_zakaznici).read()
    vfp.strtofile(jirkovo, os.path.join(os.getcwd(),
                  'applications', 'platby', 'downloads', 'zakaznici.html'))
    # mírná duplicita v controllers/platby.py, kde tento soubor parsuji
    #   ke zjištění aktuální zálohy
    soup = BeautifulSoup(jirkovo)
    for zakaznik in soup.table('tr'):
        sloupce = zakaznik('td')
        if len(sloupce):   # první řádek (hlavička) totiž <td> nemá
            planovano = unformat_castka(sloupce[-1].string)
            neuhrazeno = unformat_castka(sloupce[-2].string)
            zaloha = unformat_castka(sloupce[-4].string)
            chybi = planovano + neuhrazeno - zaloha
            if chybi>0:  
                symbol = str(sloupce[0].a.string).strip().lstrip('0')
                wk_zakaznik = db(db.auth_user.ss==symbol).select().first()
                if wk_zakaznik and wk_zakaznik.zaloha>0:
                    jeste_chybi = chybi - evidence.get(wk_zakaznik.id, 0)
                      # minus kolik jsme mu právě vyplatili v predej_planovane()
                    if jeste_chybi:
                        fl_zaloha = float(wk_zakaznik.zaloha)
                        popis = (u'z sa.cz poptával %s Kč' % jeste_chybi
                                ) if (jeste_chybi>fl_zaloha) else ''
                        posleme_mu = min(jeste_chybi, fl_zaloha) 
                        id_pohybu = db.pohyb.insert(
                            idauth_user=wk_zakaznik.id,
                            idma_dati=Uc_sa.oz,
                            iddal=Uc_sa.oz_sa,
                            datum=datetime.now(),
                            castka=posleme_mu,
                            ss=symbol,
                            popis=popis
                            )
                        wk_zakaznik.update_record(zaloha=fl_zaloha-posleme_mu)
                        pohyb = db(db.pohyb.id==id_pohybu).select().first()
                        vypis1, sumplus1, summinus1 = __add_csv(
                                          pohyb, csv_nejpozdeji)
                        vypis += vypis1
                        sumplus += sumplus1
                        summinus += summinus1
                        #db.commit() - commit je v kontroléru csv.py
                        pocet += 1
    return pocet, vypis, sumplus, summinus
            
def __add_csv(pohyb, csv_nejpozdeji):
    '''zapíše jednu transakci do csv
    '''
        #0;06.09.2013;85,00;670100-2207318349;6210;;2550;425;PAVEL  KUBIŠTA;Bezhotovostní příjem;;;BRE Bank S.A., organizační složka podniku;
    vypis1 = (
      '0;%(datum)s;%(castka)s;%(ucet)s;%(banka)s;%(ks)s;%(vs)s;%(ss)s;%(ss)s;%(bhp)s;;;banka;\n'
      % dict(datum=min(pohyb.datum, csv_nejpozdeji)
                    .strftime('%d.%m.%Y'),
            castka=('%0.2f' % pohyb.castka).replace('.',','),
            ucet=pohyb.cislo_uctu or '',
            banka=pohyb.kod_banky or '',
            bhp=u'Bezhotovostní příjem'.encode('cp1250'),
            ks=pohyb.ks or '',
            vs=pohyb.vs or '',
            ss=pohyb.ss or ''))
    sumplus1 = float(pohyb.castka) if pohyb.castka>0 else 0. 
    summinus1 = float(pohyb.castka) if pohyb.castka<0 else 0.
    return vypis1, sumplus1, summinus1

def make_csv(db, vypis, sumplus, summinus, rec_last_csv, datum_od, datum_do):
    maska = vfp.filetostr(os.path.join(os.getcwd(),
                  'applications', 'platby', 'others', 'maska.csv'))
    rec_csv_czk = db(db.systab.kod=='csv_czk').select().first()
    vychozi = float(rec_csv_czk.hodnota) 
    koncova = vychozi + sumplus + summinus
    vfp.strtofile(maska % dict(
          nyni=datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
          od=_no_zeros(datum_od),
          do=_no_zeros(datum_do),
          vychozi=_form_castka(vychozi),
          koncova=_form_castka(koncova),
          prijmy=_form_castka(sumplus),
          vydaje=_form_castka(summinus),
          zaznamy=vypis,
          suma=_form_castka(sumplus+summinus)
          ), datum_od.strftime('%Y_%m%d')+datum_do.strftime('_%m%d')+'.csv')
    rec_csv_czk.update_record(hodnota=str(koncova))
    rec_last_csv.update_record(hodnota=datum_do.strftime('%d.%m.%Y'))
    #db.commit() - commit je v kontroléru csv.py

def _no_zeros(datum):
    return datum.strftime('%d.%m.%Y').replace('.0','.').lstrip('0')
def _form_castka(castka):
    return ('%0.2f' % castka).replace('.',',')
