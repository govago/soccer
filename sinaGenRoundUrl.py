#!/usr/bin/env python
#coding=utf-8

import sys, getopt
import traceback
import time
import random
import traceback
import os

betidMatchidFile = '.\\data\\BetIdMatchId'
urlPrefix = 'http://odds.sports.sina.com.cn/liveodds/marker_list_old.php?m_id='
retFile = '.\\data\\sina_op_info.dat'
minRound = 2008001
maxRound = 2009058

if __name__ == '__main__':
    fi = open(betidMatchidFile, 'r')
    fo = open(retFile, 'w')
    for line in fi.readlines():
        fs = line.strip().split('\t')
        roundStr = '20' + fs[0].split('-')[0]
        roundId = int(roundStr)
        if roundId < minRound or roundId > maxRound:
            continue
        matchId = fs[1]
        betid = '20' + fs[0]
        fo.write('%s\t%s\n' % (betid, urlPrefix+matchId))
    fi.close()
    fo.close()

