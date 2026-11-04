#!/usr/bin/env python3
"""Download the best Bilibili DASH video stream and extract 720p frames.

Why not ffmpeg the CDN URL directly? Bilibili CDN often returns an I/O error
for ffmpeg; Python + Referer/Origin downloads fine, then ffmpeg decodes locally.

Usage:
  python extract_frames.py --bvid BV1... --times 33,259,560 \
      --out-dir assets/01 --prefix live
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
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
        headers={"User-Agent": "Mozilla/5.0", "Cookie": cookie, "Referer": "https://www.bilibili.com/"},
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def download(url: str, path: str):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.bilibili.com/",
            "Origin": "https://www.bilibili.com",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)


def find_ffmpeg(explicit: str = "") -> str:
    if explicit:
        return explicit
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    for p in glob.glob(os.path.expanduser("~/.dsh/**/ffmpeg*.exe"), recursive=True):
        return p
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise SystemExit("ffmpeg not found: pass --ffmpeg or pip install imageio-ffmpeg")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bvid", required=True)
    p.add_argument("--times", required=True, help="comma-separated seconds, e.g. 33,259,560")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--prefix", default="frame")
    p.add_argument("--ffmpeg", default="")
    p.add_argument("--cookie-file", default=os.path.expanduser("~/.dsh/bili-duty/bili_credential.json"))
    p.add_argument("--cache", default=".video-cache")
    p.add_argument("--keep-video", action="store_true")
    args = p.parse_args()

    cookie = load_cookie(args.cookie_file)
    view = get(f"https://api.bilibili.com/x/web-interface/view?bvid={args.bvid}", cookie)["data"]
    cid = view["cid"]
    play = get(
        f"https://api.bilibili.com/x/player/playurl?bvid={args.bvid}&cid={cid}&qn=80&fnval=4048&fourk=1",
        cookie,
    )["data"]
    videos = (play.get("dash") or {}).get("video") or []
    if not videos:
        raise SystemExit("no DASH video streams; check login/qn")
    best = max(videos, key=lambda x: int(x.get("width", 0)) * int(x.get("height", 0)))
    print(f"stream: {best.get('width')}x{best.get('height')} id={best.get('id')}")

    os.makedirs(args.cache, exist_ok=True)
    os.makedirs(args.out_dir, exist_ok=True)
    video_path = os.path.join(args.cache, args.bvid + ".m4s")
    if not os.path.exists(video_path) or os.path.getsize(video_path) < 1024 * 1024:
        download(best["baseUrl"], video_path)
    print(f"downloaded: {os.path.getsize(video_path) / 1024 / 1024:.1f} MB")

    ff = find_ffmpeg(args.ffmpeg)
    times = [int(float(x)) for x in args.times.split(",") if x.strip()]
    for i, t in enumerate(times, 1):
        out = os.path.join(args.out_dir, f"{args.prefix}-{i:02d}.jpg")
        r = subprocess.run(
            [ff, "-y", "-loglevel", "error", "-ss", str(t), "-i", video_path, "-frames:v", "1", "-q:v", "2", out],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode != 0:
            print(f"  {i}: t={t} FAIL {r.stderr[-160:]}")
        else:
            print(f"  {i}: t={t} -> {out} ({os.path.getsize(out) / 1024:.1f} KB)")
    if not args.keep_video:
        try:
            os.remove(video_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
