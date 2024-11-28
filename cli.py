import os
from collections import OrderedDict, defaultdict
from datetime import datetime
from typing import List

import click

# Assuming parse_res, create_res_file_mapping, create_pydantic_model, and create_msgspec_model_for_websocket are defined elsewhere in the file

@click.group()
def cli():
    """Main CLI group."""
    pass

@cli.group()
def mm_xing(): ...

@mm_xing.command()
@click.argument('task', type=click.Choice(['create_pydantic_model', 'create_msgspec_model_for_websocket']))
@click.option('--path', default='./res', help='The default xing api res file path.')
def res_converter(task, path):
    """Perform tasks related to res conversion."""
    from mm_xing.res_converter import (create_msgspec_model_for_websocket,
                                       create_pydantic_model,
                                       create_res_file_mapping, parse_res)

    res_file_paths = [
        os.path.join(path, file_name)
        for file_name in os.listdir(path)
        if os.path.isfile(os.path.join(path, file_name)) and "_" not in file_name
    ]
    res_rows = [parse_res(path) for path in res_file_paths]
    res_map = create_res_file_mapping(res_rows)

    res_code = sorted(res_map.keys())
    res_infos = [res_map[name] for name in res_code]

    if task == "create_pydantic_model":
        create_pydantic_model(res_infos=res_infos)
    elif task == "create_msgspec_model_for_websocket":
        create_msgspec_model_for_websocket(res_infos=res_infos)

@cli.group()
def mm_llm(): ...


from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import defer, reactor


@cli.group()
def mm_crawler(): 
    os.environ["SCRAPY_PROJECT"] = "mm_crawler"
    os.environ["SCRAPY_SETTINGS_MODULE"] = "mm_crawler.settings"

@mm_crawler.command()
@click.argument('spider_name')
@click.option('--arg', '-a', multiple=True, type=(str, str), help='Additional arguments for the spider in key=value format.')
def run_spider_with_runner(spider_name, arg):
    """Scrapy spider를 CrawlerRunner를 사용하여 추가 인자와 함께 실행합니다.

    사용 예:
    python cli.py run_spider_with_runner my_spider --arg key1 value1 --arg key2 value2
    """
    os.environ["SCRAPY_PROJECT"] = "mm_crawler"
    os.environ["SCRAPY_SETTINGS_MODULE"] = "mm_crawler.settings"
    runner = CrawlerRunner(get_project_settings())
    
    # Convert the list of tuples into a dictionary
    additional_args = {key: value for key, value in arg}
    
    @defer.inlineCallbacks
    def crawl():
        yield runner.crawl(spider_name, **additional_args)
        reactor.stop() # type: ignore
    
    crawl()
    reactor.run() # type: ignore

@mm_crawler.command()
@click.argument('spider_name')
@click.option('--arg', '-a', multiple=True, type=(str, str), help='Additional arguments for the spider in key=value format.')
def run_spider_with_process(spider_name, arg):
    """
    Run a Scrapy spider with additional arguments.

    Usage:
    python cli.py run_spider <spider_name> --arg <key1> <value1> --arg <key2> <value2>

    Parameters:
    spider_name: The name of the Scrapy spider to run.
    arg: Additional arguments for the spider in key=value format, passed as multiple --arg options.

    Example:
    To run a spider named 'my_spider' with additional arguments 'key1=value1' and 'key2=value2', use:
    python cli.py run_spider my_spider --arg key1 value1 --arg key2 value2
    """
    import sys
    # Check if the correct reactor is already installed
    if 'twisted.internet.reactor' not in sys.modules:
        from twisted.internet import asyncioreactor
        asyncioreactor.install()

    process = CrawlerProcess(get_project_settings())
    
    # Convert the list of tuples into a dictionary
    additional_args = {key: value for key, value in arg}
    
    process.crawl(spider_name, **additional_args)
    process.start()




if __name__ == "__main__":
    cli()