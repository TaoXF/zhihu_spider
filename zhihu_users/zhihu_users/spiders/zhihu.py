# -*- coding: utf-8 -*-
import json
from json import JSONDecodeError

import logging; logger = logging.getLogger(__name__)

from scrapy import Spider, Request

from zhihu_users.items import ZhihuUsersItem

from zhihu_users.custom_db import redis_db


class ZhihuSpider(Spider):
	# 负责生成url请求队列
	# 两个api分别对应粉丝与关注列表

	name = 'zhihu'
	allowed_domains = ['www.zhihu.com']

	fans_api = 'https://www.zhihu.com/api/v4/members/{url_token}/followers?' \
	            'include=data%5B*%5D.answer_count%2Carticles_count%2Cgender%2C' \
	            'follower_count%2Cis_followed%2Cis_following%2C' \
	            'badge%5B%3F(type%3Dbest_answerer)%5D.topics&offset={offset}&limit=20'

	attention_api = 'https://www.zhihu.com/api/v4/members/{url_token}/followees?' \
	                'include=data%5B*%5D.answer_count%2Carticles_count%2Cgender%2C' \
	                'follower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F' \
	                '(type%3Dbest_answerer)%5D.topics&offset={offset}&limit=20'

	def start_requests(self):
		# 第一次请求 为了获取粉丝与关注的总数量
		# 结束后将url_token添加进已抓取用户队列当中

		url_token = redis_db.pop_waiting() or 'Germey'
		while url_token:
			yield Request(self.fans_api.format(url_token=url_token, offset='0'), dont_filter=True,
						  callback=lambda response, url_token=url_token:
						  self.fans_requests_parse(response, url_token))

			yield Request(self.attention_api.format(url_token=url_token, offset='0'), dont_filter=True,
						  callback=lambda response, url_token=url_token:
						  self.attention_requests_parse(response, url_token))

			url_token = redis_db.pop_waiting()

	def fans_requests_parse(self, response, url_token):
		# 用于生成粉丝列表每一页的url 并添加到url队列当中
		# totals 代表总数量

		totals = self.totals_pares(response)
		if totals and 100 <= totals:
			logger.info('生成粉丝列表请求 url_token is %s' %url_token)
			for offset in range(0, totals, 20):
				url = self.fans_api.format(url_token=url_token, offset=offset)
				redis_db.add_url(url)

	def attention_requests_parse(self, response, url_token):
		# 用于生成关注列表每一页的url

		totals = self.totals_pares(response)
		if totals:
			logger.info('生成关注列表请求 url_token is %s ' %url_token)
			for offset in range(0, totals, 20):
				url = self.attention_api.format(url_token=url_token, offset=offset)
				redis_db.add_url(url)

	@staticmethod
	def totals_pares(response):
		# 解析总数

		try:
			result = json.loads(response.text)
			paging = result.get('paging')
			if paging:
				totals = int(paging.get('totals'))
				if 0 != totals:
					return totals
		except JSONDecodeError:
			logger.error('JsonError status is %s text is %s' %(response.status, response.text))


class UserInfoSpider(Spider):
	# 负责请求url队列
	# 并添加新的待抓取用户队列

	name = 'zhihu_user_info'
	allowed_domains = ['www.zhihu.com']

	def start_requests(self):
		# 根据url生成Request

		url = redis_db.pop_url()
		while url:
			yield Request(url, callback=self.parse, dont_filter=True)
			url = redis_db.pop_url()

	def parse(self, response):
		# 负责解析response
		# 返回未抓取过的用户数据

		try:
			result = json.loads(response.text)
			datas = result.get('data')
			if datas:
				for data in datas:
					# 清洗数据只保留需要的部分
					item = ZhihuUsersItem()
					for field in item.fields:
						if field in data.keys():
							item[field] = data[field]
					url_token = data['url_token']
					if redis_db.add_user_token(url_token):
						redis_db.add_waiting(url_token)
						yield item
					else:
						logger.info('user_info existing')
			else:
				logger.info('data is None')

		except JSONDecodeError as e:
			logger.error('Json Error')
			logger.error(response.text)
			logger.error(response.headrts)
			logger.error(response.url)
