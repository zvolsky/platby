#!/usr/bin/env python
# -*- coding: utf8 -*-

u'''
zpracuje xml pohybů z API FIO banky
použití:
    parse_fio_xml(xml, f1, dict(f1_more_params))
              f1 je funkce, která se volá pro každý záznam
pro insert do web2py tabulky:
    parse_fio_xml(xml, pohyb_save_to_w2, dict(db=db, tbl=db.pohyb))
'''

from datetime import datetime
from bs4 import BeautifulSoup, NavigableString
from mz_wkasa_platby import je_zakaznik, Uc_sa
import vfp

def parse_fio_xml(xml, f1, f1_more_params={}):
    u'''parsuje xml pohyby z API FIO banky
    každý pohyb parsuje do dictionary 'zaznam',
      se kterou zavolá f1(zaznam, **f1_more_params)
    načítání pokračuje, dokud f1() vrací None nebo True
    vrátí tuple (číslo chyby, načteno záznamů, zjištěno záznamů)
    číslo chyby:
      1 xml není úplné, nenalezeno </AccountStatement>
      2 načítání přerušeno kvůli podivnému záznamu (recno = načteno_záznamů+1)
    '''

    # kontrola úplnosti
    if not xml[-19:]=='</AccountStatement>':
        return 1, 0, 0   # xml není úplné
    cislo_chyby = 0

    odpoved = BeautifulSoup(xml).accountstatement
    # parsování
        # TransactionList.Transaction.column_nnn name="jmeno_polozky"
    tslist = odpoved.transactionlist
    if tslist: 
        pohyby = tslist.find_all('transaction')
        zjisteno_pohybu = len(pohyby)
        nacteno_pohybu = 0
        #try:
        for pohyb in pohyby:
            if f1(parse_fio_pohyb(pohyb), **f1_more_params)==False:                                     
                cislo_chyby = 2  # přerušeno kvůli podivnému záznamu
                break
            nacteno_pohybu += 1
        #except:
        #    cislo_chyby = 3  # chyba při provádění kódu
        return cislo_chyby, nacteno_pohybu, zjisteno_pohybu
    else:
        return 0, 0, 0  # bez chyby, ale nejsou žádné pohyby

def parse_fio_pohyb(pohyb):
    u'''parsuje jeden pohyb z API FIO banky do dictionary
    pohyb je bs4.Tag <Transaction> (bs4=BeautifulSoup4 package)
    vrátí dictionary (klíče jsou u'<atribut_podle_dokumentace_FIO>')
    '''
    zaznam = {}
    for column in pohyb.find_all(True):  # True=všechny tagy, ne stringy
        jmeno_polozky = column['name']
        newval = column.string
        zaznam[jmeno_polozky] = newval.strip() if newval else ''
    return zaznam
    
