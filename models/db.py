# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

import os
import datetime
import vfp

def TFu(txt):
    return txt # překlad zatím ne, a nezapisovat do překladové tabulky

class SOUHLAS_S_VS(object):
    '''validátor pro auth_user.ss
    '''
    def __init__(self, vs):
        self.vs = vs
    def __call__(self, value):
        value = value.strip().lstrip('0')
        if not value:
            return ('', None)
        try:
            intss = int(value)
        except:
            intss = None
        if not intss:
            return (value, 'Je třeba zadat pouze číslo.')
        try:
            intvs = int(self.vs)
        except:
            intvs = 0
        if 101<=intvs<=674:  # registrovaní při převodu
            if self.vs!=value:
                return ('', 'Lze zadat jen %s nebo ponechat prázdné' % intvs)
        else:                # registrovaní později
            if intss<675:
                return ('', 'Zadané číslo uživatele není přípustné')
        return (value, None)    

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
#request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL('sqlite://platby.sqlite',pool_size=1,check_reserved=['all'])
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db)
crud, service, plugins = Crud(db), Service(), PluginManager()

## create all tables needed by auth if not custom tables
vs_default = TFu('dostaneš..') # max 10 znaků
auth.settings.extra_fields['auth_user'] = [
    Field('nick', length=100, default='',
          comment=TFu('přezdívka na častěji používaném serveru; tuto přezdívku uváděj tomu, komu platíš v hotovosti (pro správné zpracování platby)')),
    Field('organizator', 'boolean', default=False,
          label=TFu('Organizátor placených akcí'),
          comment=TFu('zaškrtni, pokud budeš platit/vybírat peníze jménem Sdružení a předávat si peníze a doklady s pokladníkem')),
    Field('vs', length=10, writable=False, default=vs_default,
          label=TFu('Osobní symbol (VS)'),
          comment=TFu('tento variabilní symbol (osobní symbol) používej pro platby; preferujeme variabilní symbol, ale s ohledem na spolecneaktivity.cz bude číslo rozpoznáno i ve specifickém symbolu')),
    Field('ss', length=10, default='',
          label=TFu('Symbol pro spolecneaktivity.cz (SS)'),
          comment=TFu('uveď, chceš-li hradit akce pro tento specifický symbol na spolecneaktivity.cz; pozor: nesprávné zadání způsobí úhradu někomu jinému')),
    Field('zaloha', 'decimal(11,2)', writable=False, default=0),
    Field('ode_dne', 'date', readable=False, writable=False,
        default=datetime.date.today(), label=TFu('Ode dne'),
        comment=TFu('jako zákazník Sdružení jsem registrován(a) ode dne')),
    Field('prihlasen', 'date', readable=False, writable=False),
    Field('vyzva', 'date', readable=False, writable=False),
    ]
auth.define_tables(username=False, signature=False)
db.auth_user.ss.requires=[
      SOUHLAS_S_VS(auth.user and auth.user.vs or ''),
      IS_EMPTY_OR(IS_NOT_IN_DB(db, db.auth_user.ss)),
      ]
db.auth_user._format = '%(nick)s - %(vs)s'
db.auth_user.email.comment = TFu('mail z registrace na fungujeme nebo jiný funkční mail (při prvním přihlášení zákazníka se spec.sym. 101-674 je zde mail z registrace na spolecneaktivity.cz)')
name_comment = TFu('údaj nepředáme třetí straně - pomáhá nám identifikovat platby')
db.auth_user.first_name.comment = name_comment
db.auth_user.last_name.comment = name_comment

## configure email
mail = auth.settings.mailer
mail.settings.server = 'smtp.gmail.com:587'  # 'logging' or ...
mail.settings.sender = 'spolecneaktivityos@gmail.com'
mail.settings.login = 'spolecneaktivityos@gmail.com:'+vfp.filetostr(
        os.path.join(os.getcwd(),
        'applications', 'platby', 'private', 'saos_gmail.smtp'))
#mail.settings.server = 'smtp.mandrillapp.com:587'
#mail.settings.sender = 'mirek@zvolsky@gmail.com'
#mail.settings.login = 'mirek@zvolsky@gmail.com:'+vfp.filetostr(
#        os.path.join(os.getcwd(),
#        'applications', 'platby', 'private', 'zvolsky_gmail_mandrill.smtp'))

## configure auth policy
auth.settings.registration_requires_verification = True
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = False

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
#from gluon.contrib.login_methods.rpx_account import use_janrain
#use_janrain(auth, filename='private/janrain.key')
