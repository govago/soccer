#!/usr/bin/env python
#coding=utf-8

import json
from bs4 import BeautifulSoup
import re
import mechanize
import sys, getopt
import traceback
import time
import random
import os

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

from PageClass import PageDealer
class EuropePage(PageDealer):
    columns = 'id\t欧赔公司\t欧赔-胜\t欧赔-平\t欧赔-负\t胜率\t和率\t负率\t返还率\t凯利-胜\t凯利-平\t凯利-负\t最新变盘时间'
    def __init__(self, config):
        PageDealer.__init__(self, config)
        path = self._path + '.' + config['round_interval']
        self._fo = open(path, self._mode)
        if os.path.getsize(path) < 10:
            self._fo.write('%s\n' % EuropePage.columns)
    def pick(self,request):
        if len(request) > 0:
            self._request = request
        print 'pick url: %s with request: %s' % \
                (self._url, self._request)
        br = mechanize.Browser()
        br.set_handle_equiv(True)
        br.set_handle_gzip(True)
        br.set_handle_redirect(True)
        br.set_handle_referer(True)
        br.set_handle_robots(False)
        br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
        br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20100101 Firefox/15.0.1')]
        response = br.open(self._url)
        body = unicode(response.read(), self._charset)
        page = BeautifulSoup(body, 'html5lib')
        goodBody = page.find('body', id='sortable')
        if len(self._request) == 0:
            tables = goodBody.find_all('table')
        else:
            tables = goodBody.find_all('table', self._request)
        return tables
    def parse(self, tables):
        print 'start parse table[0] in url: %s' % self._url
        trs = tables[0].find_all('tr')
        for tr in trs[2:]:
            tds = tr.find_all('td')
            startIdx = 0
            if len(tds) != 13 and len(tds) != 11:
                print 'roundId=%s sys.exit() bad tds: %s' % \
                        (self._round, tds)
                self._fo.close()
                sys.exit()
            retInfo = ''
            retInfo += self._round
            retInfo += '\t'
            if len(tds) == 13:
                companyName = unicode(tds[1].string)
            else:
                retInfo += companyName + '\t'
                startIdx += 1
            for td in tds[startIdx:]:
                retInfo += unicode(td.string) + '\t'
            retInfo += '\n'
            self._fo.write('%s' % retInfo)
        self._fo.close()
        return []

def yieldPage(config, urlfi):
    line = urlfi.readline().strip()
    if len(line) < 2:
        urlfi.close()
        return
    fs = line.split('\t')
    roundId = fs[0]
    url = fs[1]
    config['url'] = url
    config['round'] = roundId
    print 'set config for url: %s; round: %s' % \
            (config['url'], config['round'])
    yield EuropePage(config)

import pdb
if __name__ == '__main__':
    
    opts, args = getopt.getopt(sys.argv[1:], 'c:')
    for op, value in opts:
        if op == '-c':
            configFile = value.strip()
            print 'get config file: %s' % configFile
    config = loadConfig(configFile)
    if None == config:
        print 'load config failed. exit'
        sys.exit(-1)

    urlfile = config['urls_file']
    urlfi = open(urlfile, 'r')
    tableRequest = {'id':'dongtaiOuPan'}
    for page in yieldPage(config, urlfi):
        pdb.set_trace()
        tables = page.pick(tableRequest)
        follows = page.parse(tables)
        while len(follows) > 0:
            p = follows.pop(0)
            tbs = p.pick()
            tmpFollows = p.parse(tbs)
            if len(tmpFollows) > 0:
                for tf in tmpFollows:
                    follows.append(tf)

