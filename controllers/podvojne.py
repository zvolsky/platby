# coding: utf8

from mz_wkasa_platby import Uc_sa, zpatky, aliases

@auth.requires_membership('admin')
def vse():
    response.view = 'podvojne/pohyby.html'
    cnt_args = len(request.args)
    if cnt_args<2:
        query = None
    else:
        if request.args[0]=='0':
            md = db.pohyb.idma_dati==None
        else:
            md = db.pohyb.idma_dati==request.args[0]
        if request.args[1]=='0':
            dal = db.pohyb.iddal==None
        else:
            dal = db.pohyb.iddal==request.args[1]
        query = ((md)&(dal))
        if cnt_args>=4:
            od = request.args[2]
            pred = request.args[3]
            query &= ((db.pohyb.datum>=datetime.date(
                        int(od[:4]), int(od[4:6]), int(od[6:])))&
                    (db.pohyb.datum<datetime.date(
                        int(pred[:4]), int(pred[4:6]), int(pred[6:]))))
    return _podvojne(query)

@auth.requires_membership('admin')
def nedavne():
    if len(request.args)>0:
        response.view = 'podvojne/vse.html'
    else:
        response.view = 'podvojne/pohyby.html'
    return _podvojne(db.pohyb.datum>=zpatky(60))

@auth.requires_membership('admin')
def zal_plus():
    response.view = 'podvojne/pohyby.html'
    return _podvojne(db.pohyb.iddal==Uc_sa.oz)

@auth.requires_membership('admin')
def fungujeme():
    response.view = 'podvojne/pohyby.html'
    return _podvojne(db.pohyb.iddal==Uc_sa.oz_fu)

@auth.requires_membership('admin')
def bu():
    response.view = 'podvojne/pohyby.html'
    return _podvojne((db.pohyb.iddal==Uc_sa.bezny)|
              (db.pohyb.idma_dati==Uc_sa.bezny))

@auth.requires_membership('admin')
def pokladna():
    response.view = 'podvojne/pohyby.html'
    return _podvojne((db.pohyb.iddal==Uc_sa.pokladna)|
              (db.pohyb.idma_dati==Uc_sa.pokladna))

@auth.requires_membership('admin')
def chybi():
    response.flash = "chybějící podvojný účet je nutno doplnit před daňovým přiznáním"
    response.view = 'podvojne/pohyby.html'
    return _podvojne((db.pohyb.iddal==None)|
              (db.pohyb.idma_dati==None))

@auth.requires_membership('admin')
def ucet():
    if len(request.args)==1:
        ucet = db.ucet[request.args[0]]
        if ucet:
            response.view = 'podvojne/pohyby.html'
            return _podvojne((db.pohyb.idma_dati==request.args[0])|
                (db.pohyb.iddal==request.args[0]), '%s : %s (%s)' % (ucet.ucet, ucet.nazev, ucet.zkratka))
    session.flash = "nesprávně zadaný účet (id)"
    redirect(URL('default', 'index'))


def _podvojne(query, hdr=None):
    md, dal, org = aliases(db) 
    return dict(hdr=hdr,
        pohyby=db(query).select(
          db.pohyb.ALL,
          db.auth_user.nick,
          org.nick,
          md.zkratka, dal.zkratka,
          left=(db.auth_user.on(db.auth_user.id==db.pohyb.idauth_user),
              org.on(org.id==db.pohyb.idorganizator),
              md.on(md.id==db.pohyb.idma_dati),
              dal.on(dal.id==db.pohyb.iddal)),
          orderby=~db.pohyb.datum))
