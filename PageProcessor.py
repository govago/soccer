#/usr/bin/env python
#coding=utf-8

import json
from bs4 import BeautifulSoup
import re
#import mechanize
import sys, getopt
import traceback
import time
import random
from splinter import Browser
import traceback

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

def BrowserManager:
    browserMap = {}
    @staticmethod
    def getBrowser(browserName):
        if browserMap.has_key(browserName):
            return browserMap[browserName]
        else:
            br = Browser('firefox')
            browserMap[browserName] = br
            return br

class PageProcessor:
    def __init__(self, config):
        paramNameList = config['params'].split(',')
        self._params = {}
        for paramName in paramNameList:
            if not config.has_key(paramName):
                print 'lack of parameter: %s for PageProcsor' % paramName
                raise 'Bad_Config'
            self._params[paramName] = config[paramName]
        #get browser
        self._br = BrowserManager.getBrowser(config['browser'])
        #init base if needed.
        if config.has_key('base'):
            self._base = config['base']
        #init tables if needed.
        if config.has_key('tables'):
            self._tables = []
            for tbName, tbConfig in config['tables'].items():
                print 'get config of table: %s.' % tbName
                self._tables.append(tbConfig)
        if config.has_key('windows'):
            self._windows = config['windows']
        if config.has_key('url_prefix'):
            self._urlPrefix = config['url_prefix']
        try:
            self._failRecord = open(config['fail_record'], 'a+')
        except:
            print 'failed to open fail record file.'
            traceback.print_exc()
            raise 'Bad_Config'
    def __del__(self):
        self._failRecord.close()
        return
    def __paramString(self):
        ret = ''
        for k,v in self._params.items():
            ret += '%s,' % v
        return ret.strip(',')
    def dealLoad(self):
        url = self._params['url']
        if self._urlPrefix != None:
            url = self._urlPrefix + self._params['url']
        self._br.visit(url)
        success = False
        try:
            self._br.visit(url)
            retryTimes = 0
            while not self._br.status_code.is_success():
                time.sleep(random.randint(20,60))
                self._br.reload()
                retryTimes += 1
                if retryTimes > 5:
                    break
            if self._br.status_code.is_success():
                success = True
            if retryTimes > 0:
                print 'reload url %d times.' % retryTimes
        except:
            print 'Failed to visit: %s' % url
            time.sleep(90)
        if not success:
            self._failRecord.write('%s\t%s\n' % \
                    (self.__paramString(), url))
    #deal with base information
    def dealBase(self):
        fo = None
        try:
            fo = open(self._base['output_file'], self._base['output_mode'])
        except:
            print 'failed open page Base Info data file'
            traceback.print_exc()
            raise 'Bad_Config'
        header = []
        vals = []
        for k,v in self._base.items():
            if k == 'output_file' or k == 'output_mode':
                continue
            header.append(k)
            if v.startswith('@P@'):
                vals.append(self._params[v[3:]])
            elif v.startswith('@XPATH@'):
                valEle = self._br.find_by_xpath(v[7:]).first
                val = valEle.text.replace('\n', '')
                val = val.replace('\t', ' ')
                vals.append(val)
            else:
                vals.append('None')
        if os.path.getsize(self._base['output_file']) < 11:
            fo.write('%s\n' % '\t'.join(header))
        fo.write('%s\n' % '\t'.join(vals))
        if None != fo:
            fo.close()
        return
    #deal with windows, generate new page processor
    def __dealWindow(self, tbConfig):
        if not tbConfig.has_key('window'):
            return

    #deal with table information
    def dealTable(self, tbConfig):
        fo = None
        try:
            fo = open(tbConfig['output_file'], tbConfig['output_mode'])
            if os.path.getsize(tbConfig['output_file']) < 11:
                if tbConfig.has_key('common_header'):
                    fo.write('%s\t%s\n' % (tbConfig['header'], \
                    tbConfig['common_header']))
                else:
                    fo.write('%s\n' % tbConfig['header'])
        except:
            print 'failed open page Base Info data file'
            traceback.print_exc()
            raise 'Bad_Config'
        #deal with prepare operation
        if tbConfig.has_key('prepare_op') and tbConfig.has_key('prepare_xpath'):
            if tbConfig['prepare_op'] == 'click':
                self._br.find_by_xpath(tbConfig['prepare_xpath']).first.click()
        #deal with common columns
        commonInfo = None
        if tbConfig.has_key('common_header') and tbConfig.has_key('common_xpath'):
            commonEle = self._br.find_by_xpath(tbConfig['common_xpath']).first
            commonInfo = commonEle.text.replace('\n', '').replace('\t', ' ')
            commonInfo += '\t'
        #deal with id columns
        idInfo = ''
        if tbConfig.has_key('id_columns'):
            ids = id_columns.strip().split(',')
            for idStr in ids:
                if idStr.startswith('@P@'):
                    idInfo += '%s\t' % self._params[idStr[3:]]
                elif idStr.startswith('@XPATH@'):
                    ele = self._br.find_by_xpath(idStr[7:]).first
                    val = ele.text.replace('\n', '').replace('\t', ' ')
                    idInfo += '%s\t' % val
                else:
                    idInfo += '%s\t' % idStr
        #deal with columns 
        tbEle = self._br.find_by_xpath(tbConfig['xpath']).first
        table = BeautifulSoup(tbEle.outer_html, 'html5lib')
        trs = table.find_all('tr')
        startIdx = 0
        endIdx = -1
        columnIdxList = []
        for columnIdx in tbConfig['columns'].strip().split(','):
            columnIdxList.append(int(columnIdx))
        if tbConfig.has_key('skip_prefix'):
            startIdx = int(tbConfig['skip_prefix'])
        if tbConfig.has_key('skip_suffix'):
            endIdx = int(tbConfig['skip_suffix'])
        if endIdx <= 0:
            for tr in trs[startIdx:]:
                columnInfo = ''
                tds = tr.find_all('td')
                for idx in columnIdxList:
                    columnInfo += unicode(tds[idx].text) + '\t'
                oneLine = (idInfo+columnInfo+commonInfo).strip('\t')
                fo.write('%s\n' % oneLine)
        else:
            for tr in trs[startIdx:endIdx]:
                columnInfo = ''
                tds = tr.find_all('td')
                for idx in columnIdxList:
                    columnInfo += unicode(tds[idx].text) + '\t'
                oneLine = (idInfo+columnInfo+commonInfo).strip('\t')
                fo.write('%s\n' % oneLine)



