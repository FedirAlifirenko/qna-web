import asyncio
import logging
from typing import Generator

import typer
from bs4 import BeautifulSoup
from langchain_community.document_loaders import AsyncChromiumLoader
from yarl import URL

logger = logging.getLogger(__name__)


class Crawler:

    def __init__(self, start_url: URL, max_seen_urls: int) -> None:
        self.start_url = start_url
        if not start_url.host:
            raise ValueError("Invalid start_url")
        self.start_url_host = start_url.host

        self.max_seen_urls = max_seen_urls
        self.urls_queue: set[str] = set()
        self.seen_urls: set[str] = set()
        self.result_urls: list[str] = []
        self.supported_schemes = {"http", "https"}

    async def crawl(self) -> list[str]:
        logger.info(f"Starting crawler: {self.start_url=}, {self.max_seen_urls=}")
        self.urls_queue.add(str(self.start_url))
        loader = AsyncChromiumLoader([], headless=True)

        while self.urls_queue and (
            (url := self.urls_queue.pop())
            and url not in self.seen_urls
            and len(self.seen_urls) < self.max_seen_urls
        ):
            loader.urls = [url]
            logger.info(f"Loading {url=}")

            try:
                docs = await loader.aload()
            except Exception:
                logger.exception(f"Error while loading {url=}")
                continue

            self.seen_urls.add(url)
            self.result_urls.append(url)

            for doc in docs:
                try:
                    for href_url in self._extract_urls(doc.page_content):
                        self.urls_queue.add(str(href_url))
                except Exception:
                    logger.exception(f"Error while processing document {url=}")

        return self.result_urls

    def _extract_urls(self, html_text: str) -> Generator[str, None, None]:
        soup = BeautifulSoup(html_text, "html.parser")
        for link in soup.find_all("a"):
            href = link.get("href")
            if not href:
                continue

            try:
                href_url = URL(href)
            except Exception:
                logger.error(f"Bad url {href=}")
                continue

            if href_url.host is None and len(href_url.path) > 1:
                # handle relative urls
                href_url = self.start_url.with_path(href_url.path)

            if not self._is_subdomain(href_url):
                continue

            if href_url.scheme not in self.supported_schemes:
                continue

            if str(href_url) in self.seen_urls:
                continue

            yield str(href_url)

    def _is_subdomain(self, url: URL) -> bool:
        return str(url.host).endswith(self.start_url_host.lstrip("www."))


def save_urls(urls: list[str], filename: str) -> None:
    with open(filename, "w") as fp:
        fp.write("\n".join(urls))
    logger.info(f"Written {len(urls)} urls to {filename}")


def main(start_url: str, max_seen_urls: int = 10) -> None:
    crawler = Crawler(URL(start_url), max_seen_urls)
    loop = asyncio.get_event_loop()
    result_urls = loop.run_until_complete(crawler.crawl())

    save_urls(result_urls, f"{URL(start_url).host}-urls.txt")


def entrypoint() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    typer.run(main)


if __name__ == "__main__":
    entrypoint()
