"""抖音评论监控器 — Playwright 浏览器模拟

启动真实 Chromium，自动处理 X-Bogus 签名。
通过拦截 API 响应获取评论数据。
"""
import asyncio
import json
import logging
import re
from datetime import datetime
from typing import AsyncGenerator, Optional
from src.models.comment import Comment, Platform

logger = logging.getLogger(__name__)


class DouyinBrowserMonitor:
    """抖音 Playwright 浏览器监控"""

    PLATFORM = Platform.DOUYIN
    COMMENT_API = "aweme/v1/web/comment/list/"

    def __init__(self, cookie: str = ""):
        self.cookie = cookie
        self._browser = None
        self._context = None
        self._running = False

    async def _ensure_browser(self):
        """确保浏览器已启动"""
        if self._browser:
            return
        from playwright.async_api import async_playwright
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=True)

        # 解析 cookie 字符串 → Playwright 格式
        cookies = self._parse_cookies(self.cookie)

        self._context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )
        if cookies:
            await self._context.add_cookies(cookies)
        logger.info("抖音: Chromium 已启动")

    def _parse_cookies(self, cookie_str: str) -> list[dict]:
        """解析 cookie 字符串"""
        cookies = []
        if not cookie_str:
            return cookies
        for item in cookie_str.split(";"):
            item = item.strip()
            if "=" in item:
                name, value = item.split("=", 1)
                cookies.append({
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": ".douyin.com",
                    "path": "/",
                })
        return cookies

    async def fetch_comments(self, aweme_id: str) -> list[Comment]:
        """通过浏览器拦截获取评论"""
        await self._ensure_browser()

        page = await self._context.new_page()
        captured_comments = []

        # 拦截评论 API 响应
        async def handle_response(response):
            if self.COMMENT_API in response.url:
                try:
                    data = await response.json()
                    if data.get("status_code") == 0:
                        for item in data.get("comments", []):
                            comment = self._parse_comment(item, aweme_id)
                            if comment:
                                captured_comments.append(comment)
                        logger.info(f"抖音: 拦截到 {len(captured_comments)} 条评论")
                except Exception as e:
                    logger.debug(f"抖音: 响应解析跳过: {e}")

        page.on("response", handle_response)

        try:
            # 访问视频页，触发评论加载
            url = f"https://www.douyin.com/video/{aweme_id}"
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # 等待评论区加载
            await page.wait_for_timeout(5000)

            # 滚动触发更多评论加载
            for _ in range(2):
                await page.evaluate("window.scrollBy(0, 800)")
                await page.wait_for_timeout(1500)

        except Exception as e:
            logger.error(f"抖音: 页面加载异常: {e}")
        finally:
            await page.close()

        # 去重
        seen = set()
        unique = []
        for c in captured_comments:
            if c.id not in seen:
                seen.add(c.id)
                unique.append(c)

        logger.info(f"抖音: 去重后 {len(unique)} 条评论 (aweme={aweme_id})")
        return unique

    def _parse_comment(self, item: dict, aweme_id: str) -> Optional[Comment]:
        """解析单条评论"""
        try:
            cid = str(item.get("cid", ""))
            user = item.get("user", {})
            return Comment(
                id=cid,
                platform=Platform.DOUYIN,
                content=item.get("text", ""),
                author_id=str(user.get("uid", "")),
                author_name=user.get("nickname", ""),
                author_avatar=user.get("avatar_thumb", {}).get("url_list", [None])[0],
                post_id=aweme_id,
                post_title="",
                likes=item.get("digg_count", 0),
                created_at=datetime.fromtimestamp(item.get("create_time", 0)),
                raw_data=item,
            )
        except Exception as e:
            logger.debug(f"抖音: 评论解析跳过: {e}")
            return None

    async def poll_comments(self, aweme_ids: list[str], interval: int = 300) -> AsyncGenerator[Comment, None]:
        """持续轮询"""
        self._running = True
        seen = set()
        while self._running:
            for aid in aweme_ids:
                comments = await self.fetch_comments(aid)
                for c in comments:
                    if c.id not in seen:
                        seen.add(c.id)
                        yield c
            await asyncio.sleep(interval)

    async def close(self):
        """关闭浏览器"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()
        self._browser = None
        self._context = None
        self._pw = None
        logger.info("抖音: Chromium 已关闭")

    def stop(self):
        self._running = False
