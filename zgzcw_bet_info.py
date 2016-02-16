#!/usr/bin/env python
#coding=utf-8

'''
get bet information from www.zgzcw.com
'''
import json
from bs4 import BeautifulSoup
import re
import mechanize
import sys, getopt
import traceback
import time
import random
import pdb
from splinter import Browser

reload(sys)
sys.setdefaultencoding('utf-8')

url = 'http://saishi.zgzcw.com/html/310xingxiang.html/'
output = 'data/zgzcw_bet_info.dat'

if __name__ == '__main__':

    br = Browser('firefox')
    br.visit(url)
    time.sleep(3)
    tableElement = br.find_by_xpath('//*[@id="zcxxt"]').first
    tableHtml = '<table>' + tableElement.html + '</table>'
    table = BeautifulSoup(tableHtml, 'html5lib')
    tbody = table.find('tbody')
    trs = tbody.find_all('tr')
    print 'table lines: %d' % len(trs)

    fo = open(output, 'w')
    line = 0
    try:
        for tr in trs:
            line += 1
            tds = tr.find_all('td')
            betNum = unicode(tds[0].text)
            if betNum < '2008001':
                continue
            print 'start process... from line: %d' % line
            if line%20 == 0:
                print 'process line: %d, betNum: %s' % (line, betNum)
            for i in range(1,15):
                betid = betNum + '-%d' % i
                result = unicode(tds[i].text)
                url = tds[i].find('a')['href']
                fo.write('%s\t%s\t%s\n' % (betid, result, url))
    except:
        pdb.set_trace()
    fo.close()
    br.windows.current.close()


