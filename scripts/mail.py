# -*- coding: utf8 -*-

import os
import vfp
import mandrill

mandrill_key = vfp.filetostr(os.path.join(request.folder,
          'private', 'zvolsky_gmail_mandrill.smtp'))

subject = u"Informace o změnách v pořádání placených akcí a vedení pokladny"
txt = (
u'''Vážená účastnice / vážený účastníku akcí našeho sdružení,

V tomto mailu se dozvíš:
- K jakým změnám došlo v pořádání akcí,
- K jakým změnám došlo ve vedení osobních záloh,
- Jak se přihlásit do evidence osobních záloh,
- Jak si zajistit správné placení pro spolecneaktivity.cz a fungujeme.aspone.cz,
- Kdo Ti poradí při problémech,
- Jak zabránit zasílání těchto mailů, pokud Tě nezajímají.

--- K jakým změnám došlo v pořádání akcí ---

Občanské sdružení Společné Aktivity o.s. začalo pořádat akce i mimo web spolecneaktivity.cz (na webu fungujeme.aspone.cz).

Web spolecneaktivity.cz profiloval Jiří Pouček v uplynulé době zcela jasně jako svůj soukromý podnikatelský záměr. Zpřístupnil jej více subjektům, přičemž jedním z nich (a možná do budoucna jediným) je nové občanské sdružení Organizátoři akcí o.s., které právě zakládá, a které bude zřejmě založeno na stejných principech jako naše sdružení před cca 2 lety: bude založeno na Jirkově práci pro vlastní živnostenské podnikání, na diktování pravidel Jirkou, a na dobrovolnické práci mnohých dalších.

Zda na webu spolecneaktivity.cz budou nadále působit i jiné subjekty, např. naše sdružení, záleží na tom, zda tyto subjekty dostanou stejné, rovné a přijatelné podmínky.


--- K jakým změnám došlo ve vedení osobních záloh ---

Účetnictví našeho sdružení a evidence osobních záloh byly dosud vedeny na webu spolecneaktivity.cz Jiřího Poučka, a protože webová aplikace vůbec nevyhovovala podmínkám pro nás povinného podvojného účetnictví, byly dále zpracovávány v další evidenci.
Abychom toto napravili a zároveň se přizpůsobili nové realitě - pořádání placených akcí na spolecneaktivity.cz i na fungujeme.aspone.cz - byla založena nová webová evidence osobních záloh zákazníků, předávání peněz mezi organizátory a pokladnou, a (do budoucna) vůbec všech pohybů našeho podvojného účetnictví.

Najdete ji na adrese:
platby.alwaysdata.net 


--- Jak se přihlásit do evidence osobních záloh ---

1) jdi na adresu:
   https://platby.alwaysdata.net/default/user/request_reset_password 

2) zadej e-mail, pod kterým jsi se zaregistroval na spolecneaktivity.cz
   a stiskni Nastavit nové heslo
   
3) v mailu, který Ti přijde, stiskni odkaz,
   a na stránce, na kterou se dostaneš, si zadej heslo


--- Jak si zajistit správné placení pro spolecneaktivity.cz a fungujeme.aspone.cz ---

chceš-li platit i pro akce na fungujeme.aspone.cz:
v profilu pod volbou Vítejte/Profil nebo na adrese
   https://platby.alwaysdata.net/default/user/profile
si změň **nick** a **e-mail** podle registrace na fungujeme.aspone.cz

Placení pro spolecneaktivity.cz je nadále funkční pod dosavadním osobním číslem. (pro spolecneaktivity.cz to byl specifický symbol, nyní jej raději uváděj do obvyklejšího, variabilního symbolu platby - ale rozpoznáme jej v obou případech)

Číslo účtu sdružení je dole na stránkách platby.alwaysdata.net
a je uvedeno u každé placené akce na obou serverech.

Ačkoli se nejedná o skutečné peníze, ale jen o způsob jejich evidence, nechceme nikomu přesunout zbývající zálohu z evidence na spolecneaktivity.cz bez jeho souhlasu.
Pokud jí tam tedy máš, a chystáš se platit i pro fungujeme, na platby.alwaysdata.cz najdeš tlačítko:
"Žádám o převedení zbylé zálohy ze spolecneaktivity.cz do této evidence".
Nebo napiš mail na zvolsky@seznam.cz

Peníze, evidované v nové evidenci, slouží pro placení na oba servery.

Ve volbách Přehled a Pohyby na záloze najdeš informace o své osobní záloze a pohybech na ní.
Došlé platby se objevují cca 30 min po příchodu na náš účet do banky.
Fungujeme inkasuje platby při přihlášení na akci, a pokud není v tu chvíli na záloze dost peněz, tak vždy během noci.
Platby pro spolecneaktivity.cz se převádí manuálním úkonem vždy po několika dnech (jako dosud). 


--- Kdo Ti poradí při problémech ---

Volej 732457966 Mirek Zvolský (zvolsky@seznam.cz).


--- Jak zabránit zasílání těchto mailů, pokud Tě nezajímají ---

Ve svém profilu na platby.alwaysdata.cz najdeš dole předvolbu Neposílat,
kterou můžeš mailové informace zablokovat.
Vzhledem k tomu, že se jedná o správu Tvých peněz a plateb, nedoporučujeme to.
''')

def sendall():
    celkem = 0
    for zakaznik in db(db.auth_user.neposilat==False).select():
        if 500<=int(zakaznik.vs)<550:
            send(subject, txt, prijemci=[{'email': zakaznik.email}])
            celkem += 1
    print "odesláno mailů: %s"%celkem

def send(subject, txt, prijemci=
      [{'email': 'mirek.zvolsky@gmail.com', 'name': u'Mirek Zvolský na Googlu'},
      {'email': 'zvolsky@seznam.cz', 'name': u'Mirek Zvolský na Seznamu'}]):
    '''
    subject, txt - nejlépe unicode objekty
    prijemci - viz příklad defaultní hodnoty
    '''
      
    # https://mandrillapp.com/api/docs/messages.python.html#method=send
    m=mandrill.Mandrill(mandrill_key)
    msg = {
         'from_email': 'spolecneaktivityos@gmail.com',
         'from_name': u'Společné Aktivity o.s. (pokladna/provoz)',
         'subject': subject,
         'text': txt,
         'to': prijemci,
    }
        # 'attachments': [{'content': 'ZXhhbXBsZSBmaWxl',
        #                 'name': 'myfile.txt', 'type': 'text/plain'}]
    m.messages.send(message=msg)

if __name__=='__main__':
    sendall() 