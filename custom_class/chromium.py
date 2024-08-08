# -*- coding: utf-8 -*-

"""
Custom ChromiumLoader Module
"""

import asyncio
import time
from typing import Iterator

from langchain_core.documents import Document

from scrapegraphai.utils import get_logger
from scrapegraphai.docloaders.chromium import ChromiumLoader

logger = get_logger("web-loader")


class MyChromiumLoader(ChromiumLoader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def ascrape_playwright(self, url: str) -> str:
        from playwright.async_api import async_playwright
        from undetected_playwright import Malenia

        print("Starting scraping...")
        results = ""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless, proxy=self.proxy, **self.browser_config
            )
            try:
                context = await browser.new_context()
                await Malenia.apply_stealth(context)
                page = await context.new_page()
                await page.goto(url, wait_until="load")
                await page.wait_for_load_state(state="load")
                await page.wait_for_timeout(5000)
                results = await page.content()
                print("Content scraped")
            except Exception as e:
                results = f"Error: {e}"
            await browser.close()
        return results

    def lazy_load(self) -> Iterator[Document]:
        scraping_fn = getattr(self, f"ascrape_{self.backend}")

        for url in self.urls:
            fun_ = scraping_fn(url)
            html_content = asyncio.run(fun_)
            metadata = {"source": url}
            yield Document(page_content=html_content, metadata=metadata)
