#!/usr/bin/env python
#coding=utf-8

import sys
import os

outputFile = 'BetIdMatchId'
inputPattern = 'sina.bet.europe.follows.'
workDir = '/home/soccer/data/' 

def FetchFromFile(fi, fo):
    for l in fi.readlines():
        fs = l.strip().split('\t')
        bid = fs[0]
        try:
            idx = fs[1].index('m_id=')
        except:
            print 'can\'t get match_id for bet_id=%s' % bid
            print 'since url=%s' % fs[1]
            continue
        mid = fs[1][idx+5:]
        fo.write('%s\t%s\n' % (bid,mid))


if __name__ == '__main__':
    files = os.listdir(workDir)
    fo = open(workDir+outputFile, 'w')
    for f in files:
        if f.startswith(inputPattern):
            fi = open(workDir+f, 'r')
            print 'deal with: %s' % f
            FetchFromFile(fi, fo)
            fi.close()
    fo.close()

