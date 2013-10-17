# coding: utf8

from datetime import datetime, timedelta, time
from mz_wkasa_platby import sa_ss, Uc_sa, vs2id
from bs4 import BeautifulSoup
from spolecneaktivity_cz import unformat_castka

@auth.requires_login()
def prehled():
    ss = sa_ss(auth.user.vs, auth.user.ss)[1] # spec.sym. na Jirkově
    sa_zal = __get_zaloha(ss)
    return dict(zaloha=auth.user.zaloha, sa_ss=ss, sa_zal=sa_zal)

@auth.requires_login()
def pohyby():
    class Celkem(object):
        vlozeno=vraceno=sa_vlozeno=z_sa_prevedeno=ozwk_vlozeno=ozwk_cerpano = 0
    uzivatel_id = auth.has_membership('admin'
        ) and vs2id(db, request.args(0)) or auth.user_id  # lze zadat parametrem
    pohyby = db(db.pohyb.idauth_user==uzivatel_id
                      ).select(orderby=~db.pohyb.datum)
    uzivatel = db.auth_user[uzivatel_id]
    nick = uzivatel.nick if request.args(0) else '' # promítání cizích adminem
    zaloha = uzivatel.zaloha
            # nelze auth.user.zaloha, když jsem připustil zadání id parametrem
    for pohyb in pohyby:
        if pohyb.idma_dati in Uc_sa.gl_ozwk and pohyb.iddal in Uc_sa.gl_ozwk:
            pohyb.castka = 0  # interní převod mezi 379 ve správě wKasa
        else:       # zobrazit uživateli
                 # gl_ozwk = (5,7)   # osobní účet ve správě na wKasa
                 # gl_sdr = (1,2,9)  # účty sdružení (pokladna a BÚ)
                 # oz_sa             # osobní účet u sa.cz
            # vložení a vrácení celkově
            ukaz_minus = False
            if pohyb.idma_dati in Uc_sa.gl_sdr:
                Celkem.vlozeno += pohyb.castka
            elif pohyb.iddal in Uc_sa.gl_sdr: 
                Celkem.vraceno += pohyb.castka
                ukaz_minus = True
            
            # vložení a převedení z sa.cz (vrácení nelze určit, dokud MD==None)
            if pohyb.iddal==Uc_sa.oz_sa:
                Celkem.sa_vlozeno += pohyb.castka
            elif pohyb.idma_dati==Uc_sa.oz_sa and pohyb.iddal in Uc_sa.gl_ozwk:
                Celkem.z_sa_prevedeno += pohyb.castka
            
            # vložení a čerpání z wKasa (vrácení nelze určit, dokud MD==None)
            if pohyb.iddal in Uc_sa.gl_ozwk:
                Celkem.ozwk_vlozeno += pohyb.castka
            elif pohyb.idma_dati in Uc_sa.gl_ozwk:      
                Celkem.ozwk_cerpano += pohyb.castka
                ukaz_minus = True

            # obrácení znaménka pro zobrazení
            if ukaz_minus:                
                pohyb.castka = -pohyb.castka
    return dict(zaloha=zaloha, pohyby=pohyby, Celkem=Celkem,
            Uc_sa=Uc_sa, nick=nick)

@auth.requires_membership('admin')
def vse():
    return dict(pohyby=db().select(db.pohyb.ALL))

@auth.requires_membership('admin')
def nedavne():
    response.view = 'platby/vse.html'
    datum_od = datetime.now()-timedelta(days=60)
    datum_od = datum_od.combine(datum_od.date(), time(0,0))
    return dict(pohyby=db(db.pohyb.datum>=datum_od).select(
          db.pohyb.ALL, orderby=~db.pohyb.datum))
        

@auth.requires_login()
def seber_jirkovi():
    db.zadost.insert(zadost=datetime.now(), ss=auth.user.ss, typ=1)
    return {}

@auth.requires_login()
def vratit_zalohu():
    pohyb = db((db.pohyb.zakaznik==auth.user.vs)
            &(db.pohyb.cislo_uctu!=None)
            &(db.pohyb.cislo_uctu!='')
            ).select().last()
    form = SQLFORM.factory(
            Field('cislo_uctu', length=30,
                    label = TFu("Číslo účtu"),
                    default=pohyb.cislo_uctu if pohyb else None,
                    requires=IS_NOT_EMPTY()),
            Field('kod_banky', length=10,
                    label = '/ ' + TFu("Kód banky"),
                    default=pohyb.kod_banky if pohyb else None,
                    requires=IS_NOT_EMPTY()),
            )
    if form.process().accepted:
        if sa_ss(auth.user.ss):
            db.zadost.insert(zadost=datetime.now(), ss=auth.user.ss, typ=1)
        db.zadost.insert(zadost=datetime.now(), ss=auth.user.ss, typ=2,
              cislo_uctu=form.vars.cislo_uctu, kod_banky=form.vars.kod_banky)
        db.commit()
        session.flash = TFu('zálohu po odečtení poplatku zašleme na %s/%s'
              %(form.vars.cislo_uctu, form.vars.kod_banky))
        redirect(URL('prehled'))
    return dict(form=form)

@auth.requires_membership('admin')
def vyridit():
    if len(request.args)==3: # 1/2=z_SA/na_BÚ, ss, castka po odečtu poplatku
        zadosti = db((db.zadost.ss==request.args[1])
                  &(db.zadost.typ==request.args[0])).select()
        for kolikata, zadost in enumerate(zadosti):
            if zadost.prevod is None:
                prevedeno = (request.args[2]
                            if kolikata==len(zadosti)-1
                            else 0.0)
                zadost.update_record(prevod=datetime.now(), prevedeno=prevedeno)
        db.commit()
        return "ok" 
    else:
        return "selhalo"

@auth.requires_membership('pokladna')
def zaloha():
    if len(request.args)==2:
        db(db.auth_user.vs==request.args(0)).update(
                                    zaloha=float(request.args(1)))
        redirect(URL('pohyby', args=request.args(0)))
    return 'bad parameters'

def __get_zaloha(ss):
    '''zjistí zákazníkovu nedávnou zálohu parsováním uloženého zakaznici.html
    '''
    # duplicitní s export_csv.predej_dluzne, odkud jsem to oprásknul
    zaloha = fdate = None
    try:
        fname = os.path.join(os.getcwd(),
                      'applications', 'platby', 'downloads', 'zakaznici.html')
        fdate = datetime.fromtimestamp(os.stat(fname).st_ctime)
        jirkovo = vfp.filetostr(fname)
        soup = BeautifulSoup(jirkovo)
        for zakaznik in soup.table('tr'):
            if str(zakaznik.td.a.string).strip().lstrip('0')==ss:
                zaloha = unformat_castka(zakaznik('td')[-4].string) 
                break
    except:
        pass
    return fdate, zaloha
