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
from splinter import Browser

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

bidMidMap = {}
def loadBidMidMap(config):
    bidmidFile = config['bidmid_file']
    fi = open(bidmidFile, 'r')
    for line in fi.readlines():
        fs = line.strip().split('\t')
        bid = fs[0].strip()
        mid = fs[1].strip()
        bidMidMap[bid] = mid
    fi.close()

from PageClass import PageDealer
class EuropePageDetail(PageDealer):
    columns = 'id\t欧赔公司\t欧赔-胜\t欧赔-平\t欧赔-负\t胜率\t和率\t负率\t凯利-胜\t凯利-平\t凯利-负\t变盘url'
    def __init__(self, config):
        PageDealer.__init__(self, config)
        path = self._path + '.' + config['round_interval']
        self._fo = open(path, self._mode)
        if os.path.getsize(path) < 10:
            self._fo.write('%s\n' % EuropePageDetail.columns)
        self._foExcept = open(config['except_path'], config['except_mode'])
    def pick(self,request):
        if len(request) > 0:
            self._request = request
        print 'pick url: %s with request: %s' % \
                (self._url, self._request)
        #br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20100101 Firefox/15.0.1')]
        try:
            br.visit(self._url)
            retryTimes = 0
            while not br.status_code.is_success():
                time.sleep(random.randint(20,60))
                br.reload()
                retryTimes += 1
                if retryTimes > 5:
                    break
            if retryTimes > 0:
                print 'reload url %d times.' % retryTimes
        except:
            print 'Failed to visit: %s' % self._url
            self._foExcept.write('%s\t%s\n' % \
                    (self._round, self._url))
            time.sleep(90)
            return []
        body = unicode(br.html)#, self._charset)
        if body.find('table') == -1:
            print 'still bad page. remember this and try later.'
            self._foExcept.write('%s\t%s\n' % (self._round, self._url))
            return []
        page = BeautifulSoup(body, 'html5lib')
        goodBody = page.find('body')
        if len(self._request) == 0:
            tables = goodBody.find_all('table')
        else:
            tables = goodBody.find_all('table', self._request)
        #br.windows.current.close()
        return tables
    def parse(self, tables):
        print 'start parse table[0] in url: %s' % self._url
        trs = tables[0].find_all('tr')
        companyName = '平均欧赔'
        tds = trs[3].find_all('td')
        retInfo = ''
        retInfo += self._round
        retInfo += '\t'
        retInfo += companyName + '\t'
        for td in tds[:-1]:
            retInfo += unicode(td.string) + '\t'
        retInfo += tds[-1].find('a')['href'] + '\n'
        self._fo.write('%s' % retInfo)
        #continue other companies.
        for tr in trs[6:]:
            tds = tr.find_all('td')
            if len(tds) != 11:
                print 'roundId=%s sys.exit() bad tds: %s' % \
                        (self._round, tds)
                self._fo.close()
                sys.exit()
            retInfo = ''
            retInfo += self._round
            retInfo += '\t'
            for td in tds[:-1]:
                retInfo += unicode(td.string) + '\t'
            retInfo += tds[-1].find('a')['href'] + '\n'
            self._fo.write('%s' % retInfo)
        self._fo.close()
        return []

UrlPattern = 'http://odds.sports.sina.com.cn/liveodds/marker_list_old.php?m_id='
def yieldPage(config):
    rounds = config['round_interval'].strip().split('-')
    for bid, mid in sorted(bidMidMap.items(), key = lambda en : en[0]):
        if bid[:-3] >= rounds[0] and bid[:-3] <= rounds[1]:
            url = UrlPattern + mid
            config['url'] = url
            config['round'] = bid
            print 'set config for url: %s; round: %s' % \
                    (config['url'], config['round'])
            yield EuropePageDetail(config)
    return

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
    loadBidMidMap(config)


    #br = Browser('firefox', user_agent='Mozilla/5.0 (Centos 6.7; WOW64; rv:15.0) Gecko/20100101 Firefox/15.0.1')
    br = Browser('firefox')
    for page in yieldPage(config):
        tables = page.pick({})
        if len(tables) == 0:
            continue
        follows = page.parse(tables)
        while len(follows) > 0:
            p = follows.pop(0)
            tbs = p.pick()
            tmpFollows = p.parse(tbs)
            if len(tmpFollows) > 0:
                for tf in tmpFollows:
                    follows.append(tf)
    #br.windows.current.close()
    br.quit()


