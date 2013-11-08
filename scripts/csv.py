# -*- coding: utf8 -*-

from export_csv import export_csv

def csv():
    pocet = export_csv(db, request.folder)
    db.commit()
    return "csv exportováno %s" % pocet

if __name__=='__main__':
    csv()