
#### 一、时延抖动模块
#### 1. 开始扫描wifi

路由：/beginScan

请求方式：post

| 参数                          |  类型   |       说明                                    |
| :---------------------------: | :----: | :-------------------------------------------: |
| current_wifi_ssid             | string |  当前电脑连接的wifi无线ssid                     |
| current_wifi_radio_frequency  | string |  当前电脑连接的wifi的频段信息（2.4GHz或者5GHz）  |

成功

```
code:1
msg:'扫描成功'
result:{
		current_wifi: 'xxxx',   //当前连接的wifi名
		current_wifi_strength: 'xxx',   //当前连接的wifi信号强度
		data:{
			'wifi_name': signal_num, //wifi名-信号值的键值对
			'xxx': 'xxx',
			'xxx': 'xxx'
		}
}
```

失败：

```
code:0
msg:'扫描失败',
result:null
```


#### 2. 停止扫描wifi

路由：/stopScan

请求方式：post

| 参数      |   类型  |       说明         |
| :-------: | :----: | :----------------: |
|           |        |                    |

成功：

```
code:1
msg:'成功'
result:{
		current_wifi:'xxxx', //当前连接的wifi
		current_wifi_strength: 'xxx'   //当前连接的wifi信号强度
}
```

失败：

```
code:0
msg:'失败',
result:null
```


#### 3. 绑定wifi

路由：/associatedWifi

请求方式：post

| 参数                             |  类型   |            说明            |
| :------------------------------: | :----: | :------------------------: |
| associated_wifi_ssid             | string |      绑定wifi的SSID信息     |
| associated_wifi_radio_frequency  | string |      绑定wifi的频段信息     |

成功

```
code:1
msg:'绑定成功'
result:{
		current_wifi:'xxx',   //当前连接的wifi
		current_wifi_strength:'xxx'   //当前连接的wifi信号强度
}
```

失败：

```
code:0
msg:'绑定失败',
result:null
```


#### 4. 添加测试流

 路由：/ addTestString 

请求方式：post

| 参数                | 类型    | 说明          |
| ------------------- | ------ | :-----------: |
| source_address      | string | 源地址         |
| destination_address | string | 目的地址       |
| data_byte           | string | 数据包大小     |
| time_interval       | string | ping的时间间隔 |
| number_of_pings     | string | ping的的包个数 |

成功：

```
code:1
msg:'添加成功'
result:{
		current_wifi:'xxx',   //当前连接的wifi
		current_wifi_strength:'xxx',   //当前连接的wifi信号强度
		delay_test_id: 'xxx' //测试流的id
}
```

失败：

```
code:0
msg:'参数错误',
result:null
```


#### 5. 开始时延抖动测试

路由：/beginDelayTest

请求方式：get

| 参数                |  类型   |       说明        |
| :----------------:  | :----: | :---------------: |
| delay_test_id       | string |   测试流的id       |


```
code:1
msg:'测试成功'
result:{
		current_wifi:'xxx',   //当前连接的wifi
		current_wifi_strength:'xxx',   //当前连接的wifi信号强度
		local_data:{
			id_of_ping:'xxxx',   //当前单个ping测试的序号数
			delay: 'xxx',   //当前单个ping的时延，单位为ms
		},
		global_data:{
			max_delay: 'xxx',   //截止当前时间，该测试流最大的ping测试时延，单位ms
			min_delay: 'xxx',   //截止当前时间，该测试流最小的ping测试时延，单位ms
			avg_delay: 'xxx',   //截止当前时间，该测试流平均的ping测试时延，单位ms
			packet_send: 'xxx',    //发送包个数
			packet_receive: 'xxx',    //接收包个数
			packet_loss_ratio: 'xxx'    //截止当前时间，该测试流的ping丢包率，单位为%
			number_of_loss_packet: 'xxx'    //截止当前时间，该测试流的ping丢包数量
			current_number_of_pings: 'xxx'    //截止当前时间，该测试流总共的ping包数量
		}		
}
```

失败

```
code:0
msg:'测试失败',
result:null
```


#### 6. 停止时延抖动测试

路由：/stopDelayTest

请求方式：post

| 参数      |   类型  |       说明         |
| :-------: | :----: | :----------------: |
|           |        |                    |

成功：

```
code:1
msg:'成功'
result:{
		current_wifi:'xxx',   //当前连接的wifi
		current_wifi_strength:'xxx',   //当前连接的wifi信号强度
		delay_test_id: 'xxx' //测试流的id
}
```

失败：

```
code:0
msg:'失败',
result:null
```




#### 二、漫游测试模块
#### 1. 绑定当前WiFi

路由：/associatedWifi

请求方式：post

| 参数                             |  类型   |            说明            |
| :------------------------------: | :----: | :------------------------: |
| associated_wifi_ssid             | string |      绑定wifi的SSID信息     |
| associated_wifi_radio_frequency  | string |      绑定wifi的频段信息     |

成功

```
code:1
msg:'绑定成功'
result:{
		current_wifi:'xxx',   //当前连接的wifi
		current_wifi_strength:'xxx',   //当前连接的wifi信号强度
}
```

失败：

```
code:0
msg:'绑定失败',
result:null
```


#### 2. 开始漫游测试

