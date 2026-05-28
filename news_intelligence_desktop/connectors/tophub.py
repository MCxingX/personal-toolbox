"""TopHubData 热榜数据连接器."""

from __future__ import annotations

import logging
from news_intelligence_desktop.connectors import BaseConnector, FetchResult

logger = logging.getLogger(__name__)


class TopHubConnector(BaseConnector):
    """TopHubData 热榜数据连接器.

    API 文档: https://www.tophubdata.com/documentation
    每日限制: 1000 次（免费）
    """

    BASE = "https://api.tophubdata.com/v1"

    def __init__(self, api_key: str):
        """初始化连接器.

        Args:
            api_key: TopHubData API Key（由用户在设置中配置）
        """
        super().__init__()
        self.api_key = api_key

    def fetch_hot_lists(self) -> FetchResult:
        """获取全部榜单列表.

        Returns:
            FetchResult: 包含所有可用榜单的列表
        """
        try:
            import json
            url = f"{self.BASE}/getAllLists"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            code, text, ms = self._get_text(url, headers=headers)
            if code != 200:
                return FetchResult(False, [], f"HTTP {code}", ms)

            data = json.loads(text)
            if data.get("code") != 200:
                return FetchResult(False, [], data.get("message", "Unknown error"), ms)

            lists = data.get("data", [])
            results = []
            for item in lists:
                results.append({
                    "list_id": item.get("listId"),
                    "title": item.get("title"),
                    "description": item.get("description"),
                    "source": item.get("sourceName"),
                    "url": item.get("url"),
                    "icon": item.get("iconUrl"),
                })

            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))

    def fetch_list_items(self, list_id: str, limit: int = 30) -> FetchResult:
        """获取指定榜单的详细内容.

        Args:
            list_id: 榜单 ID
            limit: 返回条目数量限制

        Returns:
            FetchResult: 包含榜单详细内容的列表
        """
        try:
            import json
            from urllib.parse import quote
            url = f"{self.BASE}/getListItems?listId={quote(list_id)}&limit={limit}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            code, text, ms = self._get_text(url, headers=headers)
            if code != 200:
                return FetchResult(False, [], f"HTTP {code}", ms)

            data = json.loads(text)
            if data.get("code") != 200:
                return FetchResult(False, [], data.get("message", "Unknown error"), ms)

            items = data.get("data", [])
            results = []
            for item in items:
                results.append({
                    "title": item.get("title", ""),
                    "summary": item.get("description", ""),
                    "url": item.get("url", ""),
                    "source_name": item.get("sourceName", "TopHub"),
                    "source_url": item.get("sourceUrl", ""),
                    "published_at": item.get("createTime", ""),
                    "hot_value": item.get("hotValue", 0),
                    "category": "hot",
                    "language": "zh",
                })

            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))
