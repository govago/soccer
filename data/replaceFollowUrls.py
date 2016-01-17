#!/usr/bin/env python
#coding=utf-8

import os
import sys, getopt

srcUrl = 'http://odds.sports.sina.com.cn/liveodds/marker_list.php?m_id='
destUrl = 'http://odds.sports.sina.com.cn/?s=liveodds&a=europe&m_id='

if __name__ == '__main__':
    opts,args = getopt.getopt(sys.argv[1:], 'i:o:')
    for op, val in opts:
        if op == '-i':
            inputFile = val.strip()
            print 'get inputFile: %s' % inputFile
        if op == '-o':
            outputFile = val.strip()
            print 'get outputFile: %s' % outputFile
    fi = open(inputFile, 'r')
    fo = open(outputFile, 'w')
    for line in fi.readlines():
        fs = line.strip().split('\t')
        mid = fs[1].split('m_id=')[1]
        fo.write('%s\t%s\n' % \
                (fs[0], destUrl+mid))
    fi.close()
    fo.close()

