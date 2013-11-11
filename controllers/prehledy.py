# coding: utf8

from datetime import datetime, timedelta, time, date
from mz_wkasa_platby import Uc_sa

def clenove():
    clen_id = db(db.auth_group.role=='člen sdružení').select().first().id
    clenove = db(db.clenstvi.group_id==clen_id).select(
          db.clenstvi.ALL, db.auth_user.nick,
          left=db.auth_user.on(db.auth_user.id==db.clenstvi.user_id),
          orderby=db.auth_user.nick.lower())
    return dict(clenove=clenove)

@auth.requires_login()
def zadosti():
    vyznam = {1:'převést zálohu sem',
              2:'vrátit zálohu na účet',
              3:'žádost o členství',
              4:'refundace'}
    zadosti = db(db.zadost.id>0).select(
          db.zadost.ALL, db.auth_user.nick,
          left=db.auth_user.on(db.auth_user.id==db.zadost.idauth_user),
          orderby=~db.zadost.zadost)
    return dict(zadosti=zadosti, vyznam=vyznam)

@auth.requires_membership('admin')
def nedavne():
    if len(request.args)>0:
        response.view = 'prehledy/vse.html'
    else:
        response.view = 'prehledy/pohyby.html'
    datum_od = datetime.now()-timedelta(days=60)
    datum_od = datum_od.combine(datum_od.date(), time(0,0))
    md = db.ucet.with_alias('md')
    dal = db.ucet.with_alias('dal')
    return dict(md=md, dal=dal,
        pohyby=db(db.pohyb.datum>=datum_od).select(
          db.pohyb.ALL,
          db.auth_user.nick,
          md.zkratka, dal.zkratka,
          left=(db.auth_user.on(db.auth_user.id==db.pohyb.idauth_user),
              md.on(md.id==db.pohyb.idma_dati),
              dal.on(dal.id==db.pohyb.iddal)),
          orderby=~db.pohyb.datum))

@auth.requires_membership('admin')
def zal_plus():
    response.view = 'prehledy/pohyby.html'
    md = db.ucet.with_alias('md')
    dal = db.ucet.with_alias('dal')
    return dict(md=md, dal=dal,
        pohyby=db(db.pohyb.iddal==Uc_sa.oz).select(
          db.pohyb.ALL,
          db.auth_user.nick,
          md.zkratka, dal.zkratka,
          left=(db.auth_user.on(db.auth_user.id==db.pohyb.idauth_user),
              md.on(md.id==db.pohyb.idma_dati),
              dal.on(dal.id==db.pohyb.iddal)),
          orderby=~db.pohyb.datum))

@auth.requires_membership('admin')
def fungujeme():
    response.view = 'prehledy/pohyby.html'
    md = db.ucet.with_alias('md')
    dal = db.ucet.with_alias('dal')
    return dict(md=md, dal=dal,
        pohyby=db(db.pohyb.iddal==Uc_sa.oz_fu).select(
          db.pohyb.ALL,
          db.auth_user.nick,
          md.zkratka, dal.zkratka,
          left=(db.auth_user.on(db.auth_user.id==db.pohyb.idauth_user),
              md.on(md.id==db.pohyb.idma_dati),
              dal.on(dal.id==db.pohyb.iddal)),
          orderby=~db.pohyb.datum))

@auth.requires_membership('admin')
def bu():
    response.view = 'prehledy/pohyby.html'
    md = db.ucet.with_alias('md')
    dal = db.ucet.with_alias('dal')
    return dict(md=md, dal=dal,
        pohyby=db((db.pohyb.iddal==Uc_sa.bezny)|
              (db.pohyb.idma_dati==Uc_sa.bezny)).select(
          db.pohyb.ALL,
          db.auth_user.nick,
          md.zkratka, dal.zkratka,
          left=(db.auth_user.on(db.auth_user.id==db.pohyb.idauth_user),
              md.on(md.id==db.pohyb.idma_dati),
              dal.on(dal.id==db.pohyb.iddal)),
          orderby=~db.pohyb.datum))

@auth.requires_membership('pokladna')
def vyridit():
    if len(request.args)>=2:
        if request.args(0)=='1': # převést sem zálohu sa.cz
            redirect(URL('zalohu_sem', args=request.args(1)))
        elif request.args(0)=='2': # vrátit zálohu
            redirect(URL('zalohu_vratit', args=request.args(1)))
        elif request.args(0)=='3': # přijmout za člena
            redirect(URL('prijmout_clena', args=request.args(1)))
    redirect(URL('zadosti'))

@auth.requires_membership('pokladna')
def prijmout_clena():     # asi by to chtělo rodné číslo...?
    if len(request.args)>=1:
        zadost = db.zadost[request.args(0)]
        user_id = zadost.idauth_user
        clenstvi = db(db.clenstvi.user_id==user_id).select()
        for clenstvi1 in clenstvi:
            if not clenstvi1.do_dne:
                session.flash = "přerušeno - má zahájené členství -> smazat žádost"
                redirect(URL('zadosti'))
        clen_id = db(db.auth_group.role=='člen sdružení').select().first().id 
        auth.add_membership(clen_id, user_id)
        db.clenstvi.insert(user_id=user_id, group_id=clen_id,
                        ode_dne=date.today())
        redirect(URL('vyrizeno', args=request.args(0)))
    redirect(URL('zadosti'))

