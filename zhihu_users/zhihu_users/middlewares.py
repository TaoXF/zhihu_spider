# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import random
import logging; logger = logging.getLogger(__name__)

from scrapy import signals, Request
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.response import response_status_message

from .custom_db import redis_db

PROXY = None



class ZhihuUsersSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ZhihuUsersDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ProxyMiddleware(object):

    # process_request: Add proxy when proxy is None
    # process_response: change proxy retry when status_code != 200
    # process_exception: change proxy retry when error

    def process_request(self, request, spider):

        if not request.meta.get('proxy'):
            request.meta['proxy'] = PROXY or redis_db.get_proxy()

    def process_response(self, request, response, spider):

        global PROXY

        if response.status == 401:
            raise IgnoreRequest
        if response.status != 200:
            PROXY = redis_db.get_proxy()
            logger.error("status is %s change self proxy %s" %(response.status ,PROXY))
            try:
                del request.meta['proxy']
                return request
            except KeyError:
                return request
        else:
            PROXY = request.meta.get('proxy')
            return response

    def process_exception(self, request, exception, spider):

        global PROXY

        PROXY = redis_db.get_proxy()
        logger.error("Error request url is %s" %request.url)
        try:
            del request.meta['proxy']
            return request
        except KeyError:
            return request


class CustomRetryMiddleware(RetryMiddleware):
    # change proxy when retry

    def process_response(self, request, response, spider):

        global PROXY

        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            PROXY = redis_db.get_proxy()
            logger.error(" change proxy %s retry " %PROXY)
            try:
                del request.meta['proxy']
                return self._retry(request, reason, spider) or response
            except KeyError:
                return self._retry(request, reason, spider) or response
        return response


class CustomUserAgentMiddleware(UserAgentMiddleware):

    def __init__(self, user_agent):
        super().__init__(user_agent)
        self.user_agent = user_agent

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            user_agent=crawler.settings.get('USER_AGENT_LIST')
        )

    def process_request(self, request, spider):
        agent = random.choice(self.user_agent)
        request.headers['User-Agent'] = agent