def pohyb_save_to_w2(zaznam, db, tbl, currency_required='CZK'):
    u'''jednotlivý pohyb na účtu uloží do web2py tabulky tbl
    zaznam: pohyb jako dictionary, klíče jsou u'<atribut_podle_dokumentace_FIO>'
    db: např.(obvykle) db
    tbl: např. db.banka, struktura viz níže vkládaná pole
    currency_required: zastaví import, pokud pohyb není v uvedené měně
    '''
    
    id_pohybu = zaznam.get(u'ID pohybu')
    if len(db(db.pohyb.id_pohybu==id_pohybu).select())>0:
        return True  # nesmí vracet False, jinak ukončí import
    if zaznam.get(u'Měna')!=currency_required:
        return False  # určeno jen pro stále stejnou měnu -> chyba importu 
    datum = zaznam.get(u'Datum')
    if datum:
        datum = datetime.strptime(datum, '%Y-%m-%d+%H:%M')
    msg = _sestav_msg(zaznam)
    castka = float(zaznam.get(u'Objem'))
    if castka!=0:
        zakaznik = None
        vs = zaznam.get(u'VS', '').lstrip('0')
        ss = zaznam.get(u'SS', '').lstrip('0')
        idauth_user = [None] # vrátí parametrem funkce je_zakaznik
        if castka>0:
            idmd = Uc_sa.bezny
            if vs=='111':
                iddal = Uc_sa.dary
            elif je_zakaznik(db, ss, idauth_user):  # akceptujeme ve VS i v SS
                zakaznik = ss
                iddal = Uc_sa.oz
            elif je_zakaznik(db, vs, idauth_user):  # akceptujeme ve VS i v SS
                zakaznik = vs
                iddal = Uc_sa.oz
            elif ss:
                iddal = Uc_sa.pro_sa # zatím přepouštíme neregistrované na SA
            else:
                iddal = None
        else:
            idmd = None
            if je_zakaznik(db, ss, idauth_user):
                zakaznik = ss
            iddal = Uc_sa.bezny 
        tbl.insert(
              idauth_user = idauth_user[0], 
              idma_dati = idmd,
              iddal = iddal,
              datum = datum,
              castka = abs(castka),
              cislo_uctu = zaznam.get(u'Protiúčet'),
              kod_banky = zaznam.get(u'Kód banky'),
              nazev_banky = zaznam.get(u'Název banky'),
              zakaznik = zakaznik,
              vs = vs,
              ss = ss,
              ks = zaznam.get(u'KS', '').lstrip('0'),
              popis = msg,
              id_pohybu = id_pohybu,
              id_pokynu = zaznam.get(u'ID Pokynu'),
              )
        if zakaznik:
            platce = db(db.auth_user.id==idauth_user[0]).select().first()
            platce.update_record(zaloha=max(0, float(platce.zaloha)+castka))
        db.commit()
    '''                                                     M=vždy O=občas
    ID pohybu M 12n Jedinečné číslo ID pohybu 1158152824
    Datum M dd-mm-rrrr+GMT datum pohybu ve tvaru 2012-07-27+02:00
    Objem M 18d velikost přijaté/odeslané částky 12225.25
    Měna M 3!x měna přijaté /odeslané částky dle standardu ISO 4217 EUR
    Protiúčet O 255x číslo protiúčtu 2212-2000000699
    Název protiúčtu O 255x název protiúčtu Béďa Trávníček
    Kód banky O 10x číslo banky protiúčtu 2010
    Název banky O 255x název banky protiúčtu Fio banka, a.s.
    KS O 4n konstantní symbol 0558
    VS O 10n variabilní symbol 1234567890
    SS O 10n specifický symbol 1234567890
    Uživatelská identifikace O 255x uživatelská identifikace Nákup: PENNY MARKET
    Zpráva pro příjemce O 140x zpráva pro příjemce Libovolný text
    Typ M 255x typ operace Platba převodem uvnitř banky
    Provedl O 50x oprávněná osoba, která zadala příkaz Béďa Trávníček
    Upřesnění O 255x upřesňující informace k pohybu, např. kurz 15.90 EUR
    Komentář O 255x upřesňující informace Hračky pro děti v PENNY MARKET
    BIC O 11x bankovní ident. kód banky protiúčtu dle ISO 9362 UNCRITMMXXX
    ID Pokynu O 12n číslo příkazu 2102382863
    '''

def _sestav_msg(zaznam):
    msg = ''
    msg1 = zaznam.get(u'Typ')
    msg = _msg_add(msg, msg1)
    msg1 = zaznam.get(u'Uživatelská identifikace')
    msg = _msg_add(msg, msg1)
    msg1 = zaznam.get(u'Upřesnění')
    msg = _msg_add(msg, msg1)
    msg1 = zaznam.get(u'Komentář')
    msg = _msg_add(msg, msg1)
    msg1 = zaznam.get(u'Název protiúčtu')
    if msg1:
        msg += T(u'Vlastník účtu') + ': ' + msg1 + '\n' 
    msg1 = zaznam.get(u'Zpráva pro příjemce')
    if msg1:
        msg += T(u'Pro příjemce') + ': ' + msg1 + '\n' 
    msg1 = zaznam.get(u'BIC')
    if msg1:
        msg += T(u'BIC banky') + ': ' + msg1 + '\n' 
    msg1 = zaznam.get(u'Provedl')
    if msg1:
        msg += T(u'Zadal') + ': ' + msg1 + '\n'
    return msg.rstrip('\n')

def _msg_add(msg, msg1):
    if msg1 and not msg1 in msg.split('\n'):
        msg += msg1 + '\n' 
    return msg    

#----------------------------------------------------------------------------
def T(msg):
    '''dočasně: lokální náhrada web2py překladu T()'''
    return msg

#----------------------------------------------------------------------------
# vývoj/ladění
def _test_import_fio_xml(db):
    import vfp
    xml = vfp.filetostr('fio_vzorek.xml')
    parse_fio_xml(xml, pohyb_save_to_w2, dict(db=db, tbl=db.pohyb))

#if __name__=='__main__':
#    _test_import_fio_xml(db=???)
