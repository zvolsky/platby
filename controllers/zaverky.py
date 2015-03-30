# coding: utf8

import datetime

@auth.requires_membership('admin')
def obdobi():
    volba_obdobi = '<table>'
    for rok in xrange(datetime.date.today().year, 2010, -1):
        volba_obdobi += '<tr><td><a href="%s"><b>%s</b></a></td>' % (
                    URL('zaverka', args=(rok, 1, 12)),
                    rok)
        for mesic in range(1, 13, 3):
            volba_obdobi += '<td><a href="%s"><small> %s-%s</small></a></td>' % (
                    URL('zaverka', args=(rok, mesic, mesic+2)),
                    mesic, mesic+2)
        volba_obdobi += '</tr>'
    volba_obdobi += '</table>'
    return dict(volba_obdobi=volba_obdobi)

@auth.requires_membership('admin')
def zaverka():
    if len(request.args)<3:
        session.flash = TFu("nesprávné parametry volání")
        redirect(URL('obdobi'))
    rok = int(request.args[0])
    mesic_od = int(request.args[1])
    den_od = datetime.date(rok, mesic_od, 1)
    mesic_do = int(request.args[2])
    den_po = datetime.date(rok+1, 1, 1) if mesic_do>=12 else datetime.date(rok, mesic_do+1, 1)

    # součtování podle druhů pohybu
    md = db.ucet.with_alias('md')
    dal = db.ucet.with_alias('dal')
    pocet = db.pohyb.id.count()
    suma = db.pohyb.castka.sum()
    skupiny = db((db.pohyb.datum>=den_od) & (db.pohyb.datum<den_po)
            ).select(db.pohyb.idma_dati, db.pohyb.iddal,
            md.ucet, dal.ucet, db.kategorie.vyznam, pocet, suma,
            left=[md.on(md.id==db.pohyb.idma_dati),
                dal.on(dal.id==db.pohyb.iddal),
                db.kategorie.on((db.kategorie.idma_dati==db.pohyb.idma_dati) & (db.kategorie.iddal==db.pohyb.iddal))],
            groupby=[db.pohyb.idma_dati, db.pohyb.iddal])

    ucty_dict = osnova()

    need_commit = False
    ucty = {}
    protistrana = {}
    for skupina in skupiny:
        # aktualizovat 'kategorie' (druhy pohybů) o dosud nezaznamenané druhy pohybů
        if skupina.kategorie.vyznam==None:
            if skupina.pohyb.idma_dati==None or skupina.pohyb.iddal==None:
                # mám problém, že se nepřipojily záznamy None/platný, platný/None, a dokud to neumím udělat lépe,
                # musím znova zkontrolovat, že v kategoriích nejsou, aby se tam nemnožily
                kategorie = db((db.kategorie.idma_dati==skupina.pohyb.idma_dati) & (db.kategorie.iddal==skupina.pohyb.iddal)
                            ).select(db.kategorie.vyznam)
                if len(kategorie):
                    skupina.kategorie.vyznam = kategorie.first().vyznam
                    continue
            db.kategorie.insert(idma_dati=skupina.pohyb.idma_dati, iddal=skupina.pohyb.iddal)
            need_commit = True

        # podle účtů
        ucty[skupina.md.ucet] = ucty.get(skupina.md.ucet, 0) + skupina[suma]
        if protistrana.get(skupina.md.ucet) is None:
            protistrana[skupina.md.ucet] = {}
        protistrana[skupina.md.ucet][skupina.dal.ucet] = protistrana[skupina.md.ucet].get(skupina.dal.ucet, 0) - skupina[suma]

        ucty[skupina.dal.ucet] = ucty.get(skupina.dal.ucet, 0) - skupina[suma]
        if protistrana.get(skupina.dal.ucet) is None:
            protistrana[skupina.dal.ucet] = {}
        protistrana[skupina.dal.ucet][skupina.md.ucet] = protistrana[skupina.dal.ucet].get(skupina.md.ucet, 0) + skupina[suma]

    if need_commit:
        db.commit()

    naklady = vynosy = 0
    for ucet_cislo, ucet_castka in ucty.items():
        if ucet_cislo:
            if ucet_cislo[0]=='5':
                naklady += ucet_castka
            elif ucet_cislo[0]=='6':
                vynosy -= ucet_castka

    return dict(rok=rok, mesic_od=mesic_od, mesic_do=mesic_do,
            den_od=den_od.strftime('%Y%m%d'), den_po=den_po.strftime('%Y%m%d'),
            skupiny=skupiny, pocet=pocet, suma=suma,
            ucty=ucty, ucty_dict=ucty_dict, protistrana=protistrana,
            naklady=naklady, vynosy=vynosy)

