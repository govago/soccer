#!/usr/bin/env python
#coding=utf-8

'''
get sina,09001-09042, and '08 all match urls
'''
import json
from bs4 import BeautifulSoup
import re
import mechanize
import sys, getopt
import traceback
import time
import random

reload(sys)
sys.setdefaultencoding('utf-8')

import pdb
def getTableFromPage(url, request, charset):
    br = mechanize.Browser()
    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20100101 Firefox/15.0.1')]
    response = br.open(url)
    body = unicode(response.read(), charset)
    page = BeautifulSoup(body, 'html5lib')
    try:
        contentBody = page.find('body', id='conBody').\
            find_all('center')[0]
    except:
        pdb.set_trace()
    if len(request) == 0:
        tables = contentBody.find_all('table')
    else:
        tabls = contentBody.find_all('table', request)
    return tables

def getTableFromPageDetail(url, request, charset):
    br = mechanize.Browser()
    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20100101 Firefox/15.0.1')]
    response = br.open(url)
    body = unicode(response.read(), charset)
    sp = body.index('<center>')
    ep = body.index('</center>')
    bodyCenter = body[sp:ep+9]
    contentBody = BeautifulSoup(bodyCenter, 'html5lib')
    '''
    try:
        contentBody = page.find('body', id='conBody').\
            find_all('center')[0]
    except:
        pdb.set_trace()
    '''
    if len(request) == 0:
        tables = contentBody.find_all('table')
    else:
        tabls = contentBody.find_all('table', request)
    return tables

udi = u'\u7b2c'
uqi = u'\u671f'
def getRoundLinksFromTable(table, fo):
    tras = table.find_all('a')
    for ta in tras:
        link = ta['href']
        name = unicode(ta.string)
        if name == None or len(name) == 0:
            continue
        ddname = name.strip(udi)
        ddname = ddname.strip(uqi)
        try:
            roundId = int(ddname)
            fo.write('%05d\t%s\n' % (roundId, link))
        except:
            print 'Failed convert name: %s\nlink: %s' % \
                    (name, link)
    return

if __name__ == '__main__':
    charset = 'gbk'
    url = 'http://sports.sina.com.cn/l/2012-05-11/10006056978.shtml'
    tbs = getTableFromPage(url, "", charset)
    print 'get table number: %d' % len(tbs)
    fo = open('data/sina.old.rounds', 'w')
    getRoundLinksFromTable(tbs[2], fo)
    fo.flush()
    url = 'http://sports.sina.com.cn/l/2010-03-03/12094867321.shtml'
    print 'start new url: %s' % url
    tbs = getTableFromPageDetail(url, "", charset)
    print 'get table number: %d' % len(tbs)
    getRoundLinksFromTable(tbs[0], fo)
    fo.close()

