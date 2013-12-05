# coding: utf8

from mz_wkasa_platby import Uc_sa, zpatky, aliases

@auth.requires_membership('admin')
def nedavne():
    if len(request.args)>0:
        response.view = 'podvojne/vse.html'
    else:
        response.view = 'podvojne/pohyby.html'
    md, dal, org = aliases(db) 
    return dict(
        pohyby=db(db.pohyb.datum>=zpatky(60)).select(
          db.pohyb.ALL,
          db.auth_user.nick,
          org.nick,
          md.zkratka, dal.zkratka,
          left=(db.auth_user.on(db.auth_user.id==db.pohyb.idauth_user),
              org.on(org.id==db.pohyb.idorganizator),
              md.on(md.id==db.pohyb.idma_dati),
              dal.on(dal.id==db.pohyb.iddal)),
          orderby=~db.pohyb.datum))

@auth.requires_membership('admin')
def zal_plus():
    response.view = 'podvojne/pohyby.html'
    md, dal, org = aliases(db) 
    return dict(
        pohyby=db(db.pohyb.iddal==Uc_sa.oz).select(
          db.pohyb.ALL,
          db.auth_user.nick,
          org.nick,
          md.zkratka, dal.zkratka,
          left=(db.auth_user.on(db.auth_user.id==db.pohyb.idauth_user),
              org.on(org.id==db.pohyb.idorganizator),
              md.on(md.id==db.pohyb.idma_dati),
              dal.on(dal.id==db.pohyb.iddal)),
          orderby=~db.pohyb.datum))

@auth.requires_membership('admin')
def fungujeme():
    response.view = 'podvojne/pohyby.html'
    md, dal, org = aliases(db) 
    return dict(
        pohyby=db(db.pohyb.iddal==Uc_sa.oz_fu).select(
          db.pohyb.ALL,
          db.auth_user.nick,
          org.nick,
          md.zkratka, dal.zkratka,
          left=(db.auth_user.on(db.auth_user.id==db.pohyb.idauth_user),
              org.on(org.id==db.pohyb.idorganizator),
              md.on(md.id==db.pohyb.idma_dati),
              dal.on(dal.id==db.pohyb.iddal)),
          orderby=~db.pohyb.datum))

@auth.requires_membership('admin')
def bu():
    response.view = 'podvojne/pohyby.html'
    md, dal, org = aliases(db) 
    return dict(
        pohyby=db((db.pohyb.iddal==Uc_sa.bezny)|
              (db.pohyb.idma_dati==Uc_sa.bezny)).select(
          db.pohyb.ALL,
          db.auth_user.nick,
          org.nick,
          md.zkratka, dal.zkratka,
          left=(db.auth_user.on(db.auth_user.id==db.pohyb.idauth_user),
              org.on(org.id==db.pohyb.idorganizator),
              md.on(md.id==db.pohyb.idma_dati),
              dal.on(dal.id==db.pohyb.iddal)),
          orderby=~db.pohyb.datum))

@auth.requires_membership('admin')
def pokladna():
    response.view = 'podvojne/pohyby.html'
    md, dal, org = aliases(db) 
    return dict(
        pohyby=db((db.pohyb.iddal==Uc_sa.pokladna)|
              (db.pohyb.idma_dati==Uc_sa.pokladna)).select(
          db.pohyb.ALL,
          db.auth_user.nick,
          org.nick,
          md.zkratka, dal.zkratka,
          left=(db.auth_user.on(db.auth_user.id==db.pohyb.idauth_user),
              org.on(org.id==db.pohyb.idorganizator),
              md.on(md.id==db.pohyb.idma_dati),
              dal.on(dal.id==db.pohyb.iddal)),
          orderby=~db.pohyb.datum))

@auth.requires_membership('admin')
def chybi():
    response.flash = "chybějící podvojný účet je nutno doplnit před daňovým přiznáním"
    response.view = 'podvojne/pohyby.html'
    md, dal, org = aliases(db) 
    return dict(
        pohyby=db((db.pohyb.iddal==None)|
              (db.pohyb.idma_dati==None)).select(
          db.pohyb.ALL,
          db.auth_user.nick,
          org.nick,
          md.zkratka, dal.zkratka,
          left=(db.auth_user.on(db.auth_user.id==db.pohyb.idauth_user),
              org.on(org.id==db.pohyb.idorganizator),
              md.on(md.id==db.pohyb.idma_dati),
              dal.on(dal.id==db.pohyb.iddal)),
          orderby=~db.pohyb.datum))
