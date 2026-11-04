#!/usr/bin/env python3
"""Fetch Bilibili official chapters and source dimensions.

Usage:
  python fetch_chapters.py --bvids BV1...,BV1... --out .work/chapters.json
"""
import argparse
import json
import os
import urllib.request


def load_cookie(path: str) -> str:
    data = {}
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    sess = os.environ.get("BILI_SESSDATA") or data.get("sessdata", "")
    jct = os.environ.get("BILI_JCT") or data.get("bili_jct", "")
    buvid = os.environ.get("BILI_BUVID3") or data.get("buvid3", "")
    uid = os.environ.get("BILI_DEDEUSERID") or data.get("dedeuserid", "")
    if not sess:
        raise SystemExit("missing SESSDATA")
    return f"SESSDATA={sess}; bili_jct={jct}; buvid3={buvid}; DedeUserID={uid}"


def get(url: str, cookie: str):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Cookie": cookie,
            "Referer": "https://www.bilibili.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bvids", required=True)
    p.add_argument("--out", default=".work/chapters.json")
    p.add_argument("--cookie-file", default=os.path.expanduser("~/.dsh/bili-duty/bili_credential.json"))
    args = p.parse_args()
    cookie = load_cookie(args.cookie_file)
    out = {}
    for bvid in [x.strip() for x in args.bvids.split(",") if x.strip()]:
        try:
            view = get(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}", cookie)["data"]
            cid = view["cid"]
            pv = get(f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}", cookie)["data"]
            chapters = [
                {"from": int(x.get("from", 0)), "to": int(x.get("to", 0)), "content": str(x.get("content", "")).strip()}
                for x in (pv.get("view_points") or [])
            ]
            out[bvid] = {
                "cid": cid,
                "title": view.get("title", ""),
                "duration": view.get("duration", 0),
                "dimension": view.get("dimension", {}),
                "chapters": chapters,
            }
            print(f"{bvid}: {len(chapters)} chapters, dimension={view.get('dimension')}")
        except Exception as e:
            print(f"{bvid}: ERROR {e!r}")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
