from scrapy import Spider


class DomainPipelineSpider(Spider):
    pipeline_domain: str | None = None

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)

        common_item_pipelines = settings.getdict("COMMON_ITEM_PIPELINES")
        domain_item_pipelines = settings.getdict("DOMAIN_ITEM_PIPELINES")

        domain_pipelines = {}
        if cls.pipeline_domain is not None:
            domain_pipelines = domain_item_pipelines.get(cls.pipeline_domain, {})

        spider_item_pipelines = {}
        custom_settings = getattr(cls, "custom_settings", None)
        if isinstance(custom_settings, dict):
            spider_item_pipelines = custom_settings.get("ITEM_PIPELINES", {})

        merged_pipelines = {}
        merged_pipelines.update(common_item_pipelines)
        merged_pipelines.update(domain_pipelines)
        merged_pipelines.update(spider_item_pipelines)

        settings.set("ITEM_PIPELINES", merged_pipelines, priority="spider")
