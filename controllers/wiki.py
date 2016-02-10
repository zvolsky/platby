# coding: utf8

@auth.requires_membership('pokladna')
def index():
    return auth.wiki()
