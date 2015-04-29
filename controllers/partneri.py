# coding: utf8

@auth.requires_membership('vedení')
def prehled():
    return dict(grid=SQLFORM.grid(db.partner,
              fields=[db.partner.ucel,
                  db.partner.nazev, db.partner.misto,
                  db.partner.kontakt, db.partner.poznamka
                  ],
              deletable=False,
              editable=auth.has_membership('vedení'),
              create=auth.has_membership('vedení'),
              csv=auth.has_membership('vedení'),
              showbuttontext=False,
              paginate=100,
              orderby=db.partner.typp_id,
              maxtextlengths={'partner.kontakt' : 40, 'partner.poznamka' : 40}
              ))
