"""scripts/wechat_setup.py

合并脚本（交互式）：
- 提示用户输入公众号名称（或通过 `--names` 参数传入逗号分隔的名称列表）
- 确保存在会话（统一存放在 `cfg/session.json`，由 `.gitignore` 忽略）；若缺失则尝试 Selenium 登录
- 查询每个公众号的 `biz`（FakeID），并将 `sources` 中记录为只保存 `biz`（每个 source 的 `id` 为 `wechat_<biz>`）
- 可选：通过 `--crawl` 标志在添加后立即抓取新增公众号的文章

用法（PowerShell）：
    python scripts\wechat_setup.py --names "公众号A,公众号B" --count 10 --crawl

"""
from __future__ import annotations

import os
import json
import argparse
import time
import asyncio
from typing import Optional, List, Dict, Any

import sys

# Ensure project root is on sys.path so local packages (wechat) are importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from wechat import auth as wechat_auth
except Exception:
    wechat_auth = None

from wechat import config as wechat_config
from wechat.services import get_fakeid_by_name, crawl_wechat_source

CFG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cfg")
SESSION_PATH = getattr(wechat_config, "SESSION_FILE", os.path.join(CFG_DIR, "session.json"))
LEGACY_COOKIES_PATH = os.path.join(CFG_DIR, "cookies.json")
WECHAT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "sources", "wechat.json")


def _load_sources_file() -> List[Dict[str, Any]]:
    if not os.path.exists(WECHAT_CONFIG_PATH):
        return []
    try:
        with open(WECHAT_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    if isinstance(data, list):
        return [s for s in data if isinstance(s, dict)]
    if isinstance(data, dict):
        return [s for s in data.get("sources", []) if isinstance(s, dict)]
    return []


def _load_json(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def load_local_session() -> Optional[Dict[str, Any]]:
    """Load session from the canonical cfg/session.json, falling back to legacy cookies.json if needed."""
    for path in (SESSION_PATH, LEGACY_COOKIES_PATH):
        data = _load_json(path)
        if data:
            return data
    return None


def persist_session(session: Dict[str, Any]) -> None:
    """Persist session to cfg/session.json and refresh in-memory config."""
    if not session:
        return
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)
    payload = dict(session)
    if "saved_at" not in payload:
        payload["saved_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    with open(SESSION_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    # 立即刷新 wechat_config 中的会话副本，便于后续逻辑使用
    try:
        if hasattr(wechat_config, "load_session"):
            wechat_config.load_session()
    except Exception:
        pass


def ensure_session_interactive() -> Dict[str, Any]:
    # 优先使用 wechat.config 内存中的会话（来自 cfg/session.json）
    try:
        wechat_config.load_session()
        session_from_conf = getattr(wechat_config, "WECHAT_SESSION", None) or {}
        if wechat_config.has_valid_session(session_from_conf):
            print(f"[INFO] 使用 {SESSION_PATH} 中的 session")
            return session_from_conf
    except Exception:
        pass

    sess = load_local_session()
    if sess:
        print(f"[INFO] loaded session from existing local file")
        persist_session(sess)
        return sess

    # 触发 wechat.config 自带的自动登录/提示逻辑
    wechat_config.ensure_session(interactive=True, prompt_if_missing=True)
    if wechat_config.has_valid_session():
        print(f"[INFO] 已通过交互式登录刷新 {SESSION_PATH}")
        return dict(wechat_config.WECHAT_SESSION)

    # 某些流程会先写入 cfg/cookies.json，再由脚本负责迁移到 session.json
    refreshed = load_local_session()
    if refreshed:
        print(f"[INFO] 检测到新的 cookies，会同步至 {SESSION_PATH}")
        persist_session(refreshed)
        return refreshed

    if wechat_auth and hasattr(wechat_auth, "get_cookies"):
        print("会话文件未找到，尝试使用 Selenium 交互式登录获取会话（请扫码）...")
        os.makedirs(CFG_DIR, exist_ok=True)
        data = wechat_auth.get_cookies()
        if data:
            persist_session(data)
            print(f"[INFO] 已保存会话到 {SESSION_PATH}")
            return data

    raise RuntimeError("无法获取微信会话，请先运行 scripts/wechat_setup.py --names ... 交互式扫码，或手动添加 cfg/session.json。")


def merge_wechat_config(new_sources: List[Dict[str, Any]]) -> None:
    """将 new_sources 合并到 `config/sources/wechat.json` 中（纯列表格式）。"""
    os.makedirs(os.path.dirname(WECHAT_CONFIG_PATH), exist_ok=True)
    existing_sources = _load_sources_file()
    existing = {s.get("id"): s for s in existing_sources}
    for s in new_sources:
        existing[s["id"]] = s

    merged = list(existing.values())

    with open(WECHAT_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 已写入 {WECHAT_CONFIG_PATH}，共 {len(merged)} 个源")


def build_source_entry(name: str, biz: str, count: int) -> Dict[str, Any]:
    sid = f"wechat_{biz}"
    return {
        "id": sid,
        "name": name,
        "biz": biz,
        "count": count,
        "created_at": int(time.time()),
    }


def _resolve_source_name(source_id: str) -> str:
    for src in getattr(wechat_config, "WECHAT_SOURCES", []) or []:
        if src.get("id") == source_id:
            return src.get("name") or source_id
    return source_id


async def maybe_crawl_sources(source_ids: List[str]):
    summary: List[Dict[str, Any]] = []
    for sid in source_ids:
        display_name = _resolve_source_name(sid)
        try:
            items = await crawl_wechat_source(sid)
            summary.append({"name": display_name, "count": len(items)})
        except Exception as exc:
            summary.append({"name": display_name, "error": str(exc)})

    if not summary:
        print("未抓取到任何公众号。")
        return



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--names", help="公众号名称列表，逗号分隔，例如: '校团委,信息学院'", required=False)
    parser.add_argument("--count", help="每个公众号拉取文章数量，默认 10", type=int, default=10)
    parser.add_argument("--crawl", help="添加后是否立即抓取（y/n）", action="store_true")
    args = parser.parse_args()

    wx_cfg = ensure_session_interactive()

    if args.names:
        names = [n.strip() for n in args.names.split(",") if n.strip()]
    else:
        names = []

    if not names:
        print("未提供 --names 参数，已完成会话校验/刷新，跳过新增公众号。")
        return

    new_sources = []
    new_ids = []
    for name in names:
        print(f"\n处理: {name}")
        biz = get_fakeid_by_name(wx_cfg, name)
        if not biz:
            print(f"跳过: 未找到 biz for {name}")
            continue
        entry = build_source_entry(name, biz, args.count)
        new_sources.append(entry)
        new_ids.append(entry["id"])

    if new_sources:
        merge_wechat_config(new_sources)
        # 更新内存中的 wechat 配置，确保随后立即抓取能找到新加入的 source
        try:
            # 清理旧的 sources，重新加载文件中的配置
            if hasattr(wechat_config, "WECHAT_SOURCES"):
                wechat_config.WECHAT_SOURCES.clear()
            if hasattr(wechat_config, "load_configurations"):
                wechat_config.load_configurations()
        except Exception:
            pass
        if args.crawl:
            asyncio.run(maybe_crawl_sources(new_ids))
        else:
            yn = input("是否立即抓取新增公众号文章？(y/N): ").strip().lower()
            if yn == "y":
                asyncio.run(maybe_crawl_sources(new_ids))
    else:
        print("没有新增源，退出")


if __name__ == "__main__":
    main()
