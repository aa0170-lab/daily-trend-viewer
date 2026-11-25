#!/bin/bash
# 맥용 시드 갱신 — 이 컴퓨터에서 릴스·X·틱톡을 수집해 seed/에 저장하고 내 GitHub 포크에 올립니다.
# GitHub 서버에서 막히는 소스를 웹 버전에 채워 넣는 용도입니다. 결과는 seed_task.log에 기록됩니다.
cd "$(dirname "$0")" || exit 1
LOG=seed_task.log
echo "===== $(date '+%Y-%m-%d %H:%M:%S') 시드 갱신 시작 =====" >> "$LOG"

PY=$(command -v python3 || echo /usr/bin/python3)
if ! "$PY" update_seed.py >> "$LOG" 2>&1; then
  echo "수집 실패 — 시드 유지, 푸시 생략" >> "$LOG"
  exit 1
fi

# 포크(fork)가 연결돼 있으면 거기로, 아니면 origin으로 올립니다
REMOTE=origin
git remote | grep -qx fork && REMOTE=fork

git add seed >> "$LOG" 2>&1
if git -c core.quotepath=false commit -m "chore: 릴스·X·틱톡 시드 자동 갱신" >> "$LOG" 2>&1; then
  git pull --rebase --autostash "$REMOTE" main >> "$LOG" 2>&1
  git push "$REMOTE" HEAD:main >> "$LOG" 2>&1 && echo "푸시 완료 ($REMOTE)" >> "$LOG"
else
  echo "변경 없음 — 푸시 생략" >> "$LOG"
fi
echo "===== 완료 =====" >> "$LOG"
tail -8 "$LOG"
