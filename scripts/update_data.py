#!/usr/bin/env python3
import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "articles.json"
JS_OUTPUT_PATH = ROOT / "data" / "articles.js"
PUSHPLUS_ENDPOINT = "https://www.pushplus.plus/send"

SOURCES = {
    "qingchunbangyang": {
        "name": "青春榜样",
        "url": "https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzI5MDQ2ODM2Mg==&action=getalbum&album_id=3188102698777477122&subscene=189"
    },
    "guojiangfengcai": {
        "name": "国奖风采",
        "url": "https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzI5MDQ2ODM2Mg==&action=getalbum&album_id=4411270214575767559#wechat_redirect"
    }
}


def fetch_html(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "zh-CN,zh;q=0.9"
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def extract_article_list(page: str) -> str:
    match = re.search(r"articleList:\s*\[(.*?)\],\s*continue_flag:", page, re.S)
    if not match:
      raise RuntimeError("未找到 articleList 数据段")
    return match.group(1)


def parse_articles(block: str, category: str) -> list[dict]:
    pattern = re.compile(
        r"title:\s*'(?P<title>.*?)',\s*"
        r"create_time:\s*'(?P<create_time>\d+)',.*?"
        r"url:\s*'(?P<url>.*?)',.*?"
        r"msgid:\s*'(?P<msgid>\d+)',.*?"
        r"itemidx:\s*'(?P<itemidx>\d+)'",
        re.S,
    )

    articles = []
    for match in pattern.finditer(block):
        raw_url = html.unescape(match.group("url")).replace("http://", "https://")
        timestamp = int(match.group("create_time"))
        articles.append(
            {
                "id": f"{match.group('msgid')}-{match.group('itemidx')}",
                "category": category,
                "title": clean_text(match.group("title")),
                "url": raw_url,
                "published_at": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                "published_timestamp": timestamp,
            }
        )
    return articles


def clean_text(value: str) -> str:
    return html.unescape(value).replace("\\'", "'").strip()


def build_payload() -> dict:
    all_articles = []
    for category, source in SOURCES.items():
        page = fetch_html(source["url"])
        article_block = extract_article_list(page)
        all_articles.extend(parse_articles(article_block, category))

    all_articles.sort(key=lambda item: item["published_timestamp"], reverse=True)

    return {
        "metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sources": {key: value["url"] for key, value in SOURCES.items()},
            "article_count": len(all_articles),
        },
        "articles": all_articles,
    }


def load_existing_articles() -> list[dict]:
    if not OUTPUT_PATH.exists():
        return []
    try:
        payload = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    articles = payload.get("articles")
    return articles if isinstance(articles, list) else []


def find_new_articles(old_articles: list[dict], new_articles: list[dict]) -> list[dict]:
    old_ids = {article.get("id") for article in old_articles}
    return [article for article in new_articles if article.get("id") not in old_ids]


def send_pushplus(token: str, new_articles: list[dict]) -> None:
    if not token or not new_articles:
        return

    lines = []
    for article in new_articles[:5]:
        lines.append(
            f"- {article['title']}<br/>"
            f"  发布时间：{article['published_at']}<br/>"
            f"  <a href=\"{article['url']}\">打开文章</a>"
        )
    if len(new_articles) > 5:
        lines.append(f"<br/>其余 {len(new_articles) - 5} 篇请到页面查看。")

    payload = {
        "token": token,
        "title": f"蚌院人物新闻有 {len(new_articles)} 篇新文章",
        "content": "<br/><br/>".join(lines),
        "template": "html",
    }
    request = urllib.request.Request(
        PUSHPLUS_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8", errors="ignore"))
    if result.get("code") != 200:
        raise RuntimeError(f"pushplus send failed: {result}")


def main() -> int:
    existing_articles = load_existing_articles()
    payload = build_payload()
    new_articles = find_new_articles(existing_articles, payload["articles"])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    OUTPUT_PATH.write_text(json_text, encoding="utf-8")
    JS_OUTPUT_PATH.write_text("window.__ARTICLES_DATA__ = " + json_text, encoding="utf-8")
    send_pushplus(os.getenv("PUSHPLUS_TOKEN", "").strip(), new_articles)
    print(f"wrote {len(payload['articles'])} articles to {OUTPUT_PATH}")
    print(f"detected {len(new_articles)} new articles")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"update failed: {exc}", file=sys.stderr)
        raise
