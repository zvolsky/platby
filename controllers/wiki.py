# coding: utf8

'''pro práva editace přidat do skupin wiki_editor, wiki_author'''

@auth.requires_membership('pokladna')
def index():
    return auth.wiki()
