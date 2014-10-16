# -*- coding: utf8 -*-

import os
import vfp

def clean_sessions():
    zruseno = 0
    session_dir = os.path.join(request.folder, 'sessions')
    for dummy_jmeno, dummy_dirs, soubory1 in os.walk(session_dir):
        # soubory podle času změny (nevím, jak to dělat lépe)
        soubory2 = []
        for soubor in soubory1:
            psoubor = os.path.join(session_dir, soubor) 
            soubory2.append([psoubor, os.stat(psoubor).st_mtime])
        soubory2.sort(key=lambda r:r[1], reverse=True)
        
        # smazat soubory bez mailů a starší se stejným mailem
        maily_uz_mam = []
        for soubor, dummy_cas in soubory2:
            obsah = vfp.filetostr(soubor)
            if '@' in obsah:
                for mozna_mail in obsah.split("'"):
                    if '@' in mozna_mail:
                        if mozna_mail in maily_uz_mam: 
                            zruseno += delete(soubor)
                        else:
                            maily_uz_mam.append(mozna_mail)
                        break
            else:
                zruseno += delete(soubor)
        break  # jen root (nevím, jak to dělat lépe než pomocí os.walk)
    print 'zrušeno: %s\n'%zruseno 

def delete(soubor):
    try:
        os.remove(soubor)
        zruseno = 1
    except:
        zruseno = 0
    return zruseno

if __name__=='__main__':
    clean_sessions() 