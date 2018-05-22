# zhihu_spider

### 实现功能:
   根据知乎的关注列表与粉丝列表进行整站用户信息抓取

### 使用条件
* 框架 scrapy
* 数据库 redis 用于实现存储请求url 与去重等功能
* 存储数据库 mysql 或 mongodb
* 必须要有可用的高匿名代理池队列

### spider.py
* ZhihuSpider 类\
主要用于请求生成 每个待抓取用户的 每一页关注与粉丝列表

* UserInfoSpider 类\
用于请求ZhihuSpider 生成的url 并添加未抓取的用户token到待抓取队列\
并解析用户信息返回item

### middlewares.py
* 全局变量 PROXY\
用与记录有效代理

* ProxyMiddleware\
用与检测出错一般都是timeout 或!200时 切换代理

* CustomRetryMiddleware\
用于重试时更换代理

* CustomUserAgentMiddleware\
user-agent 池

### pipelies.py
实现了mysql 与 mongodb 的储存\
mysql 使用的是executemany 插入多条数据的方式

如果要使用mongodb\
需要在time.py当中 __额外定义一个_id 字段__ 不用填值, 否则会报错\
mongodb 使用的是insert_many 插入多条的方式

**使用插入多条的优缺点**
优点就是相对节省性能,毕竟减少了与数据库的交互\
缺点就是有时会插入失败,造成小部分数据丢失, 当然概率是很小的

### custom.py
最主要的一个文件 里面定义了redis的一些相关方法

* get_proxy 方法\
取出代理 前提必须是已经实现了,有效代理池的添加.

* add_waiting 和 pop_waiting 方法\
添加待抓取用户token与 弹出 待抓取的token

* add_user_token 方法\
去重功能 每个用户与item都经过这个方法判断 必须未存在的才会继续执行下一步操作

* add_url 与 pop_url \
添加与取出 生成好的url地址
