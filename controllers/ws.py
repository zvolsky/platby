# -*- encoding: utf8 -*-

import os
from datetime import datetime, date, timedelta
from hashlib import md5
import vfp

first_token = vfp.filetostr(os.path.join(os.getcwd(),
                  'applications', 'platby', 'private', 'fungujeme.token'))

mail_subj = Uc_sa.mail_subj
podpis = Uc_sa.podpis

def udaje():
    if len(request.args)==2:
        token = request.args[0]
        dotaz = request.args[1]
        regist_token = first_token
        if token==md5(regist_token+dotaz).hexdigest():
            if '@' in dotaz:
                uzivatel = db(db.auth_user.email==dotaz).select().first()
            else:
                uzivatel = db(db.auth_user.vs==dotaz).select().first()
            if uzivatel:
                retval = dict(vs=uzivatel.vs or '',
                              email=uzivatel.email or '',
                              zaloha=str(uzivatel.zaloha or 0))
            else:
                retval = dict(vs='', email='', zaloha='0')
            return retval
    raise HTTP(403)

def chce():
    '''ws/pohyb/<args>, args:
    token = hash(token+vs+castka)
    vs
    castka>0: připsat
    email
    symbol akce
    popis
    vrací se: provedeno False/True,
              castka if True =zustatek, if False and castka<0 =chybí
    '''

    is_valid, castka, popis, uzivatel, akce = __valid_params(request.args, db)
    if is_valid and castka>0:
        db.zadost.insert(zadost=datetime.now(),
                      idauth_user=uzivatel.id,
                      typ=3,
                      zadano=castka,
                      popis=popis,
                      ss=akce)
        mail.send(uzivatel.email, mail_subj % TFu('Přijata žádost o refundaci'),
            ('Přijali jsme Tvoji žádost o refundaci %s Kč.\n'
            'O vrácení peněz bude rozhodnuto po akci, '
                'zejména s ohledem na její finanční výsledek.'%castka)
            + ('\n\nPopis: %s'%popis) + (podpis%uzivatel.email))
        return dict(provedeno=True)
    raise HTTP(403)

def pohyb():
    '''ws/pohyb/<args>, args:
    token = hash(token+vs+castka)
    vs
    castka>0: připsat, castka<0 strhnout
    email
    symbol akce
    popis
    vrací se: provedeno False/True,
              castka if True =zustatek, if False and castka<0 =chybí
    '''

    is_valid, castka, popis, uzivatel, akce = __valid_params(request.args, db)
    if is_valid:
        zustane = castka+float(uzivatel['zaloha'])
        if zustane<0:
            retval = dict(provedeno=False, castka=zustane)
            if not uzivatel.vyzva or (
                            date.today()-timedelta(1)>uzivatel.vyzva):
                            # jednou za 2 dny
                uzivatel.update_record(vyzva=date.today())
                mail.send(uzivatel.email,
                      mail_subj % TFu('Málo peněz na zaplacení'),
                      ('K zaplacení částky %s Kč Ti chybělo %s Kč.\n'
                        'Prosím, pošli proto peníze na účet sdružení nebo se '
                            'odhlaš z akce.'%(-castka, -zustane))
                        + ('\n\nPopis: %s'%popis)
                        + '\n\nPoznámka: Jsi-li přihlášen(a) i na další, zatím '
                          'neuhrazené akce, může být potřeba větší částka.'
                        + (podpis%uzivatel.email))
        else:
            if castka>0:  # vracíme na os.zálohu
                idmd = Uc_sa.oz_fu
                iddal = Uc_sa.oz
            else:         # vybíráme za akci
                idmd = Uc_sa.oz
                iddal = Uc_sa.oz_fu
            uzivatel.update_record(zaloha=zustane)
            db.pohyb.insert(
                    idauth_user=uzivatel.id,
                    zakaznik=uzivatel.vs,
                    datum=datetime.now(),
                    castka=abs(castka),
                    popis=popis,
                    idma_dati=idmd,
                    iddal=iddal,
                    ss=akce,
                    )
            retval = dict(provedeno=True, castka=zustane)
            mail.send(uzivatel.email,
                mail_subj % 
                    (TFu('Zaplacena účast na akci') if castka<0
                    else TFu('Vráceny peníze na osobní zálohu')),
                ('Osobní záloha Ti byla '
                +('snížena o %s' if castka<0 else 'zvýšena o %s')%abs(castka)+
                ' Kč na úhradu akce.\n'
                'Nyní Ti zbývá na osobní záloze %s Kč.'%zustane)
                  + ('\n\nPopis: %s'%popis)
                  + (podpis%uzivatel.email))
        return retval
    raise HTTP(403)

def __valid_params(args, db):
    is_valid = False
    castka = 0
    popis = ''
    uzivatel = None
    akce = ''
    if len(args)==6:
        token = args[0]
        vs = args[1]
        scastka = args[2]
        if vs and scastka:
            regist_token = first_token
            if token==md5(regist_token+vs+scastka).hexdigest():
                try:
                    castka = round(float(scastka), 2)
                except ValueError:
                    castka = 0
                popis = args[5]
                uzivatel = db(db.auth_user.vs==vs).select().first()
                if (castka and popis and uzivatel
                                    and uzivatel.email==args[3]):
                    akce = args[4] or ''
                    is_valid = True
    return is_valid, castka, popis, uzivatel, akce
