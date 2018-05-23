# IPProxyPool
IPProxyPool代理池项目，提供代理ip。支持py2和py3两个版本。
### 我的新书[《Python爬虫开发与项目实战》](https://item.jd.com/12206762.html)出版了,喜欢的话可以看一下[样章](http://pan.baidu.com/s/1hrWEOYg)
<br/>
详细使用方式，请看我的博客:
http://www.cnblogs.com/qiyeboy/p/5693128.html
<br/>
最近正在为IPProxyPool添加二级代理，方便调度。大家可以关注我的公众号，更新我会及时通知。
<br/>

#### 我的微信公众号:

![](qiye2.jpg)
<br/>
希望大家提供更多的代理网站，现在爬取的好用的代理ip还是太少。
<br/>
同时感谢[super1-chen](https://github.com/super1-chen),[fancoo](https://github.com/fancoo),[Leibnizhu](https://github.com/Leibnizhu)对项目的贡献。
<br/>

## 项目依赖

#### Ubuntu,debian

1.安装sqlite数据库(一般系统内置):
apt-get install sqlite3
<br/>
2.安装requests,chardet,web.py,gevent psutil:
pip install requests chardet web.py sqlalchemy gevent psutil
<br/>
3.安装lxml:
apt-get install python-lxml
<br/>
注意：

* python3下的是pip3
* 有时候使用的gevent版本过低会出现自动退出情况，请使用pip install gevent --upgrade更新)
* 在python3中安装web.py，不能使用pip，直接下载py3版本的[源码](https://codeload.github.com/webpy/webpy/zip/py3)进行安装

#### Windows

1.下载[sqlite](http://www.sqlite.org/download.html),路径添加到环境变量
<br/>
2.安装requests,chardet,web.py,gevent:
pip install requests chardet web.py sqlalchemy gevent
<br/>
3.安装lxml:
pip install lxml或者下载[lxml windows版](https://pypi.python.org/pypi/lxml/)
<br/>
注意：

* python3下的是pip3
* 有时候使用的gevent版本过低会出现自动退出情况，请使用pip install gevent --upgrade更新)
* 在python3中安装web.py，不能使用pip，直接下载py3版本的[源码](https://codeload.github.com/webpy/webpy/zip/py3)进行安装

#### 扩展说明

本项目默认数据库是sqlite，但是采用sqlalchemy的ORM模型，通过预留接口可以拓展使用MySQL，MongoDB等数据库。
配置方法：
<br/>
1.MySQL配置
```
第一步：首先安装MySQL数据库并启动
第二步：安装MySQLdb或者pymysql(推荐)
第三步：在config.py文件中配置DB_CONFIG。如果安装的是MySQLdb模块，配置如下：
        DB_CONFIG={
            'DB_CONNECT_TYPE':'sqlalchemy',
            'DB_CONNECT_STRING':'mysql+mysqldb://root:root@localhost/proxy?charset=utf8'
        }
        如果安装的是pymysql模块，配置如下：
         DB_CONFIG={
            'DB_CONNECT_TYPE':'sqlalchemy',
            'DB_CONNECT_STRING':'mysql+pymysql://root:root@localhost/proxy?charset=utf8'
        }
```
sqlalchemy下的DB_CONNECT_STRING参考[支持数据库](http://docs.sqlalchemy.org/en/latest/core/engines.html#supported-databases)，理论上使用这种配置方式不只是适配MySQL，sqlalchemy支持的数据库都可以，但是仅仅测试过MySQL。
<br/>
2.MongoDB配置
```
第一步：首先安装MongoDB数据库并启动
第二步：安装pymongo模块
第三步：在config.py文件中配置DB_CONFIG。配置类似如下：
        DB_CONFIG={
            'DB_CONNECT_TYPE':'pymongo',
            'DB_CONNECT_STRING':'mongodb://localhost:27017/'
        }
```
由于sqlalchemy并不支持MongoDB,因此额外添加了pymongo模式，DB_CONNECT_STRING参考pymongo的连接字符串。

##### 注意

如果大家想拓展其他数据库，可以直接继承db下ISqlHelper类，实现其中的方法，具体实现参考我的代码，然后在DataStore中导入类即可。
```
try:
    if DB_CONFIG['DB_CONNECT_TYPE'] == 'pymongo':
        from db.MongoHelper import MongoHelper as SqlHelper
    else:
        from db.SqlHelper import SqlHelper as SqlHelper
    sqlhelper = SqlHelper()
    sqlhelper.init_db()
except Exception,e:
    raise Con_DB_Fail
```
有感兴趣的朋友，可以将Redis的实现方式添加进来。


## 如何使用

### 本地使用

将项目目录clone到当前文件夹

$ git clone 

切换工程目录

```
$ cd IPProxyPool
```

运行脚本

```
python IPProxy.py
```
成功运行后，打印信息
```
IPProxyPool----->>>>>>>>beginning
http://0.0.0.0:8000/
IPProxyPool----->>>>>>>>db exists ip:0
IPProxyPool----->>>>>>>>now ip num < MINNUM,start crawling...
IPProxyPool----->>>>>>>>Success ip num :134,Fail ip num:7882
```

### 使用docker容器

$ git clone 

切换工程目录

```
$ cd IPProxys
$ docker build -t ipproxy .
$ docker run --name ipProxyPool -d -p 8080:8080 ipproxy
```

## API 使用方法

#### 第一种模式
```
GET /
```
这种模式用于查询代理ip数据，同时加入评分机制，返回数据的顺序是按照评分由高到低，速度由快到慢制定的。

#### 参数 

| Name | Type | Description |
| ----| ---- | ---- |
| types | int | 0: 高匿,1:匿名,2 透明 |
| protocol | int | 0: http, 1 https, 2 http/https |
| count | int | 数量 |
| country | str | 取值为 国内, 国外 |
| area | str | 地区 |



#### 例子

##### IPProxys默认端口为8000,端口可以在config.py中配置。

##### 如果是在本机上测试：

1.获取5个ip地址在中国的高匿代理：http://127.0.0.1:8000/?types=0&count=5&country=国内
<br/>
2.响应为JSON格式，按照评分由高到低，响应速度由高到低的顺序，返回数据：
<br/>
```
[["122.226.189.55", 138, 10], ["183.61.236.54", 3128, 10], ["61.132.241.109", 808, 10], ["183.61.236.53", 3128, 10], ["122.227.246.102", 808, 10]]
```
<br/>
以["122.226.189.55", 138, 10]为例，第一个元素是ip,第二个元素是port，第三个元素是分值score。

```
import requests
import json
r = requests.get('http://127.0.0.1:8000/?types=0&count=5&country=国内')
ip_ports = json.loads(r.text)
print ip_ports
ip = ip_ports[0][0]
port = ip_ports[0][1]
proxies={
    'http':'http://%s:%s'%(ip,port),
    'https':'http://%s:%s'%(ip,port)
}
r = requests.get('http://ip.chinaz.com/',proxies=proxies)
r.encoding='utf-8'
print r.text
```
#### 第二种模式
```
GET /delete
```
这种模式用于方便用户根据自己的需求删除代理ip数据

#### 参数 

| Name | Type | Description |
| ----| ---- | ---- |
| ip | str | 类似192.168.1.1 |
| port | int | 类似 80 |
| types | int |  0: 高匿,1:匿名,2 透明 |
| protocol | int | 0: http, 1 https, 2 http/https |
| count | int | 数量 |
| country | str | 取值为 国内, 国外 |
| area | str | 地区 |

大家可以根据指定以上一种或几种方式删除数据。

#### 例子

##### 如果是在本机上测试：

1.删除ip为120.92.3.127的代理：http://127.0.0.1:8000/delete?ip=120.92.3.127
<br/>
2.响应为JSON格式，返回删除的结果为成功,失败或者返回删除的个数,类似如下的效果：
["deleteNum", "ok"]或者["deleteNum", 1]
```
import requests
r = requests.get('http://127.0.0.1:8000/delete?ip=120.92.3.127')
print r.text
```
## config.py参数配置
```
#parserList是网址解析规则表,大家可以将发现的代理网址,将提取规则添加到其中,方便爬虫的爬取。
parserList = [
    {
        'urls': ['http://www.66ip.cn/%s.html' % n for n in ['index'] + list(range(2, 12))],
        'type': 'xpath',
        'pattern': ".//*[@id='main']/div/div[1]/table/tr[position()>1]",
        'position': {'ip': './td[1]', 'port': './td[2]', 'type': './td[4]', 'protocol': ''}
    },
    
   ......
 
   
    {
        'urls': ['http://www.cnproxy.com/proxy%s.html' % i for i in range(1, 11)],
        'type': 'module',
        'moduleName': 'CnproxyPraser',
        'pattern': r'<tr><td>(\d+\.\d+\.\d+\.\d+)<SCRIPT type=text/javascript>document.write\(\"\:\"(.+)\)</SCRIPT></td><td>(HTTP|SOCKS4)\s*',
        'position': {'ip': 0, 'port': 1, 'type': -1, 'protocol': 2}
    }
]

#数据库的配置

DB_CONFIG = {

    'DB_CONNECT_TYPE': 'sqlalchemy',  # 'pymongo'sqlalchemy;redis
    # 'DB_CONNECT_STRING':'mongodb://localhost:27017/'
    'DB_CONNECT_STRING': 'sqlite:///' + os.path.dirname(__file__) + '/data/proxy.db'
    # DB_CONNECT_STRING : 'mysql+mysqldb://root:root@localhost/proxy?charset=utf8'

    # 'DB_CONNECT_TYPE': 'redis',  # 'pymongo'sqlalchemy;redis
    # 'DB_CONNECT_STRING': 'redis://localhost:6379/8',

}
#THREADNUM为gevent pool的协程数目
THREADNUM = 5

#API_PORT为API web服务器的端口
API_PORT = 8000

#爬虫爬取和检测ip的设置条件
#不需要检测ip是否已经存在，因为会定时清理
# UPDATE_TIME:每半个小时检测一次是否有代理ip失效
UPDATE_TIME = 30 * 60 

# 当有效的ip值小于MINNUM时 需要启动爬虫进行爬取
MINNUM = 50  

# socket超时
TIMEOUT = 5 




#爬虫下载网页的重试次数
RETRY_TIME = 3


#USER_AGENTS 随机头信息,用来突破爬取网站的反爬虫

USER_AGENTS = [
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
   ]
#默认给抓取的ip分配20分,每次连接失败,减一分,直到分数全部扣完从数据库中删除
DEFAULT_SCORE=10

#CHECK_PROXY变量是为了用户自定义检测代理的函数,，默认是CHECK_PROXY={'function':'checkProxy'}。
#现在使用检测的网址是httpbin.org,但是即使ip通过了验证和检测
#也只能说明通过此代理ip可以到达httpbin.org,但是不一定能到达用户爬取的网址
#因此在这个地方用户可以自己添加检测函数,我以百度为访问网址尝试一下
#大家可以看一下Validator.py文件中的baidu_check函数和detect_proxy函数就会明白

CHECK_PROXY={'function':'checkProxy'}#{'function':'baidu_check'}
```
## TODO
1.添加squid代理，简化爬虫配置
<br/>


## 更新进度
-----------------------------2017-4-6----------------------------
<br/>
1.更新评分机制。
<br/>
* 之前的评分机制是刚添加进来每个代理ip为0分，每隔半个小时检测一次，检测之后依然有效则加分，无效则删除。
* 现在的评分机制是每个新的代理ip分配10分,每隔半个小时检测一次，检测之后依然有效则分数不变，无效则分数减一,直至为0删除,可以避免由于检测网站不稳定导致的误删。

2.用户可以自定义检测函数,在config.py的CHECK_PROXY变量中可以配置。
```
CHECK_PROXY变量是为了用户自定义检测代理的函数，默认是CHECK_PROXY={'function':'checkProxy'}
现在使用检测的网址是httpbin.org,但是即使ip通过了验证和检测
也只能说明通过此代理ip可以到达httpbin.org,但是不一定能到达用户爬取的网址
因此在这个地方用户可以自己添加检测函数,我以百度为访问网址尝试一下
大家可以看一下Validator.py文件中的baidu_check函数和detect_proxy函数就会明白。

CHECK_PROXY={'function':'baidu_check'}
```
3.经过大家的共同努力,彻底解决了僵死进程的问题。

-----------------------------2017-1-16----------------------------
<br/>
1.将py2和py3版本合并，并且兼容
<br/>
2.修复pymongo查询bug
<br/>
-----------------------------2017-1-11----------------------------
<br/>
1.使用httpbin.org检测代理ip的高匿性
<br/>
2.使用 国内 和 国外 作为country的查询条件
<br/>
3.修改types和protocol参数，一定要注意protocol的使用，试试访问http://www.baidu.com和https://www.baidu.com
<br/>
4.美化代码风格
<br/>
-----------------------------2016-12-11----------------------------
####大规模重构，主要包括以下几个方面：
1.使用多进程+协程的方式，将爬取和验证的效率提高了50倍以上，可以在几分钟之内获取所有的有效IP
<br/>
2.使用web.py作为API服务器，重构HTTP接口
<br/>
3.增加Mysql,MongoDB等数据库的适配
<br/>
4.增加了三个代理网站
<br/>
5.增加评分机制，评比稳定的ip
<br/>
6.支持python3
<br/>
-----------------------------2016-11-24----------------------------
<br/>
1.增加chardet识别网页编码
<br/>
2.突破66ip.cn反爬限制
<br/>
-----------------------------2016-10-27----------------------------
<br/>
1.增加对代理的检测，测试是否能真正访问到网址，实现代理
<br/>
2.添加通过正则表达式和加载插件解析网页的方式
<br/>
3.又增加一个新的代理网站
<br/>

-----------------------------2016-7-20----------------------------
<br/>
1.修复bug ,将数据库进行压缩
<br/>
