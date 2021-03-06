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
        self._urlFileFields = int(config['url_file_fields'])
        self._urlBetidIdx = int(config['url_file_betid_idx'])
        self._urlUrlIdx = int(config['url_file_url_idx'])
        self._pages = []
        for k,v in config['pages'].items():
            self._pages.append(v)
    def yieldRound(self):
        fi = open(self._params['url_file'], 'r')
        line = fi.readline().strip()
        while len(line) > 2:
            if line.startswith('#'):
                line = fi.readline().strip()
                continue
            fs = line.split('\t')
            if len(fs) < self._urlFileFields:
                line = fi.readline().strip()
                continue
            betid = fs[self._urlBetidIdx]
            if betid[:7] < self._startRound or betid[:7] > self._endRound:
                line = fi.readline().strip()
                continue
            url = fs[self._urlUrlIdx]
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
    def removeData(self):
        for page in self._pages:
            dfs = page['data_files'].strip().split(',')
            for df in dfs:
                if os.path.exists(df):
                    os.remove(df)
    def moveData(self):
        for page in self._pages:
            dfs = page['data_files'].strip().split(',')
            for df in dfs:
                newName = self._dataPath + df + '.%s' % self._roundInterval
                if os.path.exists(df):
                    sdf = str(df)
                    snewName= str(newName)
                    shutil.copy(sdf, snewName)
    def moveDataWithExcept(self, curBetid):
        roundInterval = self._roundInterval
        startRound = int(roundInterval.split('-')[0])
        curRound = int(curBetid.split('-')[0])
        curRound = curRound - 1
        if curRound < startRound:
            return
        for page in self._pages:
            dfs = page['data_files'].strip().split(',')
            for df in dfs:
                newName = self._dataPath + df + '.%d-%d' % (startRound, curRound)
                if os.path.exists(df):
                    sdf = str(df)
                    snewName= str(newName)
                    shutil.copy(sdf, snewName)
        return
    def process(self):
        dealPageNum = 0
        curBetid = None
        try:
            self.removeData()
            for betid, url in self.yieldRound():
                curBetid = betid
                self.dealPages(betid, url)
                dealPageNum += 1
                if dealPageNum > 0 and dealPageNum % 14 == 0:
                    print 'close browser when dealPageNum=%d' % dealPageNum
                    BrowserManager.closeBrowser()
            #move data at current directory to destination directory
            self.moveData()
        except:
            traceback.print_exc()
            self.moveDataWithExcept(curBetid)

