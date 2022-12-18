import os
from pickletools import floatnl
import re
import json
from urllib import response
import pywifi
import time
import subprocess
import uuid
import asyncio
import websockets
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
    

# 获取当前WiFi连接信息
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


# 添加测试流信息
def addTestString(req):
    if req.method == "POST":
        data = json.loads(req.body.decode())
        wifi_info_dict = getCurrentWifiInfo()
        source_address = data['source_address']
        destination_address = data['destination_address']
        data_byte = data['data_byte']
        time_interval = data['time_interval']
        number_of_pings = data['number_of_pings']
        if source_address and destination_address and data_byte and time_interval and number_of_pings:
            test_id = str(uuid.uuid1()).replace("-","")[-18:-10]
            res = {
                "code": 1,
                "msg": "添加成功",
                "data": {
                    "current_wifi": wifi_info_dict['ssid'],
                    "current_wifi_strength": wifi_info_dict['signal'],
                    "delay_test_id": test_id
                }
            }
            test_string_dict.update({test_id: [source_address, destination_address, data_byte, time_interval, number_of_pings]})
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


# fping环境检测
def testEnvironment():
    process = subprocess.Popen(
        ["fping"],
        stdout=subprocess.PIPE()
    )
    response, _ = process.communicate()
    txt = re.findall('Fast pinger version [0-9].+', response.decode('utf-8'))
    if txt:
        return True
    else:
        return False


# 开始测试
def beginDelayTest(req):
    data = json.loads(req.body.decode())
    test_id = data["delay_test_id"]    # 添加测试流生成的id
    temp = test_string_dict
    interval = 1
    destination_address = temp[test_id][1]

    # 参数
    max_delay = 0
    min_delay = 0
    avg_delay = 0
    number_of_loss_packet = 0
    current_number_of_pings = 0
    packet_send = 0
    packet_receive = 0

    for i in range(int(temp[test_id][4])):     # temp[test_id][4]是测试流中ping包的个数
        if flag == 1:
            process = subprocess.Popen(
                ["fping", destination_address, "-n 1", "-s", temp[test_id][2], "-t", temp[test_id][3]], 
                stdout=subprocess.PIPE
                )
            response, _ = process.communicate()
            # communicate()的返回值是一个 tuple，第一个值是标准输出的数据，byte类型， 第二个输出是标准错误输出的内容。
            packet_send += 1   # 发送包数加一
            current_number_of_pings += 1   # 当前的ping包加一
            packet_loss_ratio = number_of_loss_packet/packet_send  # 丢包率
            delay_time = re.findall('time=([\d.]+) *ms', response.decode('utf-8'))
            if delay_time:
                packet_receive += 1  # 接收包数加一
                if i == 0:
                    max_delay = float(delay_time[0])
                else:
                    if float(delay_time[0]) > max_delay:
                        max_delay = float(delay_time[0])  # 最大时延

                if i == 0:
                    min_delay = float(delay_time[0])
                else:
                    if float(delay_time[0]) < min_delay:
                        min_delay = float(delay_time[0])  # 最小时延
                
                if i == 0:
                    avg_delay = float(delay_time[0])   # 首次平均时延为第一个包的时延
                else:
                    avg_delay = (avg_delay + float(delay_time[0]))/2   # 平均时延
                write_in = '[' + str(time.time()) + ' ## ' + response.decode('utf-8') + ' ## ' + delay_time[0] + 'ms]'
                with open(test_id + '.log', "a") as f:
                    f.write(str(time.time()))
                    f.write(response.decode('utf-8'))
                    f.write(delay_time[0])
                    f.flush
                    time.sleep(interval)
                res = {
                    "code":1,
                    "msg":'测试成功',
                    "data":{
                        "current_wifi":'xxx',
                        "local_data":{
                            "id_of_ping": test_id,
                            "delay": float(delay_time[0])
                        }
                    },
                    "global_data":{
                        "max_delay": max_delay,
                        "min_delay": min_delay,
                        "avg_delay": avg_delay,
                        "packet_send": packet_send,
                        "packet_receive": packet_receive,
                        "packet_loss_ratio": '%.2f%%' % (packet_loss_ratio*100),
                        "number_of_loss_packet": number_of_loss_packet,
                        "current_number_of_pings": current_number_of_pings
                    }                        
                }
                with open(test_id + '_res.log', "a") as f:
                    f.write(str(res))
                    f.flush()
            else:  # 丢包情况
                number_of_loss_packet += 1
                packet_loss_ratio = number_of_loss_packet/packet_send  # 丢包率
                write_in = '[' + str(time.time()) + ' ## ' + response.decode('utf-8') + ' ## ' + '-1' + 'ms]'
                with open(test_id + '.log', "a") as f:
                    f.write(write_in)
                    f.flush
                    time.sleep(interval)
                res = {
                    "code":1,
                    "msg":'测试成功',
                    "data":{
                        "current_wifi":'xxx',
                        "local_data":{
                            "id_of_ping": test_id,
                            "delay": '-1'
                        }
                    },
                    "global_data":{
                        "max_delay": max_delay,
                        "min_delay": min_delay,
                        "avg_delay": avg_delay,
                        "packet_send": packet_send,
                        "packet_receive": packet_receive,
                        "packet_loss_ratio": '%.2f%%' % (packet_loss_ratio*100),
                        "number_of_loss_packet": number_of_loss_packet,
                        "current_number_of_pings": current_number_of_pings
                    }                        
                }
                with open(test_id + '_res.log', "a") as f:
                    f.write(str(res))
                    f.flush()
        else:
            print('测试终止')
            res = {
                "code":0,
                "msg":'测试终止',
            }
            return res

      
# 停止时延抖动测试
def stopDelayTest(req):
    if req.method == 'POST':
        global flag
        flag = 0


# 实时读取文件最新信息
def follow(thefile):
    thefile.seek(0, 2)
    while True:
        txt = thefile.read()
        if not txt:
            time.sleep(0.1)
            continue
        yield txt



# websocket部分
# 给客户端发信息
async def send_msg(websocket):
    # logfile = open(list(test_string_dict.keys())[0] + '_res.log', 'r')
    with open(list(test_string_dict.keys())[0] + '_res.log', 'r') as logfile:
        loglines = follow(logfile)
        while True:
            for line in loglines:
                res = line
                response_text = f"your submit context: {str(res)}"
                await websocket.send(response_text)


# 服务器端主逻辑
async def main_logic(websocket, path):
    await send_msg(websocket)


start_server = websockets.serve(main_logic, 'localhost', 9999)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()