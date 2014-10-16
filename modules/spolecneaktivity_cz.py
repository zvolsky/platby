#!/usr/bin/env python
# -*- coding: utf8 -*-

u'''
automatizace webu spolecneaktivity.cz
'''

from mechanize import Browser

def sa_login(sa_userName, sa_password):
    '''Login to spolecneaktivity.cz portal as sa_userName user.

    Temporary(?) no check
        - if online,
        - if not logged as other user
        - succesfully logged in
    '''
    url_login = 'http://www.spolecneaktivity.cz'

    br = Browser()
    br.set_handle_robots(False)
    
    ok = False
    try:
        r = br.open(url_login)
        rru = r.read().upper()
        if "LOGIN" in rru and "HESLO" in rru:   # not logged in yet
            br.select_form(nr=0)
            br["userName"] = sa_userName
            br["password"] = sa_password
            r = br.submit()
            ok = True
    except:
        pass
    if not ok:
        print u"sa_parse.sa_login: Selhalo přihlášení do spolecneaktivity.cz"
    return br

def unformat_castka(castka):
    '''z částky, rozparsované z tabulky, odstraní formátovací nesmysly,
    např. 2\xa0500,00 Kč -> 2500.0
    '''            
    return float(castka.strip().replace(u'\xa0','').replace(',','.').split()[0])
