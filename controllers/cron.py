def update_fio():
    from import_fio_sa import import_pohyby_sa
    import_pohyby_sa(db)

def reset():
    from import_fio_sa import reset_pointer
    reset_pointer()
