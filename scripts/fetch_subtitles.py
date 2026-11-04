#!/usr/bin/env python3
"""Fetch full Bilibili AI subtitles with timestamps.

The legacy x/player/v2 `subtitle_url` is often truncated (e.g. first 14 min).
bilibili-api's Video.get_subtitle(cid) returns the full track for long lectures.

Usage:
  python fetch_subtitles.py --bvids BV1...,BV1... --out .work/subs
  BILI_SESSDATA=... python fetch_subtitles.py --bvids BV1... --out .work/subs
"""
import argparse
import asyncio
import json
import os
import sys
import urllib.request


def load_credential(path: str):
    from bilibili_api import Credential

    data = {}
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    sess = os.environ.get("BILI_SESSDATA") or data.get("sessdata", "")
    jct = os.environ.get("BILI_JCT") or data.get("bili_jct", "")
    buvid = os.environ.get("BILI_BUVID3") or data.get("buvid3", "")
    uid = os.environ.get("BILI_DEDEUSERID") or data.get("dedeuserid", "")
    if not sess:
        raise SystemExit("missing SESSDATA: pass --cookie-file or BILI_SESSDATA")
    return Credential(sessdata=sess, bili_jct=jct, buvid3=buvid, dedeuserid=uid)


def fetch_json(url: str):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.bilibili.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


async def fetch_one(video_mod, cred, bvid: str, out_dir: str):
    v = video_mod.Video(bvid, credential=cred)
    info = await v.get_info()
    cid = info["cid"]
    sub = await v.get_subtitle(cid)
    tracks = sub.get("subtitles") or []
    zh = next((t for t in tracks if str(t.get("lan", "")).startswith("ai-zh")), None)
    if zh is None:
        zh = next((t for t in tracks if str(t.get("lan", "")).startswith("zh")), None)
    if zh is None:
        raise RuntimeError("no Chinese subtitle track")
    url = zh.get("subtitle_url", "")
    if url.startswith("//"):
        url = "https:" + url
    body = (fetch_json(url).get("body") or [])
    if not body:
        raise RuntimeError("empty subtitle body")
    path = os.path.join(out_dir, bvid + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"bvid": bvid, "cid": cid, "body": body}, f, ensure_ascii=False)
    print(f"{bvid}: {len(body)} segments, 0..{body[-1]['to']:.1f}s -> {path}")


async def main_async(args):
    from bilibili_api import video

    cred = load_credential(args.cookie_file)
    os.makedirs(args.out, exist_ok=True)
    for bvid in [x.strip() for x in args.bvids.split(",") if x.strip()]:
        try:
            await fetch_one(video, cred, bvid, args.out)
        except Exception as e:
            print(f"{bvid}: ERROR {e!r}", file=sys.stderr)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bvids", required=True, help="comma-separated BV ids")
    p.add_argument("--out", default=".work/subs")
    p.add_argument("--cookie-file", default=os.path.expanduser("~/.dsh/bili-duty/bili_credential.json"))
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
