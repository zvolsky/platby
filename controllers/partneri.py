# coding: utf8

@auth.requires_membership('admin')
def prehled():
    return dict(grid=SQLFORM.grid(db.partner,
              fields=(db.partner.ucel,
                  db.partner.nazev, db.partner.misto,
                  db.partner.kontakt, db.partner.poznamka
                  ),
              deletable=auth.has_membership('pokladna'),
              editable=auth.has_membership('admin'),
              create=auth.has_membership('admin'),
              csv=auth.has_membership('admin'),
              paginate=100,
              orderby=db.partner.typp_id,
              maxtextlengths={'partner.kontakt' : 40, 'partner.poznamka' : 40}
              ))
