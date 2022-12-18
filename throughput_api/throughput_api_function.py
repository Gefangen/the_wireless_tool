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


test_string_dict = {}
global flag
flag = 1


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


# 开始测试
def beginThroughputTest(req):
    data = json.loads(req.body.decode())
    test_id = data["throughput_test_id"]    # 添加测试流生成的id
    temp = test_string_dict
    interval = 1

    # 参数
    avg_total_bandwidth = 0
    total_bandwidth = 0

    if temp[test_id][0] == 'c':
        for i in range(temp[test_id][1]):
            if flag == 1:
                if temp[test_id][5] == 'u':
                    process = subprocess.Popen(
                        ["iperf3", "-c", temp[test_id][3] ,"-t", "1", "-P", temp[test_id][4], "-u", "-p", temp[test_id][6], "-i", temp[test_id][7]], 
                        stdout=subprocess.PIPE
                    )
                    response, _ = process.communicate()
                    # communicate()的返回值是一个 tuple，第一个值是标准输出的数据，byte类型， 第二个输出是标准错误输出的内容。
                else:
                    process = subprocess.Popen(
                        ["iperf3", "-c", temp[test_id][3] ,"-t", "1", "-P", temp[test_id][4], "-p", temp[test_id][6], "-i", temp[test_id][7]], 
                        stdout=subprocess.PIPE
                    )
                    response, _ = process.communicate()
            
                first_re = re.findall('SUM.+/sec', response.decode('utf-8'))
                re_list = re.findall('([\d.]+) *[A-Za-z.]+/sec', response.decode('utf-8'))
                bandwidth_list = []
                string_type = 'sender'
                if first_re and re_list:
                    for parallel in range(int(temp[test_id][4])):
                        bandwidth_list.append(re_list[parallel])
                    if i == 0:    # 初次的平均带宽和总带宽
                        sum = 0
                        for band_width in bandwidth_list:
                            sum += float(band_width)
                        avg_total_bandwidth = sum/len(bandwidth_list)
                        total_bandwidth = float(re.findall('([\d.]+) *[A-Za-z.]+/sec', first_re[0])[0])
                    else:
                        sum = 0
                        for band_width in bandwidth_list:
                            sum += float(band_width)
                        avg_total_bandwidth = (avg_total_bandwidth + (sum/len(bandwidth_list))) / 2
                        total_bandwidth = (total_bandwidth + float(re.findall('([\d.]+) *[A-Za-z.]+/sec', first_re[0])[0])) / 2
                    with open(test_id + '.log', "a") as f:
                        f.write('时间戳：'+str(time.time())+'\n')
                        f.write(response.decode('utf-8')+'\n')
                        f.write('avg_total_bandwidth='+str(avg_total_bandwidth)+'\n')
                        f.write('total_bandwidth='+ str(total_bandwidth)+'\n')
                        f.flush
                        time.sleep(interval)
                    for x in range(len(bandwidth_list)):
                        res = {
                            "code": 1,
                            "msg": "测试成功",
                            "current_wifi": "xxx",
                            "data":{
                                "id_of_time": test_id,
                                "string_type": string_type,
                                "bandwidth": bandwidth_list[x],
                                "avg_total_bandwidth": avg_total_bandwidth,
                                "total_bandwidth": total_bandwidth,
                            }
                        }
                        with open(test_id + '_res.log', "a") as f:
                            f.write(str(res)+'\n')
                            f.flush()
                else:    # 丢包情况
                    res = {
                        "code": 0,
                        "msg": "测试失败",
                        "data": ""
                    }
                    with open(test_id + '_res.log', "a") as f:
                        f.write(str(res)+'\n')
                        f.flush()
            else:
                print('测试终止')
                res = {
                    "code":0,
                    "msg":'测试终止',
                }
                with open(test_id + '_res.log', "a") as f:
                    f.write(str(res)+'\n')
                    f.flush()
                break
    else:   # 工作模式是's'
        index = 0
        while flag == 1:
            process = subprocess.Popen(
                ["iperf3", "-s", temp[test_id][3] , "-p", temp[test_id][6], "-i", temp[test_id][7]], 
                stdout=subprocess.PIPE
            )
            response, _ = process.communicate()
            first_re = re.findall('SUM.+/sec', response.decode('utf-8'))
            re_list = re.findall('([\d.]+) *[A-Za-z.]+/sec', response.decode('utf-8'))
            bandwidth_list = []
            string_type = 'receiver'
            if first_re and re_list:
                for parallel in range(int(temp[test_id][4])):
                    bandwidth_list.append(re_list[parallel])
                if index == 0:    # 初次的平均带宽和总带宽
                    sum = 0
                    for band_width in bandwidth_list:
                        sum += float(band_width)
                    avg_total_bandwidth = sum/len(bandwidth_list)
                    total_bandwidth = float(re.findall('([\d.]+) *[A-Za-z.]+/sec', first_re[0])[0])
                else:
                    sum = 0
                    for band_width in bandwidth_list:
                        sum += float(band_width)
                    avg_total_bandwidth = (avg_total_bandwidth + (sum/len(bandwidth_list))) / 2
                    total_bandwidth = (total_bandwidth + float(re.findall('([\d.]+) *[A-Za-z.]+/sec', first_re[0])[0])) / 2
                index += 1
                with open(test_id + '.log', "a") as f:
                    f.write('时间戳：'+str(time.time())+'\n')
                    f.write(response.decode('utf-8')+'\n')
                    f.write('avg_total_bandwidth='+str(avg_total_bandwidth)+'\n')
                    f.write('total_bandwidth='+ str(total_bandwidth)+'\n')
                    f.flush
                    time.sleep(interval)
                for x in range(len(bandwidth_list)):
                    res = {
                        "code": 1,
                        "msg": "测试成功",
                        "current_wifi": "xxx",
                        "data":{
                            "id_of_time": test_id,
                            "string_type": string_type,
                            "bandwidth": bandwidth_list[x],
                            "avg_total_bandwidth": avg_total_bandwidth,
                            "total_bandwidth": total_bandwidth,
                        }
                    }
                    with open(test_id + '_res.log', "a") as f:
                        f.write(str(res)+'\n')
                    f.flush()
            else:    # 丢包情况
                res = {
                    "code": 0,
                    "msg": "测试失败",
                    "data": ""
                }
                with open(test_id + '_res.log', "a") as f:
                    f.write(str(res)+'\n')
                    f.flush()
            if flag == 0:
                print('测试终止')
                res = {
                    "code":0,
                    "msg":'测试终止',
                }
                with open(test_id + '_res.log', "a") as f:
                    f.write(str(res)+'\n')
                    f.flush()
                break
                


# 停止时延抖动测试
def stopThroughputTest(req):
    if req.method == 'POST':
        global flag
        flag = 0


# 扫描wifi接口
def scanWifi(req):
    if req.method == 'POST':
        cmd_output = os.popen('netsh wlan show interface')
        cmd_txt = cmd_output.read()
        ssid = re.findall('(?:SSID +: )(\S*)', cmd_txt)
        bssid = re.findall('(?:BSSID +: )(\S*)', cmd_txt)
        radio_type = re.findall('(?:Radio type +: )(\S*)', cmd_txt)
        signal = re.findall('(?:Signal +: )(\S*)', cmd_txt)
        if ssid:
            current_wifi_ssid = ssid[0]
        else:
            print('无法读取当前wifi的ssid')
        
        if bssid:
            current_wifi_bssid = bssid[0]
        else:
            print('无法读取当前wifi的bssid')

        if radio_type:
            if radio_type[0] == '802.11b':
                current_wifi_radio_frequency = '2.4GHz'
            elif radio_type[0] == '802.11ac':
                current_wifi_radio_frequency = '5GHz'
            else:
                current_wifi_radio_frequency = radio_type[0]
        else:
            print('无法读取当前wifi的频段')
        
        if signal:
            current_wifi_strength = signal[0]
        else:
            print('无法读取当前wifi的信号强度')
        
        if ssid and bssid and radio_type and signal:
            res = {
                "data":wifi_scan,
                "code":1,
                "msg":"扫描成功",
                "current_wifi":current_wifi_ssid,
                "current_wifi_strength":current_wifi_strength
            }
            return HttpResponse(json.dumps(res))
        else:
            res = {
                "data":"",
                "code":0,
                "msg":"扫描失败"
            }
            return HttpResponse(json.dumps(res))
