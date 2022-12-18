from concurrent.futures import process
import re
import os
import json
from urllib import response
import uuid
import time
import subprocess
from joblib import parallel_backend
import pywifi
from django.http import HttpResponse
from threading import Thread
import threading
import websockets
import asyncio


test_string_dict = {}
global flag
flag = 1


class ThreadWithReturnValue(Thread):
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self):
        super().join()
        return self._return



# wifi扫描，返回WiFi名和信号值键值对，是一个字典
def wifi_scan():
    dict = {}
    wifi = pywifi.PyWiFi()
    interface = wifi.interfaces()[0]
    interface.scan()
    # 扫描结果，scan_results()返回一个集，存放的是每个wifi对象
    bss = interface.scan_results()
    wifi_name_set = set()
    for w in bss:
        dict.update({w.ssid.encode('raw_unicode_escape').decode('utf-8'): w.signal})
        wifi_name_and_signal = (w.ssid.encode('raw_unicode_escape').decode('utf-8'), w.signal)
        wifi_name_set.add(wifi_name_and_signal)
    return dict


# 判断是否连接wifi
def isConnectWifi():
    try:
        cmd_output = os.popen('netsh wlan show interface')
        cmd_txt = cmd_output.read()
        state = re.findall('(?:State +: )(\S*)', cmd_txt)
        if state:
            if state[0] == 'connected':
                return True
            elif state[0] == 'disconnected':
                return False
        else:
            raise Exception()
    except Exception as e:
        print('出错，{e}')
        return False


# 获取当前WiFi连接信息， 返回一个字典
def getCurrentWifiInfo():
    try:
        cmd_output = os.popen('netsh wlan show interface')
        cmd_txt = cmd_output.read()
        wifi_info_dict = {}
        ssid = re.findall('(?:SSID +: )(\S*)', cmd_txt)
        bssid = re.findall('(?:BSSID +: )(\S*)', cmd_txt)
        radio_type = re.findall('(?:Radio type +: )(\S*)', cmd_txt)
        signal = re.findall('(?:Signal +: )(\S*)', cmd_txt)
        if ssid:
            wifi_info_dict.update({'ssid': ssid[0]})
        else:
            raise Exception()
        if bssid:
            wifi_info_dict.update({'bssid': bssid[0]})
        else:
            raise Exception
        if radio_type:
            if radio_type[0] == '802.11b':
                wifi_info_dict.update({'radio_type': '2.4GHz'})
            elif radio_type[0] == '802.11ac':
                wifi_info_dict.update({'radio_type': '5GHz'})
            else:
                wifi_info_dict.update({'radio_type': radio_type[0]})
        else:
            raise Exception()
        if signal:
            wifi_info_dict.update({'signal': signal[0]})
        else:
            raise Exception
    except Exception as e:
        print('出错，缺少字段，{e}')
    return wifi_info_dict


# 绑定当前连接的wifi
def associateWifi(req):
    if req.method == 'POST':
        res_dict = getCurrentWifiInfo()
        key_list = list(res_dict.keys())
        if 'ssid' and 'signal' in key_list:
            res = {
                "code": 1,
                "msg": "绑定成功",
                "data":{
                    "current_wifi": res_dict['ssid'],
                    "current_wifi_strength": res_dict['signal']
                }
            }
            return HttpResponse(json.dumps(res))
        else:
            res = {
                "code": 0,
                "msg": "绑定失败",
                "data": ""
            }
            return HttpResponse(json.dumps(res))
    else:
        res = {
            "code": 0,
            "msg": "请求方式为GET请求",
            "data": ""
        }
        return HttpResponse(json.dumps(res))


# iperf3环境监测
def testEnvironment():
    process = subprocess.Popen(
        ["iperf3", "-v"],
        stdout=subprocess.PIPE
    )
    response, _ = process.communicate()
    txt = re.findall('iperf [0-9].+', response.decode('utf-8'))
    if txt:
        return True
    else:
        return False


