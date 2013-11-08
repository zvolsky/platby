# coding: utf8

from datetime import datetime, timedelta, time
from mz_wkasa_platby import Uc_sa

def clenove():
    return {}

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
