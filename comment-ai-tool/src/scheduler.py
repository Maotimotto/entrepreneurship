"""定时轮询调度器

串联：Monitor 拉评论 → Analyzer 意图分析 → Replier 生成回复 → Executor 发送回复
APScheduler 驱动，按配置间隔循环执行。
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from config.settings import settings
from src.core.database import AccountStore, AnalysisLogStore, ReplyLogStore, LeadStore
from src.models.comment import Comment, Platform
from src.analyzers.intent_analyzer import IntentAnalyzer
from src.repliers.reply_generator import ReplyGenerator
from src.repliers.executor import ReplyExecutor

logger = logging.getLogger(__name__)


class CommentScheduler:
    """评论轮询调度器"""

    def __init__(self):
        self.analyzer = IntentAnalyzer()
        self.replier = ReplyGenerator()
        self.executor = ReplyExecutor()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def _build_monitor(self, account):
        """根据平台类型构建 Monitor 实例"""
        config = {}
        if account.config:
            try:
                config = json.loads(account.config)
            except json.JSONDecodeError:
                pass

        platform = account.platform
        if platform == "douyin":
            from src.monitors.douyin_monitor import DouyinMonitor
            return DouyinMonitor(
                access_token=config.get("access_token", settings.douyin_access_token),
            )
        elif platform == "xiaohongshu":
            from src.monitors.xiaohongshu_monitor import XiaohongshuMonitor
            return XiaohongshuMonitor(
                cookie=config.get("cookie", settings.xhs_cookie),
            )
        elif platform == "wechat_video":
            from src.monitors.wechat_video_monitor import WechatVideoMonitor
            return WechatVideoMonitor(
                appid=config.get("appid", settings.wechat_appid),
                secret=config.get("secret", settings.wechat_secret),
            )
        elif platform == "bilibili":
            from src.monitors.bilibili_monitor import BilibiliMonitor
            return BilibiliMonitor(
                cookie=config.get("cookie", settings.bilibili_cookie),
                csrf=config.get("csrf", settings.bilibili_csrf),
            )
        else:
            logger.warning(f"未知平台: {platform}")
            return None

    async def poll_and_analyze(self):
        """单次轮询：拉评论 → 分析 → 生成回复 → 入队待发"""
        accounts = await AccountStore.list_all(status="active")
        if not accounts:
            logger.debug("无活跃账号，跳过轮询")
            return

        total_comments = 0
        total_leads = 0
        total_replies = 0

        for account in accounts:
            monitor = self._build_monitor(account)
            if not monitor:
                continue

            # 从 config 获取要监控的内容ID列表
            config = {}
            if account.config:
                try:
                    config = json.loads(account.config)
                except json.JSONDecodeError:
                    pass

            # 不同平台的监控目标
            content_ids = config.get("content_ids", [])
            if not content_ids:
                logger.debug(f"[{account.account_name}] 无监控内容ID，跳过")
                continue

            # 拉评论
            try:
                comments = await monitor.fetch_comments(content_ids[0])
            except Exception as e:
                logger.error(f"[{account.account_name}] 拉取评论失败: {e}")
                continue

            total_comments += len(comments)

            for comment in comments:
                # 意图分析
                try:
                    score = await self.analyzer.analyze(comment)
                except Exception as e:
                    logger.error(f"[{account.account_name}] 分析失败: {e}")
                    continue

                # 生成回复
                reply_content = ""
                if score.score >= settings.min_lead_score:
                    try:
                        reply_content = await self.replier.generate(comment, score)
                    except Exception as e:
                        logger.error(f"[{account.account_name}] 回复生成失败: {e}")

                # 存分析日志
                await AnalysisLogStore.save({
                    "platform_account_id": account.id,
                    "platform": account.platform,
                    "comment_id": comment.id,
                    "comment_content": comment.content,
                    "author_id": comment.author_id,
                    "author_name": comment.author_name,
                    "post_id": comment.post_id,
                    "post_title": comment.post_title,
                    "score": score.score,
                    "intent": score.intent,
                    "urgency": score.urgency,
                    "keywords": json.dumps(score.keywords),
                    "reply_content": reply_content,
                    "replied": bool(reply_content),
                })

                # 高意向存潜客
                if score.score >= settings.min_lead_score:
                    await LeadStore.save({
                        "platform_account_id": account.id,
                        "platform": account.platform,
                        "author_id": comment.author_id,
                        "author_name": comment.author_name,
                        "first_comment_content": comment.content,
                        "lead_score": score.score,
                        "tags": json.dumps(score.keywords),
                    })
                    total_leads += 1

                # 有待回复的入队
                if reply_content:
                    await ReplyLogStore.save({
                        "platform_account_id": account.id,
                        "platform": account.platform,
                        "comment_id": comment.id,
                        "reply_content": reply_content,
                        "status": "pending",
                    })
                    total_replies += 1

        if total_comments > 0:
            logger.info(f"轮询完成: {total_comments} 评论 → {total_leads} 潜客 → {total_replies} 待回复")

    async def execute_pending_replies(self):
        """执行待发送的回复"""
        pending, _ = await ReplyLogStore.list_all(status="pending", limit=50)
        if not pending:
            return

        sent = 0
        failed = 0
        for reply_log in pending:
            account = await AccountStore.get(reply_log.platform_account_id)
            if not account or account.status != "active":
                continue

            config = {}
            if account.config:
                try:
                    config = json.loads(account.config)
                except json.JSONDecodeError:
                    pass

            ok = await self.executor.send_reply(
                platform=reply_log.platform,
                comment_id=reply_log.comment_id,
                content=reply_log.reply_content,
                config=config,
                account=account,
            )

            if ok:
                await ReplyLogStore.save({
                    "id": reply_log.id,
                    "status": "sent",
                })
                # 更新分析日志的回复状态
                sent += 1
            else:
                failed += 1

        if sent or failed:
            logger.info(f"回复执行: {sent} 成功, {failed} 失败")

    async def _run_loop(self):
        """主循环"""
        interval = settings.check_interval_seconds
        logger.info(f"调度器启动，轮询间隔 {interval}s")

        while self._running:
            try:
                await self.poll_and_analyze()
                await self.execute_pending_replies()
            except Exception as e:
                logger.error(f"调度器异常: {e}", exc_info=True)

            await asyncio.sleep(interval)

    def start(self):
        """启动调度器（后台任务）"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("调度器已启动")

    def stop(self):
        """停止调度器"""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("调度器已停止")

    @property
    def is_running(self) -> bool:
        return self._running


# 全局实例
scheduler = CommentScheduler()
