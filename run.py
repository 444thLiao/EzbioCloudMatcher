#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from os.path import *
from WebSeqMatch import EzbioCloudMatch, LogIn
from WebSeqMatch import Sequence
from glob import glob
from Bio import SeqIO
from tqdm import tqdm 


def RetrieveAllSeqFiles(folder):
    files = glob(join(folder,'*.fasta'))
    return files

def RetrieveAllSeq(seqFiles):
    seqs = [r 
            for _ in seqFiles 
            for r in SeqIO.parse(_,format='fasta')]
    return seqs

def AddMatchToCSV(name, seqMatch, file):
    with open(file, 'a') as f:
        for item in seqMatch:
            hitTaxonName = item['taxon_name']
            hitStrainName = item['strain_name'] # 
            accession = item['accession']
            similarity = r'%.2f' % (item['similarity']*100.0)
            diffTotalNt = str(item['n_mismatch']) + '/' + str(item['n_compared'])
            hitTaxonomy = item['taxonomy']
            completeness = None
            if item['completeness'] == 0:
                completeness = 'N/A'
            else:
                completeness = r'%.1f' % (item['completeness'] * 100.0)

            text = '%s,%s,%s,%s,%s,%s,%s,%s\n' % (name, hitTaxonName, hitStrainName, accession
            , similarity, diffTotalNt, hitTaxonomy, completeness)
            f.write(text)
        f.write('\n\n')

def Run():
    # 获取序列
    if len(sys.argv) < 4:
        print(r'please input the username, password and the folder name containing sequence files(*.txt)')
        return -1
    username = sys.argv[1]
    password = sys.argv[2]
    seqFolder = sys.argv[3] # 文件夹中包含很多txt文件，每个txt文件为一个基于序列

    "1155136557@link.cuhk.edu.hk" "bioliaoth" "seq"
    
    seqFiles = RetrieveAllSeqFiles(seqFolder) # 所有带有序列的文件
    seqs = RetrieveAllSeq(seqFiles) # 获取到所有序列
    
    # 开始
    outputFile = r'.\matchResults.csv' # sys.argv[2]
    if os.path.exists(outputFile):
        os.remove(outputFile) # 在每次的运行前删除该文件

    # 登录账户    
    match = LogIn(username=username, password=password) # 在此处输入网站的用户名及密码
    if not match:
        print(r'fail to log in the EzbioCloud.net')
        return -1

    # 开始匹配
    for seq in tqdm(seqs):        
        matchResult = match.MatchSeq(name=seq.id, seq=str(seq.seq))
        if matchResult:
            AddMatchToCSV(seq.id, matchResult, outputFile)
        else:
            tqdm.write('failed %s' % seq.id)
    print(r'已执行完毕')

if __name__ == '__main__':
    Run()
