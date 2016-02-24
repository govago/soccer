#!/usr/bin/env python
#coding=utf-8

'''
page context for processing PageProcessor
'''
import json
import sys, getopt
import traceback
import time
import random
import traceback
import shutil
import os

from PageProcessor import PageProcessor
from PageProcessor import BrowserManager

def LoadConfig(cf):
    try:
        fi = open(cf, 'r')
        config = json.load(fi)
        fi.close()
        return config
    except:
        print 'failed to load config from file'
        traceback.print_exc()
        return None

class PageContext:
    def __init__(self, config):
        paramNameList = config['params'].split(',')
        self._params = {}
        for paramName in paramNameList:
            if not config.has_key(paramName):
                print 'lack of parameter: %s for PageContext' % paramName
                raise 'Bad_Config'
            self._params[paramName] = config[paramName]
        self._urlFile = config['url_file']
        self._dataPath = config['data_path']
        fields = config['round_interval'].split('-')
        self._roundInterval = config['round_interval']
        self._startRound = fields[0]
        self._endRound = fields[1]
        self._pages = []
        for k,v in config['pages'].items():
            self._pages.append(v)
    def yieldRound(self):
        fi = open(self._params['url_file'], 'r')
        line = fi.readline().strip()
        while len(line) > 2:
            fs = line.split('\t')
            if len(fs) < 3:
                line = fi.readline().strip()
                continue
            betid = fs[0]
            if betid[:7] < self._startRound or betid[:7] > self._endRound:
                line = fi.readline().strip()
                continue
            url = fs[2]
            print 'yield round: %s, url: %s' % (betid, url)
            yield (betid, url)
            line = fi.readline().strip()
        fi.close()
        return
    def dealPages(self, betid, url):
        for page in self._pages:
            print '-start process page config: %s' % page['page_config']
            confFile = page['page_config']
            pageConfig = LoadConfig(confFile)
            pageConfig['betid'] = betid
            if page.has_key('url_change'):
                fields = page['url_change'].strip().split('>>')
                pageConfig['url'] = url.replace(fields[0], fields[1])
            else:
                pageConfig['url'] = url
            pp = PageProcessor(pageConfig)
            windowPages = pp.process()
            while len(windowPages) > 0:
                wpp = windowPages.pop(0)
                windowPages.extend(wpp.process())
        return
    def moveData(self):
        for page in self._pages:
            dfs = page['data_files'].strip().split(',')
            for df in dfs:
                newName = self._dataPath + df + '.%s' % self._roundInterval
                if os.path.exists(df):
                    shutil.move(df, newName)
    def process(self):
        dealPageNum = 0
        for betid, url in self.yieldRound():
            self.dealPages(betid, url)
            dealPageNum += 1
            if dealPageNum > 0 and dealPageNum % 14 == 0:
                print 'close browser when dealPageNum=%d' % dealPageNum
                BrowserManager.closeBrowser()
        #move data at current directory to destination directory
        self.moveData()

