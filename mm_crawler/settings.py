
BOT_NAME = "mm_crawler"

SPIDER_MODULES = ["mm_crawler.spiders"]
NEWSPIDER_MODULE = "mm_crawler.spiders"

LOG_LEVEL = 'INFO'

# 중복 방지 - 동일한 URL로 요청이 여러 번 가지 않도록 설정
DUPEFILTER_CLASS = 'scrapy.dupefilters.RFPDupeFilter'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "market_mind (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False 

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# In DOWNLOAD_HANDLERS, we specify that we’ll want to use the Scrapy Playwright request handlers 
# for both our http and https requests.

# Disable the scrapy-playwright download handler
# DOWNLOAD_HANDLERS = {
#     "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#     "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
# }

# PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = (
#     30 * 1000
# )

# PLAYWRIGHT_BROWSER_TYPE = "chromium"
# PLAYWRIGHT_LAUNCH_OPTIONS = {
#     "headless": False,
# } 

# Disable the Scrapy User-Agent middleware
DOWNLOADER_MIDDLEWARES = {
    'mm_crawler.middlewares.NaverDelayMiddleware': 543,
    'scrapy.downloadermiddlewares.autothrottle.AutoThrottleMiddleware': 500,
    # 'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    # 'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    # 'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
    # 'scrapy_fake_useragent.middleware.RetryUserAgentMiddleware': 401,
}

# FAKEUSERAGENT_PROVIDERS = [
#     'scrapy_fake_useragent.providers.FakeUserAgentProvider',
#     'scrapy_fake_useragent.providers.FakerProvider',  
#     'scrapy_fake_useragent.providers.FixedUserAgentProvider',
# ]

# 2024-05-15 13:59:43 [scrapy.downloadermiddlewares.robotstxt] DEBUG: Forbidden by robots.txt: <GET https://finance.naver.com/item/news.naver?code=060310>
ROBOTSTXT_OBEY = False

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "market_mind.middlewares.LanguageCrawlerSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "market_mind.middlewares.LanguageCrawlerDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    "market_mind.pipelines.FinanceNewsListPipeline": 1,
# }

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
"""
AUTOTHROTTLE_ENABLED: AutoThrottle을 활성화합니다.
AUTOTHROTTLE_START_DELAY: 초기 요청 간격을 설정합니다.
AUTOTHROTTLE_MAX_DELAY: 서버가 느리게 응답하면 최대 지연 시간을 설정합니다.
AUTOTHROTTLE_TARGET_CONCURRENCY: 서버와 동시 연결 수를 설정합니다.
AUTOTHROTTLE_DEBUG: 활성화하면 디버깅 정보를 로그에 표시합니다.
"""
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 10.0
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
