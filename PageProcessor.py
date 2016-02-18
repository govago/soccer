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

class PageProcessor:
    def __init__(self, config):
        paramNameList = config['params'].split(',')
        self._params = {}
        for paramName in paramNameList:
            if not config.has_key(paramName):
                print 'lack of parameter: %s for PageProcsor' % paramName
                raise 'Bad_Config'
            self._params[paramName] = config[paramName]
        #init base if needed.
        if config.has_key('base'):
            self._base = config['base']
        #init tables if needed.
        if config.has_key('tables'):
            self._tables = []
            for tbName, tbConfig in config['tables'].items():
                print 'get config of table: %s.' % tbName
                self._tables.append(tbConfig)
    def __del__(self):
        return
    #deal with base information
    def dealBase(self, br):
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
                valEle = br.find_by_xpath(v[7:]).first
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
    #deal with table information
    def dealTable(self, br, tbConfig):
        fo = None
        try:
            fo = open(tbConfig['output_file'], tbConfig['output_mode'])
        except:
            print 'failed open page Base Info data file'
            traceback.print_exc()
            raise 'Bad_Config'
        #deal with common columns
        commonInfo = None
        if tbConfig.has_key('common_header') and tbConfig.has_key('common_xpath'):
            commonEle = br.find_by_xpath(tbConfig['common_xpath']).first
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
                    ele = br.find_by_xpath(idStr[7:]).first
                    val = ele.text.replace('\n', '').replace('\t', ' ')
                    idInfo += '%s\t' % val
                else:
                    idInfo += '%s\t' % idStr
        #deal with columns 
        tbEle = br.find_by_xpath(tbConfig['xpath']).first
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
                oneLine = 
        else:
            for tr in trs[startIdx:endIdx]:



