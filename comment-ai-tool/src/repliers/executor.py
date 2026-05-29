"""回复执行器 — 各平台回复发送

每个平台有独立的发送逻辑，统一接口。
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ReplyExecutor:
    """跨平台回复执行器"""

    async def send_reply(
        self,
        platform: str,
        comment_id: str,
        content: str,
        config: dict,
        account=None,
    ) -> bool:
        """发送回复到指定平台

        Returns:
            True 成功, False 失败
        """
        try:
            if platform == "douyin":
                return await self._reply_douyin(comment_id, content, config)
            elif platform == "xiaohongshu":
                return await self._reply_xiaohongshu(comment_id, content, config)
            elif platform == "wechat_video":
                return await self._reply_wechat_video(comment_id, content, config)
            elif platform == "bilibili":
                return await self._reply_bilibili(comment_id, content, config)
            else:
                logger.warning(f"不支持的回复平台: {platform}")
                return False
        except Exception as e:
            logger.error(f"[{platform}] 回复发送异常: {e}")
            return False

    async def _reply_douyin(self, comment_id: str, content: str, config: dict) -> bool:
        """抖音回复 — 开放平台 comment/reply"""
        import httpx
        access_token = config.get("access_token", "")
        if not access_token:
            logger.warning("抖音: 无 access_token")
            return False

        url = "https://open.douyin.com/api/douyin/v1/comment/reply/"
        headers = {"access-token": access_token, "Content-Type": "application/json"}
        body = {"comment_id": comment_id, "text": content}
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(url, headers=headers, json=body)
                data = r.json()
                if data.get("status_code") == 0:
                    logger.info(f"抖音回复成功: {comment_id}")
                    return True
                else:
                    logger.error(f"抖音回复失败: {data.get('description')}")
                    return False
        except Exception as e:
            logger.error(f"抖音回复请求异常: {e}")
            return False

    async def _reply_xiaohongshu(self, comment_id: str, content: str, config: dict) -> bool:
        """小红书回复 — Web API"""
        import httpx
        cookie = config.get("cookie", "")
        if not cookie:
            logger.warning("小红书: 无 cookie")
            return False

        url = "https://edith.xiaohongshu.com/api/sns/web/v1/comment/post"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Origin": "https://www.xiaohongshu.com",
            "Referer": "https://www.xiaohongshu.com/",
            "Cookie": cookie,
            "Content-Type": "application/json",
        }
        # note_id 需要从 comment_id 关联获取，这里简化处理
        body = {"content": content, "comment_id": comment_id}
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(url, headers=headers, json=body)
                data = r.json()
                if data.get("code") == 0:
                    logger.info(f"小红书回复成功: {comment_id}")
                    return True
                else:
                    logger.error(f"小红书回复失败: {data.get('msg')}")
                    return False
        except Exception as e:
            logger.error(f"小红书回复请求异常: {e}")
            return False

    async def _reply_wechat_video(self, comment_id: str, content: str, config: dict) -> bool:
        """视频号回复 — 需要先获取 access_token"""
        import httpx
        import time
        appid = config.get("appid", "")
        secret = config.get("secret", "")
        if not appid or not secret:
            logger.warning("视频号: 无 appid/secret")
            return False

        # 获取 token
        token_url = "https://api.weixin.qq.com/cgi-bin/token"
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(token_url, params={
                    "grant_type": "client_credential", "appid": appid, "secret": secret,
                })
                token_data = r.json()
                if "access_token" not in token_data:
                    logger.error(f"视频号token获取失败: {token_data}")
                    return False
                access_token = token_data["access_token"]
        except Exception as e:
            logger.error(f"视频号token请求异常: {e}")
            return False

        # 发送回复
        url = f"https://api.weixin.qq.com/channels/comment/reply?access_token={access_token}"
        body = {"comment_id": comment_id, "content": content}
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(url, json=body)
                data = r.json()
                if data.get("errcode", 0) == 0:
                    logger.info(f"视频号回复成功: {comment_id}")
                    return True
                else:
                    logger.error(f"视频号回复失败: {data.get('errmsg')}")
                    return False
        except Exception as e:
            logger.error(f"视频号回复请求异常: {e}")
            return False

    async def _reply_bilibili(self, rpid: str, content: str, config: dict) -> bool:
        """B站回复 — x/v2/reply/reply"""
        import httpx
        cookie = config.get("cookie", "")
        csrf = config.get("csrf", "")
        oid = config.get("oid")  # 视频 avid

        if not cookie or not csrf or not oid:
            logger.warning("B站: 缺少 cookie/csrf/oid")
            return False

        url = "https://api.bilibili.com/x/v2/reply/reply"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com/",
            "Cookie": cookie,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        import urllib.parse
        body = urllib.parse.urlencode({
            "oid": oid,
            "type": 1,
            "root": rpid,
            "parent": rpid,
            "message": content,
            "csrf": csrf,
        })
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(url, headers=headers, content=body)
                data = r.json()
                if data.get("code") == 0:
                    logger.info(f"B站回复成功: rpid={rpid}")
                    return True
                else:
                    logger.error(f"B站回复失败: code={data.get('code')} msg={data.get('message')}")
                    return False
        except Exception as e:
            logger.error(f"B站回复请求异常: {e}")
            return False
