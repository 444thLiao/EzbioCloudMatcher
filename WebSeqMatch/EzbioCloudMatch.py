# -*- coding: utf-8 -*-

import requests
import json
from urllib.parse import urlparse
import re
import time

HOST = r'www.ezbiocloud.net'
ACCEPT_LANGUAGE = r'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2'
ACCEPT_ENCODING = r'gzip, deflate, br'
REFERER = r'https://www.ezbiocloud.net/identify'        
X_REQUESTED_WITH = r'XMLHttpRequest'
CONNECTION = r'keep-alive'
X_CL_USER_UID = r'35460'
COOKIE = r'_ga=GA1.2.1740934173.1535733637; userEmail=734851667%40qq.com; JSESSIONID=71985069B33310B43E60143047F9876E; _gid=GA1.2.1010954890.1535863506; ezbiocode=tCz%2FGaUbIQdFqReu8YQMt0K2pTcuEaGFk6OdRuFkP%2FE%3D; ezbiocode=tCz%2FGaUbIQdFqReu8YQMt0K2pTcuEaGFk6OdRuFkP%2FE%3D; AWSELB=635129310C4081566E44A10765D042FA56566D15A6ADB7B1860DA85A2A5CAA9D9AA0A47494E0586EBEBE4B5E1D2B779ACD4E675C76EEE0F7DC2D5BEB70B34F6D09BD6D3461; _gat=1'


class EzbioCloudMatch:
    def __init__(self, userEmail=''):
        self.__userEmail = userEmail

    def MatchSeq(self, name, seq):
        '''封装函数，主要的对外接口，其他函数用于'''
        # 提交序列
        id = self.CommitSeq(name, seq)
        if not id:
            return None
        # 查询序列完成的strainUid
        time.sleep(3) # 等待提交的匹配完成
        strainUid = None
        count = 0
        for i in range(10): # 多次循环以等待完成
            strainUid = self.GetStrainID(id)
            if strainUid:
                break
            else:
                time.sleep(3)
                count += 1
            if count >= 10:
                return None            
        return self.GetMatchResults(strainUid)
    
    def CommitSeq(self, name, seq):
        '''提交一次序列对比，该函数正常完成后，web应用中既已得到结果。该函数返回本次工作提交的工作id-GetStrainID(id)的输入参数'''
        headers = {
            'Host': HOST,
            # 'User-Agent': r'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0',
            'Accept': r'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': ACCEPT_LANGUAGE,
            'Accept-Encoding': ACCEPT_ENCODING,
            'Referer': REFERER,
            'Content-Type': r'application/x-www-form-urlencoded; charset=UTF-8',
            'x-cl-userUId': X_CL_USER_UID,
            'X-Requested-With': X_REQUESTED_WITH,
            # 'Content-Length': r'888',
            'Cookie': COOKIE,
            'Connection': CONNECTION
        }

        data = r'jsonStr=%7B%22strain_name%22%3A%22' + name
        data = data + r'%22%2C%22ssurrn_seq%22%3A%22'
        data = data + seq
        data = data + r'%22%7D'    
        request = requests.post(r'https://www.ezbiocloud.net/cl16s/submit_identify_data', headers=headers, data=data)
        if request.status_code != 201:
            return None
        jsonStr = None
        try:
            jsonStr = json.loads(request.text)
        except:
            pass
        if not jsonStr:
            return None
        id = jsonStr.get('sge_job_id')
        if not id:
            return None
        return int(id)

    def GetStrainID(self, id):
        '''将CommitSeq(name, seq)返回的工作id转换为strainID-通过该值获取到本次对比的详细结果'''
        headers={
            'Host': HOST,
            # 'User-Agent': r'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0',
            'Accept': r'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': ACCEPT_LANGUAGE,
            'Accept-Encoding': ACCEPT_ENCODING,
            'Referer': REFERER,
            'x-cl-userUId': X_CL_USER_UID,
            'X-Requested-With': X_REQUESTED_WITH,
            'Cookie': COOKIE,
            'Connection': CONNECTION
        }
        request = requests.get(r'https://www.ezbiocloud.net/cl16s/poll_job_status_multi?jobs=%s' % (id), headers=headers)
        if request.status_code != 200:
            return None
        jsonStr = None
        try:
            jsonStr = json.loads(request.text)
        except:
            pass
        if not jsonStr:
            return None
        strainUid = jsonStr.get('jobs') # 此时jobUid为一个数组
        if not strainUid or len(strainUid) < 1:
            return None
        strainUid = strainUid[0].get('doneData') # 
        if not strainUid:
            return None
        strainUid = strainUid.get('strain_uid')
        if not strainUid:
            return None
        return strainUid

    def GetMatchResults(self, strainID):
        '''通过GetStrainID(id)返回的strainID获取到匹配的详细结果, 最终返回由json转化来的dict'''
        headers={
            'Host': HOST,
            # 'User-Agent': r'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0',
            'Accept': r'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': ACCEPT_LANGUAGE,
            'Accept-Encoding': ACCEPT_ENCODING,
            'Referer': REFERER,
            'x-cl-userUId': X_CL_USER_UID,
            'X-Requested-With': X_REQUESTED_WITH,
            'Cookie': COOKIE,
            'Connection': CONNECTION
        }
        request = requests.get(r'https://www.ezbiocloud.net/identify/result?id=%s' % (strainID), headers=headers)
        if request.status_code != 200:
            return None
        html = request.text # 自此获取到返回的html页面，内部的js代码中带有json数据以表示所有的匹配结果
        # 开始提取json数据
        try:
            # jsonStr = re.search(r'idResult.init\((.+)\);\r\r\n</script>\t\r\r\n\t\r\r\n</body>\r\r\n</html>$', html).group(1)
            jsonStr = re.search(r'<script type="text/javascript">\s*\$\(function\(\) \{\s+idResult.init\((.+)\);\s*\}\);\s*</script>\s*</body>\s*</html>', html).group(1)
        except:
            return None
        results = json.loads(jsonStr)
        return results.get('hits')

if __name__ == '__main__':
    match = EzbioloudMatch('sss')
    res = match.MatchSeq(name='text25', seq=__seq)
    print(res)