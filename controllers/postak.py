# -*- coding: utf-8 -*-

import os
import datetime
from mandrill_send import mandrill_send, __init_plan_maily, __parse_mailheader
import vfp

maildir, planovany, planovany2 = __init_plan_maily()

def zaslat():
    return {}

#@requires_login()
#def zaslat():
    form = __get_mailform()
    if form.process().accepted:
        session.planovany = __get_mailheader(form)
        session.planovany2 = form.vars.txt
    return dict(form=form)

@auth.requires_membership('admin')
def zakaznikum():
    planovano = os.path.isfile(planovany)
    form = __get_mailform()
    if planovano:
        stav = db(db.systab.kod=='postak').select()
        if stav and int(stav.first().hodnota)>0:
            session.flash = "Pošťák ještě neposlal maily všem, vyčkej nebo volej Mirek Zv. 732457966"
            #redirect(URL('default', 'index')) # dvojí redirekce nezobrazí flash
            redirect(URL('info', 'coajak'))    # ale toto mají všichni admini           
        form.vars.is_html, dummy, form.vars.subject = __parse_mailheader(
                                                      planovany)
        try:
            form.vars.txt = unicode(vfp.filetostr(planovany2), 'utf8')
        except:
            pass
    else:
        form.vars.subject = 'Společné Aktivity o.s. - informace rady'
        form.vars.txt = '\n\nZa Společné Aktivity o.s.' + form.table.txt.default                                  
    if form.process().accepted:
        vfp.strtoutf8file(__get_mailheader(form), planovany,
                                                      str_encoding='utf8')
        vfp.strtoutf8file(form.vars.txt, planovany2, str_encoding='utf8')
        planovano = True
        try:
            mandrill_send(form.vars.subject, form.vars.txt,
                    prijemci=[{'email': auth.user.email}],
                    styl='html' if form.vars.is_html else 'text')
            session.flash = TFu('Zkušební odeslán na %s')%auth.user.email
        except:
            session.flash = TFu(
                          'Mail naplánován, ale nezdařilo se poslat zkušební')
        redirect(URL())
    return dict(form=form, planovano=planovano)

@auth.requires_membership('admin')
def zrus_hromadny():
    vfp.remove(planovany)
    vfp.remove(planovany2)
    session.flash = TFu('Mail byl zrušen')
    redirect(URL('default', 'index'))

def __get_mailform(): 
    return SQLFORM.factory(
              Field('subject', label=TFu('Předmět'),
                    default=''),
              Field('is_html', 'boolean', default=False,
                    label=TFu('HTML mail?'),
                    comment=TFu('nepoužívej HTML mail, nemáš-li základní znalost HTML (snad zde časem bude inteligentnější prvek pro graficky zvýrazněný text)')),
              Field('txt', 'text',
                    default='\n%s %s'
                          %(auth.user.first_name, auth.user.last_name),
                    comment=TFu('zvětšit okno lze vpravo dole ---- pro HTML mail: <b>tučně</b> <i>šikmo</i> <h3>nadpis</h3> <p>odstavec</p> <ul><li>1.pol.seznamu</li><li>2.pol.seznamu</li></ul> <a href="http://adresa-odkazu">text-odkazu</a> odřádkovat navíc: <br />')),
              )

def __get_mailheader(form):
    return ('H' if form.vars.is_html else 'T') + 'Z' + (
                ' %s\n%s'%(datetime.datetime.now().strftime('%d.%m.%Y %H:%M'),
                form.vars.subject))
