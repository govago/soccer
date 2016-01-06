#!/usr/bin/env python
#coding=utf-8

'''
get main bet information.
main entrance of web site.
'''
import json
from bs4 import BeautifulSoup
import re
import mechanize
import sys, getopt
import traceback
import time

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
            url = config['url_pattern'].replace('${round}', str(round))
            urls.append( (round,url) )
            round += 1
    else:
        rstart = int(ri)
        url = config['url_pattern'].replace('${round}', str(rstart))
        urls.append( (rstart,url) )
    return urls

def getTableFromPage(url, request):
    br = mechanize.Browser()
    response = br.open(url)
    response = br.reload()
    charset = 'gb2312'
    try:
        responseInfo = str(response.info())
        charsetIdx = responseInfo.index('charset=')
        charset = responseInfo[charsetIdx+8:-1]
        print '\tget charset=%s url: %s\n' % (charset, url)
    except:
        print traceback.print_exc()
        print response.read()
        charset = 'gb2312'
    body = unicode(response.read(), charset)
    page = BeautifulSoup(body, 'html5lib')
    if len(request) == 0:
        tables = page.find_all('table')
    else:
        tabls = page.find_all('table', request)
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
    opts, args = getopt.getopt(sys.argv[1:], 'c:')
    for op, value in opts:
        if op == '-c':
            configFile = value.strip()
            print 'get config file: %s' % configFile

    if len(configFile) == 0:
        print 'no config file. exit'
        sys.exit(-1)
    config = loadConfig(configFile)
    if None == config:
        print 'load config failed. exit'
        sys.exit(-1)

    urls = loadFetchurls(config)

    tableContext = TableContext(config, config['round_interval'])
    tableProperty = config['table_property']

    for roundId, url in urls:
        print '--->roundId = %05d; %s\n' % (roundId, url)
        tbs = getTableFromPage(url, tableProperty)
        if len(tbs) == 0:
            print '\tfind no table in page. bad. coninue'
            continue
        tableContext.parseTable(roundId, tbs[0])
        time.sleep(1)

