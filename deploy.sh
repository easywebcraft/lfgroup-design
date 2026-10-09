#!/bin/bash
# lfgroup.jp（本番・Xserver）へ反映する（2026-10-09）。
#   ./deploy.sh          ... 何が変わるかを表示するだけ（反映しない）
#   ./deploy.sh --go     ... 本番へ反映する
#
# 本番の書き出し（python3 build.py --release --site-url https://lfgroup.jp）→ dist/ の中身を public_html へ rsync する。
# - パスワードや鍵はこのファイルに書かない。接続先は ~/.ssh/config の別名 lfgroup-xserver にまとめる（下の「最初の設定」）
# - --delete は付けない（Search Console の確認ファイルなど、dist にないものを消さないため）
# - お客様の本番に触るので、反映は「公開して」の指示があったときだけ（--go を付けたときだけ）
#
# 最初の設定（1回だけ）
#  1. 鍵を作る：      ssh-keygen -t ed25519 -f ~/.ssh/lfgroup_xserver
#  2. Xserver サーバーパネル → SSH設定 で SSH を ON にし、公開鍵（~/.ssh/lfgroup_xserver.pub）を登録する
#  3. ~/.ssh/config に次を足す（ホスト名・ユーザーはサーバーパネルの表示に合わせる）
#       Host lfgroup-xserver
#         HostName sv16671.xserver.jp
#         Port 10022
#         User lfgroup
#         IdentityFile ~/.ssh/lfgroup_xserver
#  4. 確認：          ssh lfgroup-xserver "ls lfgroup.jp/public_html | head"
set -euo pipefail
cd "$(dirname "$0")"

HOST_ALIAS="${LF_SSH_HOST:-lfgroup-xserver}"
REMOTE_DIR="${LF_REMOTE_DIR:-lfgroup.jp/public_html/}"
SITE_URL="https://lfgroup.jp"

echo "== 本番用の書き出し（${SITE_URL}）"
python3 build.py --release --site-url "${SITE_URL}" | grep -E "⚠|※" || true
test -f dist/index.html || { echo "dist/index.html がありません"; exit 1; }
test -f dist/google169aca25f9cbbfb6.html || { echo "Search Console の確認ファイルがありません"; exit 1; }
if grep -rl "note-draft\|試作です" dist --include="*.html" >/dev/null 2>&1; then
  echo "下書きの印・試作の帯が残っているので止めます"; exit 1
fi

if [ "${1:-}" = "--go" ]; then
  echo "== 本番へ反映します（${HOST_ALIAS}:${REMOTE_DIR}）"
  rsync -avz --itemize-changes dist/ "${HOST_ALIAS}:${REMOTE_DIR}"
  echo "== 反映しました。外から確認：https://lfgroup.jp/"
else
  echo "== 確認のみ（反映しません）。変わるファイル："
  rsync -avzn --itemize-changes dist/ "${HOST_ALIAS}:${REMOTE_DIR}"
  echo "== 問題なければ  ./deploy.sh --go  で反映します"
fi
