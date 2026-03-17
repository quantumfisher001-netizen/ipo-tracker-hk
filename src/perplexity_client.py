# -*- coding: utf-8 -*-
"""
Perplexity Sonar API 客户端
封装 Perplexity API 调用，支持实时联网搜索
"""

import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
DEFAULT_MODEL = "sonar"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


class PerplexityClient:
    """Perplexity Sonar API 客户端"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("PPLX_API_KEY")
        if not self.api_key:
            raise ValueError("未找到 PPLX_API_KEY，请设置环境变量或传入 api_key 参数")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def search(
        self,
        query: str,
        system_prompt: str = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 1024,
    ) -> dict:
        """
        执行搜索查询

        Args:
            query: 搜索查询内容
            system_prompt: 系统提示词
            model: 使用的模型，默认为 sonar
            max_tokens: 最大返回 token 数

        Returns:
            包含搜索结果的字典
        """
        if system_prompt is None:
            system_prompt = (
                "你是一个专业的香港金融市场分析师，专注于IPO市场动态。"
                "请用中文回答，提供准确、简洁的信息。"
                "如果信息不确定，请明确说明。"
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug("正在查询 Perplexity API（第 %d 次尝试）：%s", attempt, query[:80])
                response = self.session.post(
                    PERPLEXITY_API_URL, json=payload, timeout=60
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                citations = data.get("citations", [])
                logger.debug("查询成功，返回 %d 字符", len(content))
                return {
                    "success": True,
                    "content": content,
                    "citations": citations,
                    "query": query,
                }
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response is not None else None
                logger.warning("HTTP 错误 %s（第 %d 次尝试）：%s", status_code, attempt, e)
                if status_code in (401, 403):
                    # 认证错误，不重试
                    return {
                        "success": False,
                        "error": f"API 认证失败（{status_code}），请检查 PPLX_API_KEY",
                        "query": query,
                    }
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
            except requests.exceptions.Timeout:
                logger.warning("请求超时（第 %d 次尝试）", attempt)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
            except requests.exceptions.RequestException as e:
                logger.warning("网络错误（第 %d 次尝试）：%s", attempt, e)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
            except (KeyError, IndexError, ValueError) as e:
                logger.error("解析 API 响应失败：%s", e)
                return {
                    "success": False,
                    "error": f"解析响应失败：{e}",
                    "query": query,
                }

        return {
            "success": False,
            "error": f"重试 {MAX_RETRIES} 次后仍然失败",
            "query": query,
        }

    def batch_search(self, queries: list, delay: float = 1.0) -> list:
        """
        批量执行搜索，控制请求频率

        Args:
            queries: 查询列表，每项为 dict 包含 'query' 和可选的 'system_prompt'
            delay: 每次请求之间的延迟秒数（控制成本和速率）

        Returns:
            搜索结果列表
        """
        results = []
        for i, q in enumerate(queries):
            if i > 0:
                time.sleep(delay)
            if isinstance(q, str):
                result = self.search(q)
            else:
                result = self.search(
                    query=q.get("query", ""),
                    system_prompt=q.get("system_prompt"),
                    max_tokens=q.get("max_tokens", 1024),
                )
            results.append(result)
        return results
