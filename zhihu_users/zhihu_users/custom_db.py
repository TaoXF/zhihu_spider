import redis
import time


class RedisClient(object):

    def __init__(self):
        self._db = redis.Redis(host='', port=6379, password='')

    def get_proxy(self):
        # 取出代理
        try:
            proxy = self._db.rpop('proxies').decode('utf-8')
            if isinstance(proxy, bytes):
                proxy = proxy.decode('utf-8')
            return 'http://' + proxy
        except:
            print('proxy is empty sleep 5')
            time.sleep(5)

    def pop_waiting(self):
        # 取出待抓取队列
        result = self._db.spop('waiting_queue')
        if isinstance(result, bytes):
            return result.decode('utf-8')
        return result

    def add_waiting(self, url_token):
        # 待抓取队列
        self._db.sadd('waiting_queue', url_token)

    def add_user_token(self, url_token):
        # 添加url_token 用于记录用户数据是否已添加
        # 不存在返回1 存在返回0
        return self._db.sadd('user_token', url_token)

    def add_url(self, url):
        # 添加生成好的url
        self._db.sadd('url', url)

    def pop_url(self):
        # 取出一个随机的url
        url = self._db.spop('url')
        if isinstance(url, bytes):
            return url.decode('utf-8')
        return url

redis_db = RedisClient()