路由：/beginRoamingTest

请求方式：post

| 参数                |  类型   |    说明                              |
| ------------------- | ------ | ------------------------------------ |
| current_wifi        | string |   当前连接的wifi                      |
| destination_address | string |   每条ping测试流的目的地址             |
| data_byte           | string |   每次ping测试流的包大小，单位为byte    |
| time_interval       | string |   每个ping测试之间的时间间隔，单位为s   |


成功

```
code:1
msg:'测试成功'
result:{
		roaming_test_id: 'xxx',
		data:{
			id_of_ping:'xxxx',   //当前单个ping测试的序号数
			delay: 'xxx',
			avg_delay: 'xxx',   //截止当前时间，该测试流平均的ping测试时延，单位ms
			current_wifi_strenth: 'xxx',    //当前电脑连接的WiFi的信号强度信息
			packet_loss_ratio: 'xxx'    //截止当前时间，该测试流的ping丢包率，单位为%
			avg_delay: 'xxx',   //截止当前时间，该测试流平均的ping测试时延，单位ms
			packet_send: 'xxx',    //发送包个数
			packet_receive: 'xxx',    //接收包个数
			ap_bssid: 'xxx'    //连接ap的BSSID		
		}		
}
```

失败

```
code:0
msg:'获取失败'
result:null
```


#### 3. 停止漫游测试

路由：/stopRoamingTest

请求方式：get

| 参数          |  类型   |       说明        |
| :----------:  | :----: | :---------------: |
|               |        |                   |


成功：

```
code:1
msg:'成功'
result:{
		roaming_test_id: 'xxx',
		current_wifi:'xxx',   //当前连接的wifi
		current_wifi_strength:'xxx',   //当前连接的wifi信号强度
}
```

失败：

```
code:0
msg:'失败',
result:null
```



#### 三、吞吐量测试模块
#### 1. 绑定当前WiFi

路由：/associatedWifi

请求方式：post

| 参数                             |  类型   |            说明            |
| :------------------------------: | :----: | :------------------------: |
| associated_wifi_ssid             | string |      绑定wifi的SSID信息     |
| associated_wifi_radio_frequency  | string |      绑定wifi的频段信息     |

成功

```
code:1
msg:'绑定成功'
result:{
		current_wifi:'xxx',   //当前连接的wifi
		current_wifi_strength:'xxx',   //当前连接的wifi信号强度
}
```

失败：

```
code:0
msg:'绑定失败',
result:null
```


#### 2. 开始吞吐量测试

路由：/beginThroughputTest

请求方式：post

| 参数             |  类型   |  说明                                                    |
| ---------------- | ------ | -------------------------------------------------------- |
| operating_mode   | string |  设置当前终端的角色，client或者server                      |
| transmit_time    | string |  设置每次吞吐量测试的测试持续时间                           |
| source_address   | string |  源地址                                                   |
| server_address   | string |  每个ping测试之间的时间间隔，单位为s                        |
| parallel_client  | string |  设置每个类型测试流的数量                                   |
| stream_type      | string |  测试流的类型，上传或者下载                                 |
| protocol         | string |  设置每条测试流的协议类型，tcp或者udp                        |
| port             | string |  设置每条测试流的协议端口                                   |
| report_period    | string |  设置每次吞吐量测试的cmd返回信息的时间间隔，默认为1s，单位为s  |



成功

```
code:1
msg:'测试成功'
result:{
		throughput_test_id: 'xxx',
		data:{
			id_of_time: 'xxxx',   //每次吞吐量测试之间的时间间隔，单位为s
			bandwidth: 'xxx',    //每条测试流的带宽数值
			stream_type: 'xxx',   //测试流的类型，上传或者下载
			total_bandwidth: 'xxx',    //总带宽
			packet_loss_ratio: 'xxx'    //截止当前时间，该测试流的ping丢包率，单位为%
			avg_total_bandwidth: 'xxx',   //平均带宽		
		}		
}
```

失败

```
code:0
msg:'测试失败'
result:null
```


#### 3. 停止吞吐量测试

路由：/stopThroughputTest

请求方式：get

| 参数          |  类型   |       说明        |
| :----------:  | :----: | :---------------: |
|               |        |                   |


成功：

```
code:1
msg:'成功'
result:{
		current_wifi:'xxx',   //当前连接的wifi
		current_wifi_strength:'xxx',   //当前连接的wifi信号强度
}
```

失败：

```
code:0
msg:'失败',
result:null
```



#### 数据库表设计

User：

| 参数     | 类型      | 说明           |
| -------- | -------- | -------------- |
| account  | char(20) | 主键           |
| password | char(20) |                |
| uid      | char(20) | 外键           |
| admin    | int      | 管理员身份0或1  |
|          |          |                |



attack_Graph:

| 参数        | 类型           | 说明               |
| ----------- | ------------- | ------------------ |
| uid         | char(20)      | 主键               |
| graphId     | char(20)      | 主键               |
| attackGraph | varchar(100)  | 攻击图url          |
| filename    | char(20)      | 文件名             |
| analysis    | varchar(1000) | 路径分析           |
| isCollected | int           | 是否收藏，值为0或1  |
|             |               |                    |
|             |               |                    |