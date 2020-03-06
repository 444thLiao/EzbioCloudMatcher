#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from os.path import *
from WebSeqMatch import EzbioCloudMatch, LogIn
from glob import glob
from Bio import SeqIO
from tqdm import tqdm 
import pandas as pd

def RetrieveAllSeqFiles(folder):
    if isfile(folder):
        files = [folder]
    elif isdir(folder):
        files = glob(join(folder,'*.fasta'))
    return files

def RetrieveAllSeq(seqFiles):
    seqs = [r 
            for _ in seqFiles 
            for r in SeqIO.parse(_,format='fasta')]
    return seqs

def AddMatchToCSV(name, seqMatch, file):
    if not exists(file):
        f = open(file,'w')
        f.write('\t'.join(['sequence ID',
                     'taxon_name',
                     'strain_name',
                     'accession',
                     'similarity',
                     'diffTotalNt',
                     'hitTaxonomy',
                     'completeness']) + '\n')
    else:
        f = open(file, 'a')
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

        text = '\t'.join(list(map(str,(name, hitTaxonName, hitStrainName, accession
        , similarity, diffTotalNt, hitTaxonomy, completeness))))
        f.write(text+'\n')
        f.flush()
    f.close()
def Run():
    # 获取序列
    if len(sys.argv) < 4:
        print(r'please input the username, password and the folder name containing sequence files(*.txt)')
        return -1
    # username = sys.argv[1]
    # password = sys.argv[2]
    seqFolder = sys.argv[1] # 文件夹中包含很多txt文件，每个txt文件为一个基于序列
    username = '1155136557@link.cuhk.edu.hk'
    password = '12345678'
    #seqFolder = '/home-user/thliao/data/jjtao_20191113/16S.fasta'
    seqFiles = RetrieveAllSeqFiles(seqFolder) # 所有带有序列的文件
    seqs = RetrieveAllSeq(seqFiles) # 获取到所有序列
    
    # 开始
    if not '/' in seqFolder:
        seqFolder = './' + seqFolder
    odir = dirname(abspath(seqFolder))
    outputFile = join(odir, r'matchResults.csv')
    outputFile2 = join(odir, r'filtered_matchResults.csv')
    # if os.path.exists(outputFile):
    #     os.remove(outputFile) # 在每次的运行前删除该文件

    # 登录账户    
    match = LogIn(username=username, password=password) # 在此处输入网站的用户名及密码
    if not match:
        print(r'fail to log in the EzbioCloud.net')
        return -1

    # 开始匹配
    matchResult = None
    for seq in tqdm(seqs):        
        RETRY = 0
        while matchResult is None:
            matchResult = match.MatchSeq(name=seq.id, seq=str(seq.seq))
            if RETRY >= 5 and matchResult is None:
                tqdm.write('failed %s' % seq.id)
                break
            if matchResult is None:
                RETRY+=1
                continue
            AddMatchToCSV(seq.id, matchResult, outputFile)
        matchResult = None
    print(r'all annotations done')
    
    df = pd.read_csv(outputFile,sep='\t')
    top_df = df.groupby('sequence ID').head(1)
    seq2tax = dict(zip(top_df.iloc[:,0],
                       [_.split(';;')[-2].split(';')[0] for _ in top_df.loc[:,'hitTaxonomy']] ))
    # dict which is mapping sequence name of 16S to a genus level taxonomys
    genomes = set([_.split('_')[0] for _ in top_df.iloc[:,0]])
    genome2seq = {g:[_ for _ in top_df.iloc[:,0] if _.split('_')[0] == g] for g in genomes}
    multi_genome = [g for g,v in genome2seq.items() if len(v)>1]
    sub_seq2tax = {g:[tax for seq,tax in seq2tax.items() if seq.split('_')[0] == g] for g in multi_genome }
    
    same_genome = [g for g,v in sub_seq2tax.items() if len(set(v))==1]
    diff_genome = [g for g,v in sub_seq2tax.items() if len(set(v))>1]
    
    drop_seq = [seq for seq in seq2tax if seq.split('_')[0] in diff_genome]
    drop_seq += [[seq for seq in seq2tax if seq.split('_')[0] == g][0] for g in same_genome]
    
    print(f"detect {len(same_genome+diff_genome)} genomes with multiple 16S")
    print(f"Only {len(diff_genome)} genomes with different annotated 16S(in genera level)... And they might be polluted and will be filterout ")
    print(f"Left {len(same_genome)} genomes have multiple but same annotation, multiple 16S would be random retained one of them")
    print(f"Final filtered annotation table would output with name '{outputFile2}'")
    sub_df = df.loc[~df.iloc[:,0].isin(drop_seq),:]
    sub_df.to_csv(outputFile2,index=False,sep='\t')
    
    
if __name__ == '__main__':
    Run()