@auth.requires_membership('pokladna')
def zalohu_vratit():
    if len(request.args)>=1:
        form = SQLFORM.factory(
                Field('cislo_uctu', length=30, label='Číslo účtu',
                        requires=IS_NOT_EMPTY()),
                Field('kod_banky', length=10, label='Kód banky',
                        requires=IS_NOT_EMPTY()),
                Field('zaloha', 'decimal(11,2)',
                        label="Zálohu snížit o (vč.poplatku)"),
                Field('strhnout', 'decimal(11,2)', label="Z toho poplatek")
                )
        zadost = db.zadost[request.args(0)]
        zakaznik = db.auth_user[zadost.idauth_user]
        zaloha = zakaznik.zaloha 
        form.vars.zaloha = zaloha
        form.vars.strhnout = min(30., form.vars.zaloha)
        form.vars.cislo_uctu = zadost.cislo_uctu
        form.vars.kod_banky = zadost.kod_banky
        if form.process().accepted:
            zaloha = form.vars.zaloha  # tj. kolik ze zálohy vzít vč. poplatku
            if zaloha<zakaznik.zaloha:
                session.flash = "přerušeno - zákazník nemá tolik na záloze"
                redirect(URL('zadosti'))
            if zaloha<form.vars.strhnout:
                session.flash = "přerušeno - stržená částka nestačí na poplatek"
                redirect(URL('zadosti'))
            cas = datetime.now()
            if form.vars.strhnout:     # if poplatek
                db.pohyb.insert(idauth_user=zadost.idauth_user,
                      idma_dati=Uc_sa.oz, iddal=Uc_sa.vynos_jiny,
                      datum=cas, castka=form.vars.strhnout,
                      popis="Poplatek Vrácení zálohy %s"%zakaznik.nick,
                      zakaznik=zadost.vs, vs=zadost.vs,
                      id_pokynu='vr zal p')
            prevedeno = zaloha-form.vars.strhnout
            if prevedeno>0:
                db.pohyb.insert(idauth_user=zadost.idauth_user,
                      idma_dati=Uc_sa.oz, iddal=Uc_sa.vraceno,
                      datum=cas, castka=prevedeno,
                      popis="Vrácení zálohy %s"%zakaznik.nick,
                      zakaznik=zadost.vs, vs=zadost.vs, ss=zadost.vs, ks='0308',
                      cislo_uctu=zadost.cislo_uctu, kod_banky=zadost.kod_banky,
                      id_pokynu='vr zal bu')
            zakaznik.update_record(zaloha=zakaznik.zaloha-zaloha)
            zadost.update_record(zadano=zaloha, prevedeno=prevedeno)
            mail_subj = Uc_sa.mail_subj
            podpis = Uc_sa.podpis
            mail.send(zakaznik.email,
                  mail_subj % TFu('Vrácení osobní zálohy'),
                  ('Ze zálohy Kč %1.2f\n'
                  'po stržení poplatku Kč %1.2f\n'
                  'jsme poslali Kč %1.2f\n'
                  'na účet %s/%s.\n\n'
                  'V případě nejasnosti kontaktuj pokladníka.\n'
                  'Díky za účast na našich akcích a rádi Tě uvidíme později.'
                  %(zaloha, form.vars.strhnout, zaloha-form.vars.strhnout,
                        zadost.cislo_uctu, zadost.kod_banky))
                  + (podpis%zakaznik.email))
            redirect(URL('vyrizeno', args=request.args(0)))
        response.view = 'prehledy/zalohu.html'
        return dict(form=form)              
    redirect(URL('zadosti'))

@auth.requires_membership('pokladna')
def zalohu_sem():
    if len(request.args)>=1:
        form = SQLFORM.factory(
                Field('castka', 'decimal(11,2)', label="Kolik Kč přebíráme?")
                )
        if form.process().accepted:
            zadost = db.zadost[request.args(0)]
            povel = (zadost.vs, form.vars.castka)
            __init(povel[0], povel[1])
            zadost.update_record(zadano=form.vars.castka,
                                prevedeno=form.vars.castka)
            redirect(URL('vyrizeno', args=request.args(0)))
        response.view = 'prehledy/zalohu.html'
        return dict(form=form)              
    redirect(URL('zadosti'))

# duplicitně převzato z fixdata.py
def __init(vs, castka):
    zakaznik = db(db.auth_user.vs==vs).select().first()
    if zakaznik:
        db.pohyb.insert(
              idauth_user=zakaznik.id,
              castka=castka,
              idma_dati=Uc_sa.oz_sa,
              iddal=Uc_sa.oz,
              datum=datetime.now(),
              popis="převod ze spolecneaktivity.cz",
              zakaznik=vs,
              vs=vs,
              ss=vs,
              id_pokynu='z sa.cz'
              )
        zakaznik.update_record(zaloha=zakaznik.zaloha + castka)
        mail_subj = Uc_sa.mail_subj
        podpis = Uc_sa.podpis
        mail.send(zakaznik.email,
            mail_subj % TFu('Připsána záloha ze spolecneaktivity.cz'),
              ('Byla vynulována Tvoje osobní záloha %s Kč na webu Jiřího Poučka spolecenaktivity.cz.\n'
              'O tuto částku byla navýšena Tvoje osobní záloha v účetním systému sdružení,\n'
              'takže bude možné platit i pro spolecneaktivity.cz i pro fungujeme.aspone.cz.\n\n'
              'Další podrobnosti zjištíš přihlášením se do účetního systému sdružení (přihlašovací údaje jsou uvedeny níže).\n'
              'V případě nejasností kontaktuj pokladníka.' % castka)
              + (podpis%zakaznik.email))

@auth.requires_membership('pokladna')
def vyrizeno():
    if len(request.args)>=1:
        db.zadost[request.args[0]] = dict(prevod=datetime.now(),
                              vyridil_id=auth.user_id)
        if len(request.args)>=3:
            db.zadost[request.args[0]] = dict(zadano=request.args[1],
                                          prevedeno=request.args[2])
    redirect(URL('zadosti'))
