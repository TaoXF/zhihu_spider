# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json

import pymongo
import pymysql

import logging; logger = logging.getLogger(__name__)

from pymongo import errors


class MysqlPipeline(object):

	count = 0
	item_list = []

	def __init__(self, host, port, user, password, db_name):
		self.host = host
		self.port = port
		self.user = user
		self.password = password
		self.db_name = db_name

	@classmethod
	def from_crawler(cls, crawler):
		return cls(host=crawler.settings.get('MYSQL_HOST'),
		           port=crawler.settings.get('MYSQL_PORT'),
		           user=crawler.settings.get('MYSQL_USER'),
		           password=crawler.settings.get('MYSQL_PASSWORD'),
		           db_name=crawler.settings.get('MYSQL_DB_NAME'),
		           )

	def open_spider(self, spider):
		self.connect = pymysql.connect(host=self.host, user=self.user, password=self.password,
		                               port=self.port, db=self.db_name,  charset='utf8')
		self.cursor = self.connect.cursor()
		sql = "create table if not exists user_info" \
		      "(id int auto_increment primary key, " \
		      "user_id varchar(100), name varchar(50), " \
		      "gender int, headline varchar(500), " \
		      "url_token varchar(100), avatar_url varchar(100)," \
		      " answer_count int, articles_count int, follower_count int)"""

		self.cursor.execute(sql)
		self.connect.commit()

	def close_spider(self, spider):
		self.connect.close()

	def process_item(self, item, spider):
		info = [
			item['id'],
			item['name'],
			item['gender'],
			item['headline'],
			item['url_token'],
			item['avatar_url'],
			item['answer_count'],
			item['articles_count'],
			item['follower_count'],
		]
		self.count += 1
		self.item_list.append(info)
		sql = "insert into user_info(user_id, name, gender, headline, url_token," \
		      "avatar_url, answer_count, articles_count, follower_count)" \
		      "values(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
		if self.count >= 1000:
			try:
				self.cursor.executemany(sql, self.item_list)
				self.connect.commit()
				logger.info('inser into 1000 user_info')
			except:
				self.connect.rollback()
				logger.error('Inser Error')
			finally:
				self.count = 0
				self.item_list = []
		return item


class MongoPipeline(object):

	count = 0
	item_list = []

	def __init__(self, host, port, database, user, pwd, ):
		self.mongo_url = "mongodb://{user}:{pwd}@{host}:{port}/{database}".format(
			user=user, pwd=pwd, host=host, port=port, database=database
		)

	@classmethod
	def from_crawler(cls, crawler):
		return cls(
			host=crawler.settings.get('MONGO_HOST'),
			port=crawler.settings.get('MONGO_PORT'),
			database=crawler.settings.get('MONGO_DATABASE'),
			user=crawler.settings.get('MONGO_USER'),
			pwd=crawler.settings.get('MONGO_PWD'),
		)

	def open_spider(self, spider):
		self.client = pymongo.MongoClient(self.mongo_url)
		self.user_info_db = self.client.scrapy.user_info

	def close_spider(self, spider):
		self.client.close()

	def process_item(self, item, spider):

		self.count += 1
		self.item_list.append(item)
		if self.count >= 1000:
			logger.info('insert 1000 user_info in mongodb')
			try:
				self.user_info_db.insert_many(self.item_list)
			except errors.BulkWriteError as e:
				logger.error(e)
				logger.error('=' * 500)
				logger.error([item['_id'] for item in self.item_list])
				logger.error('=' * 500)
			finally:
				self.count = 0
				self.item_list = []
		return item