#/usr/bin/env python
#coding=utf-8

import json
from bs4 import BeautifulSoup
import re
import os
#import mechanize
import sys, getopt
import traceback
import time
import random
from splinter import Browser
import traceback
from urllib import unquote
import pdb
import copy

reload(sys)
sys.setdefaultencoding('utf-8')

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

class BrowserManager:
    browserMap = {}
    @staticmethod
    def getBrowser(browserName):
        if BrowserManager.browserMap.has_key(browserName):
            return BrowserManager.browserMap[browserName]
        else:
            br = Browser('firefox')
            BrowserManager.browserMap[browserName] = br
            return br
    @staticmethod
    def closeBrowser():
        while len(BrowserManager.browserMap) > 0:
            for k in BrowserManager.browserMap.keys():
                v = BrowserManager.browserMap.pop(k)
                v.quit()
                del v
            

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
        self._base = None
        #init base if needed.
        if config.has_key('base'):
            self._base = config['base']
        #init tables if needed.
        self._tables = None
        if config.has_key('tables'):
            self._tables = []
            for tbName, tbConfig in config['tables'].items():
                print 'get config of table: %s.' % tbName
                self._tables.append(tbConfig)
        self._windows = None
        if config.has_key('windows'):
            self._windows = config['windows']
        self._urlPrefix = None
        self._failRecord = None
        if config.has_key('url_prefix'):
            self._urlPrefix = config['url_prefix']
        try:
            self._failRecord = open(config['fail_record'], 'a+')
        except:
            print 'failed to open fail record file.'
            traceback.print_exc()
            raise 'Bad_Config'
        #list to store window page processor objects.
        self._windowPage = []
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
        print '--load url: %s' % url
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
        if self._base.has_key('column_order'):
            keys = self._base['column_order'].strip().split(',')
            for k in keys:
                v = self._base[k]
                header.append(k)
                if v.startswith('@P@'):
                    vals.append(self._params[v[3:]])
                elif v.startswith('@XPATH@'):
                    valEle = self._br.find_by_xpath(v[7:]).first
                    val = unicode(valEle.text).replace('\n', '')
                    val = val.replace('\t', ' ')
                    vals.append(val)
                else:
                    vals.append('None')
        else:
            for k,v in self._base.items():
                if k == 'output_file' or k == 'output_mode':
                    continue
                header.append(k)
                if v.startswith('@P@'):
                    vals.append(self._params[v[3:]])
                elif v.startswith('@XPATH@'):
                    valEle = self._br.find_by_xpath(v[7:]).first
                    val = unicode(valEle.text).replace('\n', '')
                    val = val.replace('\t', ' ')
                    vals.append(val)
                else:
                    vals.append('None')
        try:
            if os.path.getsize(self._base['output_file']) < 11:
                fo.write('%s\n' % '\t'.join(header))
            fo.write('%s\n' % '\t'.join(vals))
        except:
            traceback.print_exc()
            pdb.set_trace()
        finally:
            if None != fo:
                fo.close()
        return
    #deal with windows, generate new page processor
    def __dealWindow(self, tbConfig, bs4Element):
        windowParam = dict(self._windows[tbConfig['window']])
        kvList = tbConfig['window_params'].items()
        if tbConfig.has_key('window_params_order'):
            keys = tbConfig['window_params_order'].strip().split(',')
            del kvList
            kvList = []
            for k in keys:
                kvList.append((k,tbConfig['window_params'][k]))
        for k,v in kvList:
            decodeMode = None
            if v.find('|') != -1:
                contents = v.strip().split('|')
                decodeMode = contents[1]
                v = contents[0]
            if v.startswith('@P@'):
                windowParam[k] = self._params[v[3:]]
            elif v.startswith('__'):
                if v.find('>>') != -1:
                    fields = v.strip('__').split('>>')
                    if fields[1] == 'url_decode':
                        val = unicode(unquote(windowParam[fields[0]]), 'gbk')
                        windowParam[k] = val
                elif v.find('@') != -1:
                    fields = v.strip('__').split('@')
                    assert (fields[1].startswith('[') and \
                            fields[1].endswith(']'))
                    idxStr = fields[1][1:-1].split(':')
                    startStr = idxStr[0]
                    endStr = idxStr[1]
                    if windowParam[fields[0]].find(startStr) == -1:
                        windowParam[k] = 'None'
                        continue
                    startIdx = windowParam[fields[0]].find(startStr) + \
                            len(startStr)
                    endIdx = -1
                    if len(endStr) > 0:
                        endIdx = windowParam[fields[0]].find(endStr)
                    if endIdx > -1:
                        value = windowParam[fields[0]][startIdx:endIdx]
                        windowParam[k] = value
                        if None != decodeMode and decodeMode == 'url_decode':
                            bvalue = bytes(value)
                            windowParam[k] = unicode(unquote(bvalue), 'utf-8')
                    else:
                        value = windowParam[fields[0]][startIdx:]
                        windowParam[k] = value
                        if None != decodeMode and decodeMode == 'url_decode':
                            bvalue = bytes(value)
                            windowParam[k] = unicode(unquote(bvalue), 'utf-8')
            elif v.startswith('@'):
                fields = v.strip('@').split('@')
                key = fields[-1]
                eleStr = fields[0]
                eleIdx = None
                eleName = None
                startIdx = eleStr.find('[')
                endIdx = eleStr.find(']')
                if startIdx != -1 and endIdx != -1:
                    eleIdx = int(eleStr[startIdx+1:endIdx])
                    eleName  = eleStr[:startIdx]
                else:
                    eleName = eleStr
                ele = None
                if None != eleIdx:
                    eles = bs4Element.find_all(eleName)
                    ele = eles[eleIdx]
                else:
                    ele = bs4Element.find(eleName)
                for subEle in fields[1:-1]:
                    ele = ele.find(subEle)
                if key.startswith('.'):
                    eleValStr = 'ele%s' % key
                    windowParam[k] = eval(eleValStr)
                else:
                    windowParam[k] = ele[key]
            else:
                print 'bad param: (%s,%s). when deal with window: %s' % \
                        (k, v, tbConfig['window'])
                traceback.print_exc()
                raise 'Bad_Config'
        return PageProcessor(windowParam)
    #deal with table information
    def dealTable(self, tbConfig):
        print '--process table to: %s' % tbConfig['output_file']
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
        commonInfo = ''
        if tbConfig.has_key('common_header') and tbConfig.has_key('common_xpath'):
            commonEle = self._br.find_by_xpath(tbConfig['common_xpath']).first
            commonInfo = commonEle.text.replace('\n', '').replace('\t', ' ')
            commonInfo += '\t'
        #deal with id columns
        idInfo = ''
        if tbConfig.has_key('id_columns'):
            ids = tbConfig['id_columns'].strip().split(',')
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
            try:
                for tr in trs[startIdx:]:
                    try:
                        if tr['style'] == 'display: none;':
                            continue
                    except:
                        pass
                    columnInfo = ''
                    tds = tr.find_all('td')
                    for idx in columnIdxList:
                        if idx < len(tds):
                            columnInfo += unicode(tds[idx].text) + '\t'
                    oneLine = (idInfo+columnInfo+commonInfo).strip('\t')
                    fo.write('%s\n' % oneLine)
                    if tbConfig.has_key('window') and \
                            tbConfig['window_mode'] == 'tr':
                        self._windowPage.append(self.__dealWindow(tbConfig, tr))
            except:
                traceback.print_exc()
                pdb.set_trace()
        else:
            for tr in trs[startIdx:endIdx]:
                try:
                    if tr['style'] == 'display: none;':
                            continue
                except:
                    pass
                columnInfo = ''
                tds = tr.find_all('td')
                for idx in columnIdxList:
                    if idx < len(tds):
                        columnInfo += unicode(tds[idx].text) + '\t'
                oneLine = (idInfo+columnInfo+commonInfo).strip('\t')
                fo.write('%s\n' % oneLine)
                if tbConfig.has_key('window') and \
                        tbConfig['window_mode'] == 'tr':
                    self._windowPage.append(self.__dealWindow(tbConfig, tr)) 
        #deal with same column rows
        if tbConfig.has_key('same_columns'):
            sameRowIdxs = [int(i) for i in tbConfig['same_row_index'].strip().split(',')]
            sameValues = [i for i in tbConfig['same_columns'].strip().split(',')]
            sameColIdxs = [int(i) for i in tbConfig['same_index'].strip().split(',')]
            for rowIdx in sameRowIdxs:
                tr = trs[rowIdx]
                fillTr = copy.copy(tr)
                try:
                    if tr['style'] == 'display: none;':
                        continue
                except:
                    pass
                columnInfo = ''
                tds = tr.find_all('td')
                for sIdx in sameColIdxs:
                    tds.insert(sIdx, sameValues[sIdx])
                    #insert same values in coulumns of the tr, avoid deal windows
                    #parameters error. keep the same size tr.
                    tdStr = '<table><tr><td>' + sameValues[sIdx] + '</td></tr></table>'
                    fillTd = BeautifulSoup(tdStr, 'html5lib')
                    fillTd = fillTd.find('td')
                    fillTr.insert(sIdx, fillTd)
                for idx in columnIdxList:
                    if idx < len(tds):
                        if idx in sameColIdxs:
                            columnInfo += unicode(tds[idx]) + '\t'
                        else:
                            columnInfo += unicode(tds[idx].text) + '\t'
                oneLine = (idInfo+columnInfo+commonInfo).strip('\t')
                fo.write('%s\n' % oneLine)
                if tbConfig.has_key('window') and \
                        tbConfig['window_mode'] == 'tr':
                    self._windowPage.append(self.__dealWindow(tbConfig, fillTr)) 
        #deal with table level(mode) window
        if tbConfig.has_key('window') and \
                tbConfig['window_mode'] == 'table':
                self._windowPage.append(__dealWindow(tbConfig, table))
        if None != fo:
            fo.close()
        return
    #deal with whole flow
    def process(self):
        self.dealLoad()
        if None != self._base:
            self.dealBase()
        for tbConfig in self._tables:
            self.dealTable(tbConfig)
        return self._windowPage


