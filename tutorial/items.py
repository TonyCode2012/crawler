# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TutorialItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class Restaurant(scrapy.Item):
    restaurantName = scrapy.Field()
    restaurantId = scrapy.Field()
    address = scrapy.Field()
    latitude = scrapy.Field()
    longitude = scrapy.Field()
    month_sales = scrapy.Field()
    month = scrapy.Field()
    total_month_sales = scrapy.Field()
    storage_time = scrapy.Field()

class Dish(scrapy.Item):
    restaurantId = scrapy.Field()
    name = scrapy.Field()
    category_name = scrapy.Field()
    price = scrapy.Field()
    month_sales = scrapy.Field()
    month = scrapy.Field()
    storage_time = scrapy.Field()
