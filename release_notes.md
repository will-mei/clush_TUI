## 进度log
### 2019/5/20前
#### tui
* 基本窗口  主机组添加,部署任务添加,帮助页,主窗口
* 菜单      将窗口切换添加到中央菜单
* 本地语言  支持中文等东亚语言显示(基本支持全部Unicode语言)
* 调整      正常退出,中止退出,Ctrl+c也会被捕获并发送到当前窗口.      
* grptree   主机组的树状显示
* statusbox 状态负载信息框
* inputbox  获取命令输入
* msgbox    带时间戳和基本换行的中央信息更新控件
* 调整      monitor主机列表添加默认filter(Monitor)
* 调整      ceph集群主机使用快捷键完成状态自动切换节点类型,当前默认使用左右键
* 设计中    修改控件的 resize方法, 自动调整空间宽度,更新宽度信息
*           多行编辑器控件,添加原因是npyscreen基础控件在最初设计上就没有换行支持,因此需要重构或者设计单独的控件
*               (char_width_tool / LineBreak: v[行号][自动换行显示行号][行字符][游标值] )
*               单行 数组(cursor_position : char)
*                   自动换行    添加内部换行/隐藏超出部分(pager)
*                               更新行 (input char -- '\n' -- update array -- other printable -- update line)
*                   char_under_cursor(char)
*                   char_cursor(index_of_char)
*               多行 数组(nu : 单行数组)  #二维数组
* 设计中    修改 Form类的显示逻辑,从最小长度宽度初始化显示,npyscreen当前是以屏幕宽度初始化显示的,因此原有设计上后续的动态宽度调整只能扩大不能缩小
*           迭代测试任务配置窗口,
*           集群状态平铺显示窗口(适配测试和部署状态的查看),
*           主机列表添加主机搜索过滤filter,
*           默认将组节点标记为高亮
*           host group tree 节点连通状态颜色指示
*           实时命令行返回信息收敛统计,依赖于数据库查询更新
* 设计中    中断恢复:1历史和状态信息保存到数据库;2提供对象信息的导入方法
#### paramiko SSHConnection
* put       传送目录/文件
* get       拉取目录/文件
* exec_command  执行命令/命令列表
* exec_script   执行脚本
* close     手动关闭连接
#### paramiko ssh_to
* with      可以使用with语句建立ssh连接,在命令完成后自动关闭.

### 2019/5/20 
#### paramiko SSHConnection
* run       返回信息添加时间戳, 时间戳使用 datetime.datetime()对象,便于相互计算,同时保留主机ip在结果(元组)末尾,整组的输出结果的键值是主机名.
* update_ssh_info   更新连接信息
* update    重新/更新 连接, 以当前的连接配置重连
* reconnect 重置/恢复 连接, 以初始的连接配置重连
#### connection group
* run       方法    返回结果按: 主机-结果 的 k-v 字典列表 返回.
* grp_run   方法    不再为错误信息单独输出内容,返回结果是所有信息的合集,每个结果将包含自己的错误信息.
* cut_off   方法    仅尝试执行动作,不返回状态信息,以免不必要的中断.
* expel     方法    切断主机连接并从改组移除信息,直到它被重新添加否则状态不可用.

### 2019/5/21
#### connection group
* 设计中    计划使用协程完成批量远程任务
* run       方法    暂时改为使用多进程同步paramiko,完成ssh连接
* 进行中    放弃python3协程异步ssh连接,异步改造留待以后完成

### 2019/5/22
#### connection group
* 调整      因为虚拟机性能限制,弃用临时的多进程,改为使用多线程执行ssh连接
* 索引器    为连接组添加了索引器,连接组现在可以以主机名为键值选定某一台主机的连接,并可以使用循环迭代主机和连接
* str格式   为连接和连接组添加了更加清晰的 str 函数的输出结果
* 设计中    异步改造:并行ssh任务结果由异步http传送到数据库proxy,不再等待执行函数的return值

### 2019/5/23
#### connection group
* 日志      为连接的中间过程和函数状态添加日志,日志切割100M, rotate 份数5,其他配置留待调整
* exec_script   批量执行脚本
* put       批量拷贝文件
* get       批量拉取文件,支持目录拉取,不同主机来源将存入不同子目录
* 设计中    关联数据库返回值代理接收服务,由http接收各个session的命令返回结果,存到数据库中
*           发送结果方法api, 查询结果api

#### 2019/5/24
#### connection group
* 消息接口  确定消息使用json格式, 包含: 任务id, 消息内容(命令信息), 信息摘要, 时间
#### ssh terminal
* 设计中    添加命令任务的tcp监听服务
#### sqlite proxy
* 设计中    接收返回值并存入sqlite
#### tui
* 设计中    1使用指定间隔查询更新session返回结果
*           2在数据库proxy中添加事件通知,当某个session返回结果被更新时,在存入数据库的同时发送信息到前端

### 2019/5/27
#### connection group
* 消息接口  添加信息校验 时间超时,摘要
*           任务id使用更加易读格式: 时间戳+ 序号+ 随机字符id
*           时间戳用于检验超时,超时5秒以后收到消息无效
*           任务id检验信息有效性, 摘要与内容不一致消息无效
* 消息接口  发送端配置异步函数,发送后等待任务确认并完成通讯.
* 消息接口  信息分片与组包,length:总长度,no:编号,slice:分片内容

### 2019/5/28-29
#### 安全加固

### 2019/5/30
#### connection group
* api_server        v1 base line done
* api_client        v1 base line done

### 2019/5/31
#### connection group
* 消息接口          基本测试完成

### 2019/6/3
* terminal          socket日志与命令分发
* 进行中            使用sqlite3存储中间状态

### 2019/6/4
#### 虚拟机测试环境配置

### 2019/6/5-6
* sqlite3server     参阅sqlite3文档,需要设计ORM
