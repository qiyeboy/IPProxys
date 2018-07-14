# coding:utf-8
import sys

import chardet
from gevent import monkey
monkey.patch_all()

import json
import os
import gevent
import requests
import time
import psutil
from multiprocessing import Process, Queue

import config
from db.DataStore import sqlhelper
from util.exception import Test_URL_Fail


def detect_from_db(myip, proxy, proxies_set):
    proxy_dict = {'ip': proxy[0], 'port': proxy[1]}
    result = detect_proxy(myip, proxy_dict)
    if result:
        proxy_str = '%s:%s' % (proxy[0], proxy[1])
        proxies_set.add(proxy_str)

    else:
        if proxy[3] < 1:
            sqlhelper.delete({'ip': proxy[0], 'port': proxy[1]})
        else:
            score = proxy[3]-1
            sqlhelper.update({'ip': proxy[0], 'port': proxy[1]}, {'score': score})
            proxy_str = '%s:%s' % (proxy[0], proxy[1])
            proxies_set.add(proxy_str)



def validator(queue1, queue2, myip):
    tasklist = []
    proc_pool = {}     # 所有进程列表
    cntl_q = Queue()   # 控制信息队列
    while True:
        if not cntl_q.empty():
            # 处理已结束的进程
            try:
                pid = cntl_q.get()
                proc = proc_pool.pop(pid)
                proc_ps = psutil.Process(pid)
                proc_ps.kill()
                proc_ps.wait()
            except Exception as e:
                pass
                # print(e)
                # print(" we are unable to kill pid:%s" % (pid))
        try:
            # proxy_dict = {'source':'crawl','data':proxy}
            if len(proc_pool) >= config.MAX_CHECK_PROCESS:
                time.sleep(config.CHECK_WATI_TIME)
                continue
            proxy = queue1.get()
            tasklist.append(proxy)
            if len(tasklist) >= config.MAX_CHECK_CONCURRENT_PER_PROCESS:
                p = Process(target=process_start, args=(tasklist, myip, queue2, cntl_q))
                p.start()
                proc_pool[p.pid] = p
                tasklist = []

        except Exception as e:
            if len(tasklist) > 0:
                p = Process(target=process_start, args=(tasklist, myip, queue2, cntl_q))
                p.start()
                proc_pool[p.pid] = p
                tasklist = []

def process_start(tasks, myip, queue2, cntl):
    spawns = []
    for task in tasks:
        spawns.append(gevent.spawn(detect_proxy, myip, task, queue2))
    gevent.joinall(spawns)
    cntl.put(os.getpid())  # 子进程退出是加入控制队列


def detect_proxy(selfip, proxy, queue2=None):
    '''
    :param proxy: ip字典
    :return:
    '''
    ip = proxy['ip']
    port = proxy['port']
    protocol, types, speed = getattr(sys.modules[__name__],config.CHECK_PROXY['function'])(selfip, ip, port)#checkProxy(selfip, proxies)
    if protocol >= 0:
        proxy['protocol'] = protocol
        proxy['types'] = types
        proxy['speed'] = speed
    else:
        proxy = None
    if queue2:
        queue2.put(proxy)
    return proxy


def checkProxy(selfip, ip, port):
    '''
    用来检测代理的类型，突然发现，免费网站写的信息不靠谱，还是要自己检测代理的类型
    :param
    :return:
    '''
    protocol = -1
    types = -1
    speed = -1
    proxies = {"http": "http://%s:%s" % (ip, port), "https": "http://%s:%s" % (ip, port)}
    http, http_types, http_speed = _checkHttpProxy(selfip, proxies)
    https, https_types, https_speed = _checkHttpProxy(selfip, proxies, False)
    if http and https:
        protocol = 2
        types = http_types
        speed = http_speed
    elif http:
        types = http_types
        protocol = 0
        speed = http_speed
    elif https:
        types = https_types
        protocol = 1
        speed = https_speed
    else:
        proxies = {"http": "socks5://%s:%s" % (ip, port), "https": "socks5://%s:%s" % (ip, port)}
        socks5, socks5_types, socks5_speed = _checkHttpProxy(selfip, proxies)
        if socks5:
            types = socks5_types
            protocol = 4
            speed = socks5_speed
        else:
            proxies = {"http": "socks4://%s:%s" % (ip, port), "https": "socks4://%s:%s" % (ip, port)}
            socks4, socks4_types, socks4_speed = _checkHttpProxy(selfip, proxies)
            if socks4:
                types = socks4_types
                protocol = 3
                speed = socks4_speed
            else:
                types = -1
                protocol = -1
                speed = -1
    return protocol, types, speed


def _checkHttpProxy(selfip, proxies, isHttp=True):
    types = -1
    speed = -1
    if isHttp:
        test_url = config.TEST_HTTP_HEADER
    else:
        test_url = config.TEST_HTTPS_HEADER
    try:
        start = time.time()
        r = requests.get(url=test_url, headers=config.get_header(), timeout=config.TIMEOUT, proxies=proxies)
        if r.ok:
            speed = round(time.time() - start, 2)
            content = json.loads(r.text)
            headers = content['headers']
            ip = content['origin']
            proxy_connection = headers.get('Proxy-Connection', None)
            if ',' in ip:
                types = 2
            elif proxy_connection:
                types = 1
            else:
                types = 0

            return True, types, speed
        else:
            return False, types, speed
    except Exception as e:
        return False, types, speed


def baidu_check(selfip, proxies):
    '''
    用来检测代理的类型，突然发现，免费网站写的信息不靠谱，还是要自己检测代理的类型
    :param
    :return:
    '''
    protocol = -1
    types = -1
    speed = -1
    # try:
    #     #http://ip.chinaz.com/getip.aspx挺稳定，可以用来检测ip
    #     r = requests.get(url=config.TEST_URL, headers=config.get_header(), timeout=config.TIMEOUT,
    #                      proxies=proxies)
    #     r.encoding = chardet.detect(r.content)['encoding']
    #     if r.ok:
    #         if r.text.find(selfip)>0:
    #             return protocol, types, speed
    #     else:
    #         return protocol,types,speed
    #
    #
    # except Exception as e:
    #     return protocol, types, speed
    try:
        start = time.time()
        r = requests.get(url='https://www.baidu.com', headers=config.get_header(), timeout=config.TIMEOUT, proxies=proxies)
        r.encoding = chardet.detect(r.content)['encoding']
        if r.ok:
            speed = round(time.time() - start, 2)
            protocol= 0
            types=0

        else:
            speed = -1
            protocol= -1
            types=-1
    except Exception as e:
            speed = -1
            protocol = -1
            types = -1
    return protocol, types, speed

def getMyIP():
    try:
        r = requests.get(url=config.TEST_IP, headers=config.get_header(), timeout=config.TIMEOUT)
        ip = json.loads(r.text)
        return ip['origin']
    except Exception as e:
        raise Test_URL_Fail


if __name__ == '__main__':
    ip = '222.186.161.132'
    port = 3128
    proxies = {"http": "http://%s:%s" % (ip, port), "https": "http://%s:%s" % (ip, port)}
    _checkHttpProxy(None,proxies)
    # getMyIP()
    # str="{ip:'61.150.43.121',address:'陕西省西安市 西安电子科技大学'}"
    # j = json.dumps(str)
    # str = j['ip']
    # print str