@auth.requires_membership('admin')
def prubezne():
    from mz_wkasa_platby import Uc_sa

    def ucty_init(ucty, ucet_id):
        ucty[ucet_id]['stav'] = {}
        ucty[ucet_id]['pohyb'] = {}
        ucty[ucet_id]['md'] = {}
        ucty[ucet_id]['dal'] = {}
        pohyb = ucty[ucet_id]['pohyb']
        md = ucty[ucet_id]['md']
        dal = ucty[ucet_id]['dal']
        stav = ucty[ucet_id]['stav']
        for rok in xrange(2010, letos + 1): # 2010: i pro 2011 vypisujeme předchozí
            pohyb[rok] = 0
            md[rok] = 0
            dal[rok] = 0
            stav[rok] = 0

    letos = datetime.date.today().year
    ucty_rows = db(db.ucet).select()
    ucty = {}

    ucty[0] = {}
    ucty[0]['ucet'] = '?'
    ucty[0]['nazev'] = '<neurčeno>'
    ucty_init(ucty, 0)
    ucty[-1] = {} # ZAL=osobní zálohy (z pohybů)
    ucty[-1]['ucet'] = 'ZAL'  # musí být vyplněno, je to klíč pro třídění
    ucty[-1]['nazev'] = 'závazek: osobní zálohy neumístěné na akce (z pohybů)'
    ucty_init(ucty, -1)

    for ucet in ucty_rows:
        ucty[ucet.id] = {}
        ucty[ucet.id]['ucet'] = ucet.ucet
        ucty[ucet.id]['nazev'] = ucet.nazev
        ucty_init(ucty, ucet.id)

    kredit_pohyb = {}  # zákaznické zálohy podle pohybů
    kredit_soucet = {}
    for rok in xrange(2010, letos + 1): # 2010: i pro 2011 vypisujeme předchozí
        kredit_pohyb[rok] = kredit_soucet[rok] = 0

    pohyby = db(db.pohyb).select(orderby=db.pohyb.datum)
    kasa = 0
    zapor = False
    chybi = ''
    pod = 0
    for pohyb in pohyby:
        # kontrola, zda pokladna není v záporu
        if pohyb.idma_dati==Uc_sa.pokladna:
            kasa += pohyb.castka
            if zapor and kasa>=0:
                zapor = False
                chybi += ' - %s - Kč %s<br />' % (pohyb.datum.strftime('%d.%m.%Y'), -pod)
                pod = 0
        elif pohyb.iddal==Uc_sa.pokladna:
            kasa -= pohyb.castka
            pod = min((pod, kasa))
            if not zapor and kasa<0:
                zapor = True
                chybi += pohyb.datum.strftime('%d.%m.%Y')

        rok = pohyb.datum.year
        ucty[pohyb.idma_dati or 0]['md'][rok] += pohyb.castka
        ucty[pohyb.iddal or 0]['dal'][rok] += pohyb.castka
        ucty[pohyb.idma_dati or 0]['pohyb'][rok] += pohyb.castka
        ucty[pohyb.iddal or 0]['pohyb'][rok] -= pohyb.castka
        if pohyb.idauth_user:
            if pohyb.idma_dati in Uc_sa.gl_ozwk:  # OsZ, >SA
                ucty[-1]['md'][rok] += pohyb.castka
                ucty[-1]['pohyb'][rok] -= pohyb.castka
            if pohyb.iddal in Uc_sa.gl_ozwk:
                ucty[-1]['dal'][rok] += pohyb.castka
                ucty[-1]['pohyb'][rok] += pohyb.castka

    if zapor:  # dotisk načatého řádku
        chybi += ' - %s - Kč %s<br />' % (pohyb.datum.strftime('%d.%m.%Y'), -pod)

    for rok in xrange(2011, letos + 1):
        for rok_b in xrange(2011, rok + 1):
            for ucet in ucty:
                ucty[ucet]['stav'][rok] += ucty[ucet]['pohyb'][rok_b]

    soucet = db.auth_user.zaloha.sum()
    zaloha_ted = db().select(soucet).first()[soucet]

    return dict(ucty=ucty,
        chybi = chybi,
        od_roku=request.args(0) or letos,
        zaloha_zakaznik=zaloha_ted  # < ucty[-1=ZAL], dokud vrácení záloh (None/221) není určeno
        )

