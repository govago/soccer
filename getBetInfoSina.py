#!/usr/bin/env python
#coding=utf-8

'''
get main bet information.
for old sina bet infomation
because html format is old.
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

def loadConfig(cf):
    try:
        fi = open(cf, 'r')
        config = json.load(fi)
        fi.close()
        return config
    except:
        traceback.print_exc()
        return None

#load fetch urls
def loadFetchurlsFromFile(fileName, config):
    fi = open(fileName, 'r')
    rifs = config['round_interval'].split('-')
    rend = int(rifs[1])
    rstart = int(rifs[0])
    urls = []
    for line in fi.readlines():
        if line.startswith('#'):
            continue
        fs = line.strip().split('\t')
        round = int(fs[0])
        if round >= rstart and round <= rend:
            urls.append( (round, fs[1]) )
    fi.close()
    return urls

def loadFetchurls(config):
    ri = config['round_interval']
    print 'get round_interval: %s\n' % ri
    urls = []
    rifs = ri.split('-')
    if len(rifs) == 2:
        rstart = int(rifs[0])
        rend = int(rifs[1])
        round = rstart
        while round <= rend:
            #url = config['url_pattern'].replace('${round}', '%05d'%round)
            url = config['url_pattern'].replace('${round}', str(round))
            urls.append( (round,url) )
            round += 1
    else:
        rstart = int(ri)
        #url = config['url_pattern'].replace('${round}', '%05d'%rstart)
        url = config['url_pattern'].replace('${round}', str(rstart))
        urls.append( (rstart,url) )
    return urls

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
    sp = body.index('<div class="Main">')
    ep = body.index('<div class="MainBorderBottom">')
    goodBody = body[sp:ep]
    page = BeautifulSoup(goodBody, 'html5lib')
    if len(request) == 0:
        sub = page.find('div', id='artibody')
        tables = sub.find_all('table')
    else:
        tabls = page.find_all('table', request)
    if len(tables) == 0:
        pdb.set_trace()
    return tables

def getTableFromPageOld(url, request, charset):
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
    subPage = page.find('table', class_='vsplit')
    if len(request) == 0:
        tables = subPage.find_all('table')
    else:
        tables = subPage.find_all('table', request)
    if len(tables) == 0:
        pdb.set_trace()
    return tables

def getFollowLink(roundId, matchId, td):
    tda = td.find('a')
    link = tda['href']
    return '%05d-%02d\t%s' % \
            (roundId, matchId, link)

class FollowContext:
    def __init__(self, config, roundInterval):
        self._column = int(config['column'])
        self._path = config['links_path'] + '.' + roundInterval
        self._fo = open(self._path, 'w')
        print 'follow context: (c)%d, %s' % \
                (self._column, self._path)
    def __del__(self):
        self._fo.close()
    def dump(self, link):
        self._fo.write('%s\n' % link)
    def column(self ):
        return self._column
    def dumpFollow(self, rid, mid, tds) :
        link = getFollowLink(rid, mid, tds[self._column])
        self.dump(link)

class TableContext:
    def __init__(self, config, roundInterval):
        if config['table_has_header'].lower() == 'yes':
            self._header = True
        else:
            self._header = False
        self._title = config['table_column']
        self._columns = len(self._title.split('\t'))
        self._selects = []
        for idx in config['select_column'].split(','):
            self._selects.append(int(idx))
        self._commons = []
        self._commonValues = []
        for idx in config['common_column'].split(','):
            self._commons.append(int(idx))
            self._commonValues.append(None)
        self._path = config['output_path'] + '.' + roundInterval
        self._fo = open(self._path, 'w')
        header = 'betid\t%s' % unicode(config['table_column'])
        self._fo.write('%s\n' % header)
        self._property = config['table_property']
        self._matchColumn = config['match_column']
        self._lastRow = config['table_last_row']
        print 'get table title: %s\noutput: %s\n' % \
                (self._title, self._path)
        print 'get table _columns=%d,_selects=%s,_commons=%s' % \
                (self._columns, self._selects, self._commons)
        print 'get table _matchColumn=%d, _lastRow=%d' % \
                (self._matchColumn, self._lastRow)
        fls = config['follow_link']
        self._follows = []
        for name, conf in fls.items():
            print 'get follow link for: %s' % name
            self._follows.append(FollowContext(conf, roundInterval))
    def __del__(self):
        self._fo.close()
    def getDataFromTdA(self, td):
        if None == td.string:
            a = td.find_all('a')
            return unicode(a[0].string)
        else:
            return unicode(td.string)
    def parseTable(self, roundId, table):
        print '\tparse table for round: %d' % roundId
        trs = table.find_all('tr')
        for i in xrange(0, self._lastRow):
            if self._header and i == 0:
                continue
            tds = trs[i].find_all('td')
            if len(tds) < self._columns - len(self._commons):
                print '!!!!not full @roundId=%d, return' % roundId
                return
            if len(tds) == self._columns:
                for idx in self._commons:
                    self._commonValues[idx] = unicode(tds[idx].string)
            else:
                for idx in self._commons:
                    tds.insert(idx, self._commonValues[idx])
            values = []
            matchId = 0
            for idx in self._selects:
                if isinstance(tds[idx], unicode):
                    values.append(tds[idx])
                else:
                    #values.append( unicode(tds[idx].string) )
                    values.append(self.getDataFromTdA(tds[idx]))
                if idx == self._matchColumn:
                    matchId = int(values[-1])
            values.insert(0, '%05d-%02d' % (roundId, matchId))
            trline = '\t'.join(values)
            self._fo.write('%s\n' % trline)
            #deal with following links in the table row
            for fl in self._follows:
                fl.dumpFollow(roundId, matchId, tds)

import pdb
if __name__ == '__main__':

    configFile = ''
    opts, args = getopt.getopt(sys.argv[1:], 'c:f:')
    for op, value in opts:
        if op == '-c':
            configFile = value.strip()
            print 'get config file: %s' % configFile
        if op == '-f':
            urlFile = value.strip()
            print 'get url file: %s' % urlFile

    if len(configFile) == 0:
        print 'no config file. exit'
        sys.exit(-1)
    config = loadConfig(configFile)
    if None == config:
        print 'load config failed. exit'
        sys.exit(-1)

    if None == urlFile:
        urls = loadFetchurls(config)
    else:
        urls = loadFetchurlsFromFile(urlFile, config)

    tableContext = TableContext(config, config['round_interval'])
    tableProperty = config['table_property']
    charset = config['charset']
    print 'get charset=%s' % charset

    for roundId, url in urls:
        print '--->roundId = %05d; %s' % (roundId, url)
        if roundId <= 8048:
            kwargs = { 'class' : 'IF_table' }
            tbs = getTableFromPageOld(url, kwargs, charset)
        else:
            tbs = getTableFromPage(url, tableProperty, charset)
        if len(tbs) == 0:
            print '\tfind no table in page. bad. coninue'
            continue
        tableContext.parseTable(roundId, tbs[0])

        time.sleep(random.randint(1,5))

