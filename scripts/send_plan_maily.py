# -*- coding: utf8 -*-

'''
zasílá maily pomocí mandrill velkému počtu příjemců, ale v krátkých dávkách
při existenci souboru k odeslání nejprve nastaví db.systab['postak']= >>max
hodnota db.systab['postak'] znamená poslední odeslané db.auth_user.id,
    přičemž jdeme descending
s každým voláním send_plan_maily()
    vyhledáme tedy vždy id<db.systab['postak'], orderby=~id
    a odešleme jich prvních ncount
jakmile je jich vyhledáno <ncount, znamená to, že (po jejich odeslání) jsme
    u konce - přejmenujeme soubory, čímž se zabrání opakovanému/dalšímu posílání
    
crontab např. (200/hod. if ncount=25):
5,10,15,25,30,35,45,50,55 5-8 * * * python web2py.py -M -S platby -R applications/platby/scripts/send_plan_maily.py 
'''

import os
import datetime
from mandrill_send import mandrill_send, __init_plan_maily, __parse_mailheader
import vfp

maildir, planovany, planovany2 = __init_plan_maily()

def send_plan_maily():
    '''odesílá maily v drobných dávkách'''
    if not os.path.isfile(planovany) or not os.path.isfile(planovany2):
        return ''
    pozice_rec = db(db.systab.kod=='postak').select()
    if pozice_rec:
        pozice = int(pozice_rec.first().hodnota)
    else:
        pozice = 0
    if not pozice:    # začni rozesílat
        pozice = 999999999   # >>max 
    is_html, dummy, subject = __parse_mailheader(planovany)
    obsah = unicode(vfp.filetostr(planovany2), 'utf8')
    ncount = 25  # aby nás alwaysdata netípla kvůli moc dlouhému jobu
    zakaznici = db((db.auth_user.neposilat==False) &
            (db.auth_user.id<pozice)).select(
            db.auth_user.id, db.auth_user.email,
            orderby=~db.auth_user.id, limitby=(0,ncount))
    vfp.strtofile(str(id)+'\n')
    #debug:
    #zakaznici = db(db.auth_user.vs=='347').select()
    for zakaznik in zakaznici:
        vfp.strtofile(str(zakaznik.id)+'\n','xxxx.log',1)
        mandrill_send(subject, obsah, prijemci=[{'email': zakaznik.email}],
                styl='html' if is_html else 'text')
        pozice = db.auth_user.id 
        db.systab.update_or_insert(kod='postak', hodnota=str(pozice))
        db.commit()
    if len(zakaznici)<ncount:   # další už nejsou
        new_filestem = 'mail_' + datetime.datetime.now().strftime('%Y%m%d_%H%M') 
        vfp.rename(planovany, new_filestem + '.hlavicka')
        vfp.rename(planovany2, new_filestem + '.obsah')
        # db update až po přejmenování = jistota proti opakovanému rozeslání
        db.systab.update_or_insert(kod='postak', hodnota='0')
        db.commit()

if __name__=='__main__':
    send_plan_maily()