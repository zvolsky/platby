# coding: utf8

from mz_wkasa_platby import fix_login, Uc_sa
    # Uc_sa - id účtů účtové osnovy - při importu zde je vidí controléry i views

db.define_table('ucet',
    Field('ucet', length=7),
    Field('zkratka', length=3),
    Field('nazev', length=100),
    format='%(ucet)s - %(nazev)s'
    )

db.define_table('pohyb',
    Field('idauth_user', 'reference auth_user', label=TFu("Uživatel"),
          requires=IS_EMPTY_OR(IS_IN_DB(db, db.auth_user.id, '%(nick)s - %(vs)s'))),
    Field('idorganizator', 'reference auth_user', label=TFu("Zadal organizátor"),
          readable=False, writable=False,
          requires=IS_EMPTY_OR(IS_IN_DB(db, db.auth_user.id, '%(nick)s - %(vs)s'))),
    Field('idma_dati', 'reference ucet'),
    Field('iddal', 'reference ucet'),
    Field('datum', 'datetime',
          requires=[IS_NOT_EMPTY(), IS_DATETIME(format=TFu('%d.%m.%Y'))]),
    Field('castka', 'decimal(11,2)'),
    Field('popis', 'text'),
    Field('cislo_uctu', length=30),
    Field('kod_banky', length=10),
    Field('nazev_banky', length=40),
    Field('zakaznik', length=10),
    Field('vs', length=10, default=''),
    Field('ss', length=10, default=''),
    Field('ks', length=4, default=''),
    Field('id_pohybu', length=12),
    Field('id_pokynu', length=12),
    )

db.define_table('systab',
    Field('kod', length=12),
    Field('hodnota', length=100),
    )

db.define_table('loginlog',
    Field('idauth_user', 'reference auth_user'),
    Field('datum', 'date'),
    )

db.define_table('zadost',
    Field('zadost', 'datetime', label="Datum žádosti"),
    Field('idauth_user', 'reference auth_user', label="Uživatel"),
    Field('vyridil_id', 'reference auth_user', label="Vyřídil"),
    Field('vs', length=10, label="Symbol",
          comment="symbol uživatele"),
    Field('ss', length=10, label="Symbol obsol",
          comment=""),
    Field('typ', 'integer', label='Typ žádosti',
          comment='1 sa->wKasa, 2->na BÚ, 3 členství, 4 refundace'),
    Field('cislo_uctu', length=30, label='Číslo účtu'),
    Field('kod_banky', length=10, label='Kód banky'),
    Field('popis', 'text'),
    Field('prevod', 'datetime', label='Datum vyřízení'),
    Field('zadano', 'decimal(11,2)', label='Žádaná částka'),
    Field('prevedeno', 'decimal(11,2)', label='Převedená částka'),
    )

db.define_table('clenstvi',
    Field('user_id', 'reference auth_user', label="Uživatel"),
    Field('group_id', 'reference auth_group', label="Role ve sdružení"),
    Field('ode_dne', 'date', label="Ode dne"),
    Field('do_dne', 'date', label="Do dne"),
    )

fix_login(db, auth, vs_default)  # každému dát osobní symbol, logovat
    
## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)
