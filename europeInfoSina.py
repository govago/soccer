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

from PageClass import PageDealer
class EuropePage(PageDealer):
    columns = '欧赔公司\t欧赔-胜\t欧赔-平\t欧赔-负\t胜率\t和率\t负率\t返还率\t凯利-胜\t凯利-平\t凯利-负\t最新变盘时间'
    def __init__(self, config):
        PageDealer.__init__(self, config)
        self._fo = open(self._path, self._mode)
        if os.path.getsize(self._path) < 10:
            self._fo.write('%s\n' % columns)
    def parse(self, tables):
        print 'start parse table[0] in url: %s' % self._url


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


    tableRequest = {'id':'dongtaiOuPan'}


