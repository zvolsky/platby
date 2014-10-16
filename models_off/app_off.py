# pro odstaveni nakopirovat do models,
# pripadne na prvnim radku zpruchodnit jednu adresu zjistenou pomoci
#     platby.alwaysdata.net/odstaveno/ip

if not request.env.http_host=='localhost:8000':
    if not request.controller=='odstaveno':
        redirect(URL('odstaveno', 'info'))
