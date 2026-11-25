#!/usr/bin/env python3
"""시드 갱신 스크립트 (집 컴퓨터에서 실행).
인스타그램·nitter(X)·tikwm(틱톡)은 GitHub 서버(데이터센터 IP)를 막거나 제한하므로,
웹 버전의 릴스·X·틱톡 데이터는 이 스크립트로 수집해 seed/에 저장한 뒤 커밋·푸시해서 공급합니다.
collect.py는 하루(36시간) 안에 만든 시드가 GitHub에서 모은 것보다 많으면 시드를 씁니다.
사용: python3 update_seed.py  (맥: 시드갱신-Mac.command, 윈도우: 시드갱신-릴스.bat)
"""
import hashlib
import json
import os
import shutil
import subprocess
from urllib.parse import urlparse

import server

SEED = os.path.join(server.BASE_DIR, "seed")
IMG = os.path.join(SEED, "img")

# (파일명, 항목 키, 이미지 필드, 최대 개수, 수집 함수)
SOURCES = [
    ("reels.json", "reels", "thumbnail", 80, server.get_reels),
    ("x.json", "posts", "media", 120, server.get_x_posts),
    ("tiktok.json", "posts", "thumbnail", 100, server.get_tiktok),
]


def save_image(url, keep):
    if not (url.startswith("https://")
            and urlparse(url).netloc.lower().endswith(server.IMG_PROXY_ALLOW)):
        return ""
    name_base = hashlib.sha1(url.encode()).hexdigest()[:16]
    try:
        ctype, body = server.http_get(url, timeout=12)
    except Exception:
        return ""
    ext = ".png" if "png" in ctype else ".webp" if "webp" in ctype else ".jpg"
    name = name_base + ext
    path = os.path.join(IMG, name)
    with open(path, "wb") as fh:
        fh.write(body)
    if shutil.which("sips"):
        # 맥 기본 도구로 썸네일을 작게(긴 변 360px JPEG) 줄여 저장소 용량 증가를 억제합니다
        small = os.path.join(IMG, name_base + ".jpg")
        r = subprocess.run(["sips", "-Z", "360", "-s", "format", "jpeg",
                            "-s", "formatOptions", "70", path, "--out", small],
                           capture_output=True)
        if r.returncode == 0 and os.path.exists(small):
            if small != path:
                os.remove(path)
            name = name_base + ".jpg"
    keep.add(name)
    return "img/" + name


def main():
    os.makedirs(IMG, exist_ok=True)
    keep, ok = set(), 0
    for fname, key, field, limit, fetch in SOURCES:
        items, accounts, fetched = fetch(True)
        items = items[:limit]
        path = os.path.join(SEED, fname)
        if not items:
            print("%s: 수집 실패(0개) — 기존 시드 유지" % fname)
            # 기존 시드가 쓰는 이미지는 지우지 않습니다
            try:
                with open(path, encoding="utf-8") as f:
                    for it in json.load(f).get(key) or []:
                        v = it.get(field) or ""
                        if v.startswith("img/"):
                            keep.add(v.split("/", 1)[1])
            except (OSError, json.JSONDecodeError):
                pass
            continue
        saved = 0
        for it in items:
            v = it.get(field) or ""
            if v:
                it[field] = save_image(v, keep)
                saved += bool(it[field])
        with open(path, "w", encoding="utf-8") as f:
            json.dump({key: items, "accounts": accounts, "fetchedAt": fetched},
                      f, ensure_ascii=False)
        print("%s: %d개, 이미지 %d개 저장" % (fname, len(items), saved))
        ok += 1
    # 더 이상 쓰지 않는 이미지 정리
    for f in os.listdir(IMG):
        if f not in keep:
            os.remove(os.path.join(IMG, f))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
