import logging

from mm_crawler.orchestration.cli import run_orchestrator_cli


logger = logging.getLogger(__name__)


def run_poll_loop() -> None:
    logger.info("orchestrator.py is deprecated, forwarding to orchestration.cli")
    run_orchestrator_cli()


if __name__ == "__main__":
    run_poll_loop()
