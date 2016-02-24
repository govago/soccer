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
import os

from PageContext import PageContext
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


if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], 'c:')
    for op, value in opts:
        if op == '-c':
            configFile = value.strip()
            print 'get config file: %s' % configFile
    config = LoadConfig(configFile)
    if None == config:
        print 'load config failed. exit'
        sys.exit(-1)
    pc = PageContext(config)
    pc.process()

    BrowserManager.closeBrowser()
    shutdownStr = 'shutdown.exe -f -s -t %s' % int(10)
    print shutdownStr
    os.system( shutdownStr )
    