@auth.requires_membership('admin')
def osnova():
    return dict(ucty = db(db.ucet).select(orderby=db.ucet.ucet))

@auth.requires_membership('admin')
def dp():
    def zapis_mesice(akt_rok, akt_mesic, dne, ziskano, ziskano_mesice):
        '''přelité osobní zálohy po měsících
        '''
        if (dne is None) or pohyb.datum.month!=akt_mesic or pohyb.datum.year!=akt_rok:
            if dne is None:
                dnes = datetime.date.today()
                akt_rok = dnes.year
                akt_mesic = dnes.month
            ziskano_mesice.append((akt_rok, akt_mesic, ziskano))
            if dne is not None:
                akt_rok = dne.year
                akt_mesic = dne.month
        return akt_rok, akt_mesic

    preklenovaci_ucet = db(db.ucet.ucet=='96').select().first().id
    permice_ucet = db(db.ucet.ucet=='213').select().first().id
    vynosy_akci_ucet = db(db.ucet.ucet=='602').select().first().id
    fungujeme_ucet = db(db.ucet.ucet=='379-12').select().first().id

    expr_max = db.pohyb.datum.max()
    iniciovano_ke_dni = db((db.pohyb.idma_dati==preklenovaci_ucet)|(db.pohyb.iddal==preklenovaci_ucet)).select(expr_max).first()[expr_max]
    if iniciovano_ke_dni is None:
        expr_min = db.pohyb.datum.min()
        iniciovano_ke_dni = db().select(expr_min).first()[expr_min]
        if iniciovano_ke_dni is None:
            iniciovano_ke_dni = datetime.date.today()
    iniciovany_rok = iniciovano_ke_dni.year
    k_datu_default = min(datetime.date(iniciovany_rok, 12, 31), datetime.date.today())

    permice_in = db((db.pohyb.datum>=iniciovano_ke_dni) & (db.pohyb.idma_dati==permice_ucet)).select(orderby=db.pohyb.datum)
    permice_out = db((db.pohyb.datum>=iniciovano_ke_dni) & (db.pohyb.iddal==permice_ucet)).select(orderby=db.pohyb.datum)
    permice_max = 0
    for permice in permice_in:
        permice_max += permice.castka
    for permice in permice_out:
        permice_max -= permice.castka

    fungujeme = db((db.pohyb.datum>=iniciovano_ke_dni) & ((db.pohyb.idma_dati==fungujeme_ucet) | (db.pohyb.iddal==fungujeme_ucet))).select(orderby=db.pohyb.datum)
    akt_rok = iniciovano_ke_dni.year
    akt_mesic = iniciovano_ke_dni.month
    ziskano = 0
    ziskano_mesice = []
    prevedeno = 0
    prevedeno_dne = None
    for pohyb in fungujeme:
        akt_rok, akt_mesic = zapis_mesice(akt_rok, akt_mesic, pohyb.datum, ziskano, ziskano_mesice)
        if pohyb.iddal==fungujeme_ucet:
            ziskano += pohyb.castka
        elif pohyb.iddal==vynosy_akci_ucet:
            prevedeno += pohyb.castka
            prevedeno_dne = pohyb.datum
        else:
            ziskano -= pohyb.castka
    else:
        zapis_mesice(akt_rok, akt_mesic, None, ziskano, ziskano_mesice)

    return dict(permice_in=permice_in, permice_out=permice_out,
            ziskano_mesice=ziskano_mesice, ziskano=ziskano,
            prevedeno=prevedeno, prevedeno_dne=prevedeno_dne,
            permice_max=permice_max)