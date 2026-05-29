"""MarkItDown 内容摄入器

将多格式文件统一转为 Markdown，供 LLM 生成视频脚本。
支持：PDF / Word / PPT / Excel / 图片 / 音频 / HTML / YouTube
"""
import logging
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    """摄入结果"""
    source_path: str
    markdown: str = ""
    title: str = ""
    success: bool = True
    error: str = ""


class ContentIngestor:
    """多格式内容 → Markdown 转换器"""

    def __init__(self):
        self._md = None

    def _get_converter(self):
        """延迟加载 MarkItDown"""
        if self._md is None:
            try:
                from markitdown import MarkItDown
                self._md = MarkItDown()
                logger.info("MarkItDown 已加载")
            except ImportError:
                logger.error("markitdown 未安装: pip install markitdown")
                raise
        return self._md

    def ingest_file(self, file_path: str, title: str = "") -> IngestResult:
        """摄入单个文件

        Args:
            file_path: 文件路径（本地路径或 URL）
            title: 可选标题
        """
        path = Path(file_path)

        if not path.exists():
            return IngestResult(
                source_path=file_path,
                success=False,
                error=f"文件不存在: {file_path}",
            )

        try:
            md = self._get_converter()
            result = md.convert(file_path)

            return IngestResult(
                source_path=file_path,
                markdown=result.markdown if hasattr(result, 'markdown') else str(result),
                title=title or path.stem,
                success=True,
            )
        except Exception as e:
            logger.error(f"文件摄入失败 {file_path}: {e}")
            return IngestResult(
                source_path=file_path,
                success=False,
                error=str(e),
            )

    def ingest_directory(self, dir_path: str, extensions: list[str] = None) -> list[IngestResult]:
        """批量摄入目录下的文件

        Args:
            dir_path: 目录路径
            extensions: 文件扩展名过滤，如 [".pdf", ".docx"]
        """
        path = Path(dir_path)
        if not path.is_dir():
            return [IngestResult(source_path=dir_path, success=False, error="不是目录")]

        if extensions is None:
            extensions = [".pdf", ".docx", ".pptx", ".xlsx", ".html", ".htm", ".txt", ".md"]

        results = []
        for f in sorted(path.rglob("*")):
            if f.is_file() and f.suffix.lower() in extensions:
                result = self.ingest_file(str(f))
                results.append(result)

        logger.info(f"目录摄入完成: {len(results)} 个文件, {sum(1 for r in results if r.success)} 成功")
        return results

    def ingest_url(self, url: str) -> IngestResult:
        """摄入 URL 内容（YouTube / 网页等）"""
        try:
            md = self._get_converter()
            result = md.convert(url)
            return IngestResult(
                source_path=url,
                markdown=result.markdown if hasattr(result, 'markdown') else str(result),
                title=url.split("/")[-1][:50],
                success=True,
            )
        except Exception as e:
            logger.error(f"URL 摄入失败 {url}: {e}")
            return IngestResult(source_path=url, success=False, error=str(e))

    def ingest_to_obsidian(
        self,
        file_path: str,
        vault_path: str,
        subfolder: str = "创业/09-素材库",
        title: str = "",
    ) -> IngestResult:
        """摄入文件并保存到 Obsidian 知识库

        Args:
            file_path: 源文件路径
            vault_path: Obsidian vault 根路径
            subfolder: vault 内子目录
            title: 笔记标题
        """
        result = self.ingest_file(file_path, title)
        if not result.success:
            return result

        # 构建 Obsidian 笔记路径
        note_dir = os.path.join(vault_path, subfolder)
        os.makedirs(note_dir, exist_ok=True)

        note_name = result.title.replace("/", "_").replace("\\", "_") + ".md"
        note_path = os.path.join(note_dir, note_name)

        # 写入 Obsidian 笔记
        content = f"# {result.title}\n\n"
        content += f"> 来源: `{result.source_path}`\n\n"
        content += "---\n\n"
        content += result.markdown

        with open(note_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"已保存到 Obsidian: {note_path}")
        return result


# 全局实例
content_ingestor = ContentIngestor()
