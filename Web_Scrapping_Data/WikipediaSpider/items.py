import scrapy

class Disease(scrapy.Item):
    # Define the fields for your item here
    name = scrapy.Field()
    url = scrapy.Field()
    description = scrapy.Field()
    symptoms = scrapy.Field()
    diagnosis = scrapy.Field()
    category = scrapy.Field()