# 检测server端是否打开
def testServerOpen(ipaddress, port):
    process = subprocess.Popen(
        ["iperf3", "-c", ipaddress, "-p", port, "-t", "1"],
        stdout=subprocess.PIPE
    )
    response, _ = process.communicate()
    txt = re.findall('Connecting to host', response.decode('utf-8'))
    if txt:
        return True
    else:
        return False


# 单位转换
def unitChange(bw):
    '''
    1b = 1bit
    1k = 1000bit
    1M = 1000kbit = 1000000bit
    1G = 1000Mbit = 1000000kbit = 1000000000bit
    '''
    unit = re.findall('[A-Za-z]', bw)[0]
    num = re.findall('[0-9.]+', bw)[0]
    if unit == 'b':
        res = float(num)
    elif unit == 'k':
        res = float(num) * 1000
    elif unit == 'M':
        res = float(num) * 1000000
    elif unit == 'G':
        res = float(num) * 1000000000
    return str(res)


# 计算总带宽
def addTwoBw(bw1, bw2):
    num1 = float(unitChange(bw1))
    num2 = float(unitChange(bw2))
    num = num1 + num2
    if num/1000000000 >= 1:
        res = str('%.2f'%(num/1000000000)) + 'Gbit'
    elif num/1000000 >= 1 and num/1000000 < 1000:
        res = str('%.2f'%(num/1000000)) + 'Mbit'
    elif num/1000 >= 1 and num/1000 < 1000:
        res = str('%.2f'%(num/1000)) + 'kbit'
    return res


# 计算平均带宽
def avgTwoBw(bw1, bw2):
    num1 = float(unitChange(bw1))
    num2 = float(unitChange(bw2))
    num = (num1 + num2)/2
    if num/1000000000 >= 1:
        res = str('%.2f'%(num/1000000000)) + 'Gbit'
    elif num/1000000 >= 1 and num/1000000 < 1000:
        res = str('%.2f'%(num/1000000)) + 'Mbit'
    elif num/1000 >= 1 and num/1000 < 1000:
        res = str('%.2f'%(num/1000)) + 'kbit'
    return res


# 客户端，client发送,server接收，上传
def uploadTest(test_string_dict, test_id):
    temp = test_string_dict
    # 参数
    avg_total_bandwidth = 0
    total_bandwidth = 0
    value_len = len(temp[test_id])
    if value_len > 5:
        process = subprocess.Popen(
            ["iperf3", "-c", temp[test_id][2], "-t", "1", "-P", temp[test_id][4], "-p", "5201", temp[test_id][8]],
            stdout=subprocess.PIPE
        )
        response, _ = process.communicate()
    else:
        process = subprocess.Popen(
            ["iperf3", "-c", temp[test_id][2], "-t", "1", "-P", temp[test_id][4], "-p", "5201"],
            stdout=subprocess.PIPE
        )
        response, _ = process.communicate()

    first_re = re.findall('SUM.+/sec', response.decode('utf-8'))
    re_list = re.findall('([\d.]+ *[A-Za-z.]+)/sec', response.decode('utf-8'))
    bandwidth_list = []
    if first_re and re_list:
        for parallel in range(int(temp[test_id][4])):
            bandwidth_list.append(re_list[parallel])
        total_bandwidth = '%.2f' % float(re.findall('([\d.]+) *[A-Za-z.]+/sec', first_re[0])[0])  # 不含单位
        avg_total_bandwidth = '%.2f' % (float(total_bandwidth) / len(bandwidth_list))  # 不含单位
        res = {
            "code": 1,
            "msg": "测试成功",
            "data": {
                "response": response.decode('utf-8') + '\n',
                "bandwidth": bandwidth_list,
                "avg_total_bandwidth": str(avg_total_bandwidth) + re.findall('[0-9.]+ ([A-Za-z]+)/sec', first_re[0])[0],
                "total_bandwidth": str(total_bandwidth) + re.findall('[0-9.]+ ([A-Za-z]+)/sec', first_re[0])[0],
            }
        }
    else:
        res = {
            "code": 0,
            "msg": "测试失败",
            "data": ""
        }
    return res


