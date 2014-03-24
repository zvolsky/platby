# coding: utf8

@auth.requires_membership('admin')
def prehled():
    return dict(grid=SQLFORM.grid(db.fp,
              fields=(db.fp.zauctovana, db.fp.vystaveno, db.fp.uhrazeno,
                  db.fp.no_jejich, db.fp.castka, db.fp.poznamka
                  ),
              deletable=auth.has_membership('pokladna'),
              editable=auth.has_membership('pokladna'),
              create=auth.has_membership('pokladna'),
              csv=auth.has_membership('admin'),
              paginate=100,
              orderby=db.fp.vystaveno,
              maxtextlengths={'fp.poznamka' : 40}
              ))

@auth.requires_membership('pokladna')
def zauctovani():
    nezauctovane = db(db.fp.zauctovana==False).select()
    ucet_fp = db(db.ucet.ucet=='321').select().first().id
    prijate = db(db.pohyb.iddal==ucet_fp).select()
    platby = db(db.pohyb.idma_dati==ucet_fp).select()
    return dict(prijate=prijate, platby=platby, nezauctovane=nezauctovane)
