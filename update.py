# -*- coding: utf8 -*-
# Copyright (c) 2018 - githubxp
# Usage: python update.py subdomain.yourdomain.suffix

import sys
import json
import ipaddress
import logging
import tldextract
import requests
from logging.handlers import RotatingFileHandler
from aliyunsdkcore.client import AcsClient
from aliyunsdkalidns.request.v20150109 import DescribeDomainRecordsRequest, UpdateDomainRecordRequest


# AcsClient
client = AcsClient(
   "access id",
   "access secret",
   "region_id"
)

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('/var/log/alidns.log', maxBytes=10485760, backupCount=5, encoding='UTF-8')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# Acquire main domain info
def get_sub_domain_info(sd, md):
    request = DescribeDomainRecordsRequest.DescribeDomainRecordsRequest()
    request.set_DomainName(md)
    try:
        response = client.do_action_with_exception(request)
        result = json.loads(response)
    except Exception as e:
        # print(e)
        logger.info('Acquire main domain failed[EXIT]:' + str(e))
        sys.exit(1)
    # print(result['DomainRecords']['Record'])
    # ['RecordId']['RR']['Type']['Line']['Value']['TTL']['Status']
    # 0000001 sub_domain A default xxx.xxx.xxx.xx 600 ENABLE
    try:
        for domain_list in result['DomainRecords']['Record']:
            if sd == domain_list['RR']:
                return domain_list['RecordId'], domain_list['Value']
        raise Exception('no sub domain')
    except Exception as e:
        logger.info('Sub domain error[EXIT]:' + str(e))
        sys.exit(1)


# Update sub domain
def update_rr(record_id, sd, ip):
    request = UpdateDomainRecordRequest.UpdateDomainRecordRequest()
    request.set_RecordId(record_id)
    request.set_RR(sd)
    request.set_Type('A')
    request.set_Value(ip)
    request.set_TTL('600')
    try:
        client.do_action_with_exception(request)
        logger.info('Update:' + sd + ', IP:' + ip + ', accomplished[DONE]:')
    except Exception as e:
        # print(e)
        logger.info('Update sub domain failed[EXIT]:' + str(e))
        sys.exit(1)


# Update sub domain entrance
def update_sub_domain(sd, md):
    sub_domain_id, record_ip = get_sub_domain_info(sd, md)
    my_ip = get_my_ip()
    try:
        ip_check = ipaddress.ip_address(my_ip).is_global
    except Exception as e:
        # print(e)
        logger.info('check ip failed[EXIT]:' + str(e))
        sys.exit(1)

    if sub_domain_id and ip_check and record_ip != my_ip:
        update_rr(sub_domain_id, sd, my_ip)
    else:
        # logger.info('pass[EXIT]:')
        pass


# Acquire new ip
def get_my_ip():
    url = "http://ip.taobao.com/service/getIpInfo2.php?ip=myip"
    try:
        response = requests.get(url)
        res = json.loads(response.text)
        return res['data']['ip']
    except Exception as e:
        # print(e)
        logger.info('Acquire new ip failed[EXIT]:' + str(e))
        sys.exit(1)


if __name__ == '__main__':
    DomainName = sys.argv
    try:
        tld_res = tldextract.extract(DomainName[1])
    except Exception as e:
        logger.info('Parameters error[EXIT]:' + str(e))
        sys.exit(1)
    sub_domain = tld_res.subdomain
    main_domain = "%s.%s" % (tld_res.domain, tld_res.suffix)
    if sub_domain == "" or main_domain == "":
        pass
    else:
        update_sub_domain(sub_domain, main_domain)
