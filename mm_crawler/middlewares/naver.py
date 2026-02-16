import time

from scrapy.downloadermiddlewares.retry import RetryMiddleware


class NaverDelayMiddleware(RetryMiddleware):
    def __init__(self, delay=0.5):
        self.delay = delay

    @classmethod
    def from_crawler(cls, crawler):
        return cls(delay=crawler.settings.getfloat("NAVER_DELAY"))

    def process_request(self, request, spider):
        print(f"[Middleware] request.url: {request.url}")
        if "finance.naver.com" in request.url and request.meta.get("delay") is not None:
            time.sleep(self.delay)
        return None

    def process_response(self, request, response, spider):
        if response.status in [429, 503]:
            print(
                "[Middleware] Too Many Requests or Service Unavailable. Sleep 10 seconds."
            )
            time.sleep(1)
            request.meta["download_slot"] = "slow-server"
            return (
                self._retry(request, f"Response status: {response.status}", spider)
                or response
            )
        request.meta["download_slot"] = "fast-server"
        return response

    def spider_opened(self, spider):
        spider.logger.info("[Middleware] Spider opened: %s" % spider.name)
