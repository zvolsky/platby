# -*- coding: utf8 -*-

import os
import vfp
import mandrill

mandrill_key = vfp.filetostr(os.path.join(request.folder,
          'private', 'zvolsky_gmail_mandrill.smtp'))

subject = u"Informace o změnách v pořádání placených akcí a vedení pokladny"
txt = ''
html = (
u'''Vážená účastnice / vážený účastníku akcí našeho sdružení,
<br />
<ul><b>V tomto mailu se dozvíš:</b>
<li>K jakým změnám došlo v pořádání akcí,</li>
<li>K jakým změnám došlo ve vedení osobních záloh,</li>
<li>Jak se přihlásit do evidence osobních záloh,</li>
<li>Jak si zajistit správné placení pro spolecneaktivity.cz a fungujeme.aspone.cz,</li>
<li>Kdo Ti poradí při problémech,</li>
<li>Jak zabránit zasílání těchto mailů, pokud Tě nezajímají.</li>
</ul>

<h4>K jakým změnám došlo v pořádání akcí</h4>

Občanské sdružení Společné Aktivity o.s. začalo pořádat akce i mimo web <a href="http://www.spolecneaktivity.cz">spolecneaktivity.cz</a> (na webu <a href="http://fungujeme.aspone.cz">fungujeme.aspone.cz</a>).<br /><br />

Web spolecneaktivity.cz naopak jeho provozovatel a vlastník Jiří Pouček otevřel i pro jiné subjekty.<br /><br />

Zda na webu spolecneaktivity.cz budou nadále působit i jiné subjekty, např. naše sdružení, záleží na tom, zda tyto subjekty dostanou stejné, rovné a přijatelné podmínky.


<h4>K jakým změnám došlo ve vedení osobních záloh</h4>

Účetnictví našeho sdružení a evidence osobních záloh byly dosud vedeny na webu spolecneaktivity.cz Jiřího Poučka, a protože webová aplikace vůbec nevyhovovala podmínkám pro nás povinného podvojného účetnictví, byly dále zpracovávány v další evidenci.<br />
Abychom toto napravili a zároveň se přizpůsobili nové realitě - pořádání placených akcí na spolecneaktivity.cz i na fungujeme.aspone.cz - byla založena nová webová evidence osobních záloh zákazníků, předávání peněz mezi organizátory a pokladnou, a (do budoucna) vůbec všech pohybů našeho podvojného účetnictví.
<br /><br />
Podrobnosti o své osobní záloze do září 2013 najdeš na spolecneaktivity.cz.
Od října 2013 už tam bude jen útrata za akce na webu spolecneaktivity.cz.
<br /><br />
Úplnou evidenci Tvé osobní zálohy, přehled Tvých plateb na účet sdružení, stav osobní zálohy i výdaje pro spolecneaktivity.cz i Fungujeme najdeš na adrese:
<a href="https://platby.alwaysdata.net">platby.alwaysdata.net</a> 


<h4>Jak se přihlásit do evidence osobních záloh</h4>

<ol>
<li>jdi na adresu:
   <a href="https://platby.alwaysdata.net/default/user/request_reset_password">https://platby.alwaysdata.net/default/user/request_reset_password</a></li> 

<li>zadej e-mail, pod kterým jsi se zaregistroval na spolecneaktivity.cz
   a stiskni Nastavit nové heslo</li>
   
<li>v mailu, který Ti přijde, stiskni odkaz,
   a na stránce, na kterou se dostaneš, si zadej heslo</li>
</ol>

<h4>Jak si zajistit správné placení pro <a href="http://www.spolecneaktivity.cz">spolecneaktivity.cz</a> a <a href="http://fungujeme.aspone.cz">fungujeme.aspone.cz</a></h4>

Peníze, evidované v nové evidenci, slouží pro placení na oba servery.

Vše potřebné zjistíš zde:
<a href="https://platby.alwaysdata.net/info/coajak">https://platby.alwaysdata.net/info/coajak</a>

Ve volbách menu Zákazník najdeš informace o své osobní záloze a pohybech na ní.
Došlé platby se objevují cca 30 min po příchodu na náš účet do banky.<br />
Fungujeme inkasuje platby při přihlášení na akci, a pokud není v tu chvíli na záloze dost peněz, tak vždy během noci.<br />
Platby pro spolecneaktivity.cz se převádí manuálním úkonem vždy po několika dnech (jako dosud). 
<br /><br />
Ačkoli se nejedná o skutečné peníze, ale jen o způsob jejich evidence, nechceme nikomu přesunout zbývající zálohu z evidence na spolecneaktivity.cz bez jeho souhlasu.<br />
Pokud ji tam tedy máš, a chystáš se platit i pro fungujeme, v menu Zákazník najdeš možnost:<br />
"Žádám o převedení zbylé zálohy ze spolecneaktivity.cz do této evidence".
Nebo napiš mail na zvolsky@seznam.cz


<h4>Kdo Ti poradí při problémech</h4>

Volej 732457966 Mirek Zvolský (zvolsky@seznam.cz).


<h4>Jak zabránit zasílání těchto mailů, pokud Tě nezajímají</h4>

Ve svém profilu na platby.alwaysdata.cz najdeš dole předvolbu Neposílat,
kterou můžeš mailové informace zablokovat.<br />
Vzhledem k tomu, že se jedná o správu Tvých peněz a plateb, nedoporučujeme to.
''')

def sendall():
    celkem = 0
    for zakaznik in db(db.auth_user.neposilat==False).select():
        if 100<=int(zakaznik.vs)<150:
            send(subject, html or txt, prijemci=[{'email': zakaznik.email}],
                    styl='html' if html else 'text')
            celkem += 1
    print "odesláno mailů: %s"%celkem

def send(subject, txt, prijemci=
      [{'email': 'mirek.zvolsky@gmail.com', 'name': u'Mirek Zvolský na Googlu'},
      {'email': 'zvolsky@seznam.cz', 'name': u'Mirek Zvolský na Seznamu'}],
      styl='text'):
    '''
    subject, txt - nejlépe unicode objekty
    prijemci - viz příklad defaultní hodnoty
    styl = 'html'/'text'
    '''
      
    # https://mandrillapp.com/api/docs/messages.python.html#method=send
    m=mandrill.Mandrill(mandrill_key)
    msg = {
         'from_email': 'spolecneaktivityos@gmail.com',
         'from_name': u'Společné Aktivity o.s. (pokladna/provoz)',
         'subject': subject,
         styl: txt,
         'to': prijemci,
    }
        # 'attachments': [{'content': 'ZXhhbXBsZSBmaWxl',
        #                 'name': 'myfile.txt', 'type': 'text/plain'}]
    m.messages.send(message=msg)

if __name__=='__main__':
    sendall() 