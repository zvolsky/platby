# -*- coding: utf8 -*-

def update_fio():
    from import_fio_sa import import_pohyby_sa
    import_pohyby_sa(db)

'''toto mám vždy ve fixdata
def oprav_fio():
    from import_fio_sa import import_pohyby_sa
    import_pohyby_sa(db, od='2013-11-05', od='2013-11-08')
'''

def reset():
    from import_fio_sa import reset_pointer
    reset_pointer()

if __name__=='__main__':
    update_fio()