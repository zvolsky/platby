# -*- coding: utf8 -*-

from export_csv import export_csv

def csv():
    pocet = export_csv(db)
    db.commit()
    return "csv exportováno %s" % pocet
