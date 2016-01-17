#/usr/bin/env python
#coding=utf-8

import json
from bs4 import BeautifulSoup
import re
import mechanize
import sys, getopt
import traceback
import time
import random

class PageDealer:
    def __init__(self, config, request={}):
        self._url = config['url']
        #output path & mode can be multiples
        #and seprated by '|'
        self._mode = config['output_mode']
        self._path = config['output_path']
        self._roundInterval = config['round_interval']
        self._charset = config['charset']
        self._round = config['round']
        self._request = request
        print 'init page dealer for round: %s, request: %s' \
                % (self._round, self._request)
    def __del__(self):
        return
    #find table from page
    #request is dict of key-value.
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
        if len(self._request) == 0:
            tables = page.find_all('table')
        else:
            tables = page.find_all('table', self._request)
        return tables
    #parse table
    def parse(self, tables):
        #return new need processed page dealers
        return []


