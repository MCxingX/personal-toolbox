"""设置导入导出 - 支持 API Key 等配置的备份和迁移."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def export_settings(repo, output_path: str | Path | None = None) -> dict:
    """导出所有设置到 JSON 文件.

    导出内容：
    - app_settings 表中的所有设置（API Key 等）
    - 板块启用状态
    - 自定义 RSS 源
    - 数据保留策略配置

    Returns:
        导出的设置字典
    """
    settings = {}

    try:
        with repo.db.connect() as conn:
            # 1. 读取 app_settings
            rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
            settings["app_settings"] = {r["key"]: r["value"] for r in rows}

            # 2. 读取 source_configs（自定义源）
            rows = conn.execute(
                "SELECT * FROM source_configs WHERE name NOT IN (?, ?, ?, ?, ?, ?, ?, ?)"
                , ("Open-Meteo", "USGS Earthquake", "韩小韩 API", "GDELT", "DEV.to", "Lobsters", "CEIC地震台网", "百度新闻")
            ).fetchall()
            settings["custom_sources"] = [dict(r) for r in rows]

            # 3. 读取网页来源
            rows = conn.execute("SELECT * FROM web_page_sources").fetchall()
            settings["web_page_sources"] = [dict(r) for r in rows]

            # 4. 读取 uapi_fetch_log（平台状态）
            rows = conn.execute("SELECT * FROM uapi_fetch_log").fetchall()
            settings["uapi_fetch_log"] = {r["board_type"]: r["last_fetch_at"] for r in rows}

        # 元信息
        settings["_meta"] = {
            "exported_at": datetime.now().isoformat(),
            "version": "1.0",
            "description": "News Intelligence Desktop 设置备份",
        }

        # 写入文件
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            logger.info("设置已导出到: %s", output_path)

    except Exception as e:
        logger.warning("导出设置失败: %s", e)

    return settings


def import_settings(repo, input_path: str | Path) -> dict:
    """从 JSON 文件导入设置.

    导入策略：
    - 合并模式：已存在的 key 不覆盖，只添加新 key
    - 自定义源：检查去重后添加
    - 平台状态：恢复上次采集时间

    Returns:
        {"imported_keys": int, "imported_sources": int, "skipped": int}
    """
    results = {"imported_keys": 0, "imported_sources": 0, "skipped": 0}

    try:
        input_path = Path(input_path)
        if not input_path.exists():
            logger.warning("导入文件不存在: %s", input_path)
            return results

        with open(input_path, "r", encoding="utf-8") as f:
            settings = json.load(f)

        # 检查版本
        meta = settings.get("_meta", {})
        if meta.get("version") != "1.0":
            logger.warning("导入文件版本不匹配: %s", meta.get("version"))
            return results

        with repo.db.connect() as conn:
            # 1. 导入 app_settings（合并模式）
            existing = {r["key"] for r in conn.execute("SELECT key FROM app_settings").fetchall()}
            for key, value in settings.get("app_settings", {}).items():
                if key not in existing:
                    conn.execute(
                        "INSERT INTO app_settings(key, value) VALUES(?,?)",
                        (key, value),
                    )
                    results["imported_keys"] += 1
                else:
                    results["skipped"] += 1

            # 2. 导入自定义源
            for src in settings.get("custom_sources", []):
                name = src.get("name", "")
                if not name:
                    continue
                existing_src = conn.execute(
                    "SELECT id FROM source_configs WHERE name=?", (name,)
                ).fetchone()
                if not existing_src:
                    conn.execute(
                        """INSERT INTO source_configs(name, type, category, url, enabled, auth_type, auth_config, parse_rules)
                        VALUES(?,?,?,?,?,?,?,?)""",
                        (name, src.get("type", src.get("source_type", "api")), src.get("category", "news"),
                         src.get("url", ""), src.get("enabled", 1), src.get("auth_type", "none"),
                         src.get("auth_config", "{}"), src.get("parse_rules", "{}")),
                    )
                    results["imported_sources"] += 1

            # 3. 导入网页来源
            for src in settings.get("web_page_sources", []):
                name = src.get("name", "")
                url = src.get("url", "")
                if not name or not url:
                    continue
                existing_src = conn.execute(
                    "SELECT id FROM web_page_sources WHERE url=?", (url,)
                ).fetchone()
                if not existing_src:
                    conn.execute(
                        """INSERT INTO web_page_sources(name, url, url_pattern, title_selector, link_selector,
                        summary_selector, content_selector, date_selector, author_selector, item_selector,
                        use_xpath, encoding, max_items, remove_selectors, category, enabled)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (name, url, src.get("url_pattern", ""), src.get("title_selector", ""),
                         src.get("link_selector", "a[href]"), src.get("summary_selector", ""),
                         src.get("content_selector", ""), src.get("date_selector", ""),
                         src.get("author_selector", ""), src.get("item_selector", ""),
                         src.get("use_xpath", 0), src.get("encoding", ""), src.get("max_items", 30),
                         src.get("remove_selectors", "[]"), src.get("category", "web"), src.get("enabled", 1)),
                    )
                    results["imported_sources"] += 1

            # 3. 恢复 UAPI 平台状态
            for board_type, last_fetch in settings.get("uapi_fetch_log", {}).items():
                conn.execute(
                    "INSERT OR REPLACE INTO uapi_fetch_log(board_type, last_fetch_at) VALUES(?,?)",
                    (board_type, last_fetch),
                )

        logger.info("设置导入完成: %d 个 key, %d 个源, %d 个跳过",
                    results["imported_keys"], results["imported_sources"], results["skipped"])

    except Exception as e:
        logger.warning("导入设置失败: %s", e)

    return results


def get_export_summary(settings: dict) -> str:
    """生成导出摘要文本."""
    lines = ["设置备份摘要："]
    lines.append(f"  导出时间：{settings.get('_meta', {}).get('exported_at', 'N/A')}")

    app_settings = settings.get("app_settings", {})
    lines.append(f"  API Key 数量：{len(app_settings)}")
    for key in app_settings:
        # 脱敏显示
        value = app_settings[key]
        if len(value) > 8:
            masked = value[:4] + "****" + value[-4:]
        else:
            masked = "****"
        lines.append(f"    - {key}: {masked}")

    sources = settings.get("custom_sources", [])
    lines.append(f"  自定义源：{len(sources)} 个")

    uapi_log = settings.get("uapi_fetch_log", {})
    lines.append(f"  UAPI 平台状态：{len(uapi_log)} 个")

    return "\n".join(lines)
