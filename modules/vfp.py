# coding: utf8
#-------------------------------------------------------------------------------
# Name:        vfp
# Purpose:     mimics behaviour of some Visual FoxPro functions
#
# Author:      Mirek Zvolsky
#
# Created:     07.12.2011
# Licence:     public domain
#-------------------------------------------------------------------------------
#!/usr/bin/env python

"""mimics behaviour of some Visual FoxPro functions"""

def filetostr(fname):
    """return content of the file"""
    f = open(fname, 'rb')
    content = f.read()
    f.close()
    return content

def strtofile(content, fname, additive=0, encoding='mbcs'):
    """writes string to file
    expression - string to output to the fname file
    fname - output filename
    additive - default=rewrite, 1 (or True)=append
        vfp par nFlag>1 (nFlag ~ additive) not implemented yet"""
            # mbcs in windows is the default encoding,
            #   f.e. in czech windows it means windows-1250
            # on non-windows systems enter 'windows-1250' explicitly
    length = 0
    if content:
        if type(content)==unicode:
            encoded = content.encode(encoding)
        else:
            encoded = content
        try:
            f = open(fname, 'ab' if additive else 'wb')
            f.write(encoded)
            f.close()
            length = len(encoded)
        except:
            pass
    return length

def strtoutf8file(content, fname, additive=0, encoding='mbcs'):
    """writes string to file
    expression - string to output to the fname file
    fname - output filename
    additive - default=rewrite, 1 (or True)=append
        vfp par nFlag>1 (nFlag ~ additive) not implemented yet"""
            # mbcs in windows is the default encoding,
            #   f.e. in czech windows it means windows-1250
            # on non-windows systems enter 'windows-1250' explicitly
    length = 0
    utf8leadingbyte = chr(239)+chr(187)+chr(191)
    if type(content)==str:
        content = unicode(content, encoding)
                # mbcs in windows is the default encoding,
                #   f.e. in czech windows it means windows-1250
    encoded = ('' if additive else utf8leadingbyte) + content.encode('utf-8')
    if content:
        try:
            f = open(fname, 'ab' if additive else 'wb')
            f.write(encoded)
            f.close()
            length = len(encoded)
        except:
            pass
    return length