# 客户端，server发送,client接收，下载
def downloadTest(test_string_dict, test_id):
    temp = test_string_dict
    # 参数
    avg_total_bandwidth = 0
    total_bandwidth = 0
    value_len = len(temp[test_id])
    if value_len > 5:
        process = subprocess.Popen(
            ["iperf3", "-c", temp[test_id][2], "-t", "1", "-P", temp[test_id][4], "-p", "5202", temp[test_id][8], "-R"],
            stdout=subprocess.PIPE
        )
        response, _ = process.communicate()
    else:
        process = subprocess.Popen(
            ["iperf3", "-c", temp[test_id][2], "-t", "1", "-P", temp[test_id][4], "-p", "5202", "-R"],
            stdout=subprocess.PIPE
        )
        response, _ = process.communicate()

    first_re = re.findall('SUM.+/sec', response.decode('utf-8'))
    re_list = re.findall('([\d.]+ *[A-Za-z.]+)/sec', response.decode('utf-8'))
    bandwidth_list = []
    if first_re and re_list:
        for parallel in range(int(temp[test_id][4])):
            bandwidth_list.append(re_list[parallel])
        total_bandwidth = '%.2f' % float(re.findall('([\d.]+) *[A-Za-z.]+/sec', first_re[0])[0])
        avg_total_bandwidth = '%.2f' % (float(total_bandwidth) / len(bandwidth_list))
        res = {
            "code": 1,
            "msg": "测试成功",
            "data": {
                "response": response.decode('utf-8') + '\n',
                "bandwidth": bandwidth_list,
                "avg_total_bandwidth": str(avg_total_bandwidth) + re.findall('[0-9.]+ ([A-Za-z]+)/sec', first_re[0])[0],
                "total_bandwidth": str(total_bandwidth) + re.findall('[0-9.]+ ([A-Za-z]+)/sec', first_re[0])[0],
            }
        }
    else:
        res = {
            "code": 0,
            "msg": "测试失败",
            "data": ""
        }
    return res



# 添加测试流
def addTestString(req):
    if req.method == "POST":
        data = json.loads(req.body.decode())
        wifi_info_dict = getCurrentWifiInfo()
        operating_mode = data['operating_mode']      # -c/-s
        source_address = data['source_address']      # <host>
        server_address = data['server_address']      # <host>
        download_parallel_client = data['download_parallel_client']    # -P
        upload_parallel_client = data['upload_parallen_client']    # -P
        transmit_time = data['transmit_time']        # -t
        report_period = data['report_period']        # -i
        protocol = data['protocol']                  # -u(use UDP rather than TCP)
        port = data['port']                          # -p

        if operating_mode and source_address and server_address and download_parallel_client and upload_parallel_client:
            test_id = str(uuid.uuid1()).replace("-","")[-18:-10]
            res = {
                "code": 1,
                "msg": "添加成功",
                "data":{
                    "current_wifi": wifi_info_dict['ssid'],
                    "current_wifi_strength": wifi_info_dict['signal'],
                    "throughput_test_id": test_id
                }
            }
            if not (transmit_time and report_period and protocol and port):
                test_string_dict.update({test_id: ['-'+operating_mode, source_address, server_address, download_parallel_client, upload_parallel_client]})
            else:
                test_string_dict.update({test_id: ['-'+operating_mode, source_address, server_address, download_parallel_client, upload_parallel_client, '-t '+transmit_time, '-i '+report_period, '-'+protocol, '-p '+port]})
        else:
            res = {
                "code": 0,
                "msg": "添加失败，缺少字段",
                "data": ""
            }
    else:
        res = {
            "code": 0,
            "msg": "请求方式为GET请求",
            "data": ""
        }
        return HttpResponse(json.dumps(res))

