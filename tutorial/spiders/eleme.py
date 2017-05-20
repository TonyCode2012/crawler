import scrapy
import json
import codecs
import time
import copy
import logging
import logging.config
import yaml
from scrapy.utils.log import configure_logging
from ..utils import mystring
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from ..items import *

with codecs.open("log.yml", 'r') as ymlfile:
    log_cfg = yaml.load(ymlfile)

logging.config.dictConfig(log_cfg)
elog = logging.getLogger('eleme')

class eleSpd(scrapy.Spider):
    name = 'eleme'

    outputfile = 'dish.json'
    restfile = 'restaurant.json'
    failurefile = 'failurefile'
    reqFauledList = []
    reqRetryDict = {}
    latitude = 31.09262
    longitude = 121.31891
    retry = 3

    url_tlp = ['https://mainsite-restapi.ele.me/shopping/restaurants?extras%5B%5D=activities&geohash=wtw2bsjxxkr&latitude=31.09262&limit=24&longitude=121.31891&offset={offset}&terminal=web','https://mainsite-restapi.ele.me/shopping/restaurants?extras%5B%5D=activities&geohash=wtw31rrjbnf&latitude=31.15413&limit=24&longitude=121.35361&offset={offset}&terminal=web']

    def start_requests(self):
        # erase existed content
        open(eleSpd.outputfile, 'w').close()
        open(eleSpd.failurefile, 'w').close()
        open(eleSpd.restfile, 'w').close()

        # try possibly existed url
        for url in eleSpd.url_tlp:
            for offset in [x * 24 for x in range(5)]:
                url = url.format(**{'offset':offset})
                #time.sleep(1)
                yield scrapy.Request(url=url,callback=self.parse)

    def parse(self, response):
        shops = json.loads(response.body)
        shopUrl_tlp = 'https://mainsite-restapi.ele.me/shopping/v2/menu?restaurant_id={restId}' 
        count = 0

        for shop in shops:
            #if count > 2:
            #    break
            #count += 1
            name = shop['name']
            restId = shop['id']
            address = shop['address']
            month = time.localtime().tm_mon
            month_sales = shop['recent_order_num']
            stime = int(time.strftime('%Y%m%d%H%M%S',time.localtime()))
            # request Restaurant info
            shopUrl = shopUrl_tlp.format(**{'restId':restId})
            request = scrapy.Request(url=shopUrl,callback=self.parse_shop,errback=self.errback_httpbin)
            request.meta['dish'] = {}
            dish = request.meta['dish']
            dish['restaurantId'] = restId
            dish['storage_time'] = stime
            dish['month'] = month
            # pass shop info in request meta
            request.meta['restaurant'] = {}
            restItem = request.meta['restaurant']
            restItem['restaurantName'] = name
            restItem['restaurantId'] = restId
            restItem['address'] = address
            restItem['month'] = month
            restItem['month_sales'] = month_sales
            restItem['storage_time'] = stime
            restItem['latitude'] = eleSpd.latitude
            restItem['longitude'] = eleSpd.longitude
            #time.sleep(1)
            yield request

        # submit failed jobs
        #while 1:
        #    for url in eleSpd.reqFauledList:
        #        yield scrapy.Request(url=url,callback=self.parse_shop,errback=self.errback_httpbin)
        #        self.logger.error('Retry the %d time on url: %s',eleSpd.reqRetryDict[reqUrl]+1, url)
        #        time.sleep(3)
        #    if len(eleSpd.reqFauledList) == 0:
        #        break

    def parse_shop(self, response):
        # request successfully delete url from reqFauledList
        #if eleSpd.reqFauledList.count(response.url) != 0:
        logging.info('url %s is requested successfully', response.url)
        elog.info('url %s is requested successfully', response.url)
        if eleSpd.reqRetryDict.has_key(response.url):
            #print '//////////////////Retry url is:%s' % response.url
            eleSpd.reqFauledList.remove(response.url)

        food_category = json.loads(response.body)
        dish = Dish()
        restaurant = Restaurant()
        total_month_sales = 0
        dish = response.meta['dish']
        restaurant = response.meta['restaurant']
        dish_set = []

        with codecs.open(eleSpd.outputfile, 'ab','utf-8') as f:
            for fctg in food_category:
                dish['category_name'] = fctg['name']
                for food in fctg['foods']:
                    food_name = food['name']
                    if dish_set.count(food_name) != 0:
                        continue
                    else:
                        dish_set.append(food_name)
                    dish['name'] = food_name
                    dish['month_sales'] = food['month_sales']
                    dish['price'] = food['specfoods'][0]['price']
                    total_month_sales += dish['month_sales'] * dish['price']
                    json.dump(dish,f,encoding='utf-8',ensure_ascii=False)
                    f.write('\n')
                    yield dish

        with codecs.open(eleSpd.restfile, 'ab' ,'utf-8') as f:
            restaurant['total_month_sales'] = total_month_sales
            json.dump(restaurant,f,encoding='utf-8',ensure_ascii=False)
            f.write('\n')
            yield restaurant

    def errback_httpbin(self,failure):
        request = failure.request
        reqUrl = request.url
        response = failure.value.response

        if eleSpd.reqRetryDict.has_key(reqUrl):
            eleSpd.reqRetryDict[reqUrl] += 1
            if eleSpd.reqRetryDict[reqUrl] == eleSpd.retry:
                #self.logger.error('Get data from %s failed', reqUrl)
                elog.error('Get data from %s failed', reqUrl)
                eleSpd.reqFauledList.remove(reqUrl)
        else:
            eleSpd.reqRetryDict[reqUrl] = 0
            eleSpd.reqFauledList.append(reqUrl)

        #self.logger.error('Get data from %s failed', reqUrl)

        #with codecs.open(eleSpd.failurefile, 'ab', 'utf-8') as f:
        #    print>>f,failure
        #    f.write('\n')

        # submit failed jobs
        #elog.error('Retry the %d time on url: %s',eleSpd.reqRetryDict[reqUrl]+1, reqUrl)
        #time.sleep(1)
        #return scrapy.Request(url=reqUrl,callback=self.parse_shop,errback=self.errback_httpbin)

        #if failure.check(HttpError):
        #    self.logger.error('HttpError on %s', reqUrl)
        #elif failure.check(DNSLookupError):
        #    self.logger.error('DNSLookupError on %s', reqUrl)
        #elif failure.check(TimeoutError, TCPTimedOutError):
        #    self.logger.error('TimeoutError on %s', reqUrl)
