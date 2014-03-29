# coding: utf8

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
    for pohyb in pohyby:
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
                
    for rok in xrange(2011, letos + 1):
        for rok_b in xrange(2011, rok + 1):
            for ucet in ucty:
                ucty[ucet]['stav'][rok] += ucty[ucet]['pohyb'][rok_b]
    
    soucet = db.auth_user.zaloha.sum()
    zaloha_ted = db().select(soucet).first()[soucet]
    
    return dict(ucty=ucty,
        od_roku=request.args(0) or letos,
        zaloha_zakaznik=zaloha_ted  # < ucty[-1=ZAL], dokud vrácení záloh (None/221) není určeno
        )

@auth.requires_membership('admin')
def osnova():
    ucty_rows = db(db.ucet).select()
    ucty_dict = {}
    for ucet in ucty_rows:
        ucty_dict[ucet.ucet] = ucet.nazev
    return ucty_dict
