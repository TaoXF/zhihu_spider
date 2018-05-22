# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class ZhihuUsersItem(Item):
    id = Field()
    name = Field()
    gender = Field()
    headline = Field()
    url_token = Field()
    avatar_url = Field()
    answer_count = Field()
    articles_count = Field()
    follower_count = Field()


