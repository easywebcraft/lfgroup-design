#!/bin/bash
# lfgroup.jp（本番・Xserver）へ反映する（2026-10-09）。
#   ./deploy.sh          ... 何が変わるかを表示するだけ（反映しない）
#   ./deploy.sh --go     ... 本番へ反映する（反映の前に、サーバー側へバックアップを残す）
#
# 本番の書き出し（python3 build.py --release --site-url https://lfgroup.jp）→ dist/ の中身を public_html へ rsync する。
# - 内容（チェックサム）が変わったファイルだけを送る。--delete は付けない（Search Console の確認ファイルなど、dist にないものを消さないため）
# - パスワードや鍵はこのファイルに書かない。接続は次のどちらか
#     A. ~/.ssh/config の別名 lfgroup-xserver（標準）
#     B. 環境変数  LF_SSH_TARGET=lfgroup@sv16671.xserver.jp  LF_SSH_KEY=~/.ssh/lfgroup_deploy
# - お客様の本番に触るので、反映は「公開して」の指示があったときだけ（--go を付けたときだけ）
#
# 最初の設定（1回だけ）
#  1. 鍵を作る：      ssh-keygen -t ed25519 -f ~/.ssh/lfgroup_deploy -C lfgroup-deploy -N ""
#  2. Xserver サーバーパネル → SSH設定 → 公開鍵を登録（~/.ssh/lfgroup_deploy.pub の中身）して ON にする
#  3. 確認：          ssh -i ~/.ssh/lfgroup_deploy -p 10022 lfgroup@sv16671.xserver.jp "ls lfgroup.jp/public_html | head"
#  4. （標準の接続にする場合）~/.ssh/config に次を足す
#       Host lfgroup-xserver
#         HostName sv16671.xserver.jp
#         Port 10022
#         User lfgroup
#         IdentityFile ~/.ssh/lfgroup_deploy
set -euo pipefail
cd "$(dirname "$0")"

TARGET="${LF_SSH_TARGET:-lfgroup-xserver}"
REMOTE_ROOT="lfgroup.jp"
REMOTE_DIR="${REMOTE_ROOT}/public_html/"
SITE_URL="https://lfgroup.jp"
SSH_CMD="ssh -o BatchMode=yes"
if [ -n "${LF_SSH_KEY:-}" ]; then SSH_CMD="${SSH_CMD} -i ${LF_SSH_KEY/#\~/$HOME} -p ${LF_SSH_PORT:-10022}"; fi
# 公開しないものが前に上がっていた場合に、反映のついでに消す（1行に1つ。public_html からの相対パス）
REMOVE_FILES=("images/recruit-work-prompts.md")

echo "== 本番用の書き出し（${SITE_URL}）"
python3 build.py --release --site-url "${SITE_URL}" | grep -E "⚠|※" || true
test -f dist/index.html || { echo "dist/index.html がありません"; exit 1; }
test -f dist/google169aca25f9cbbfb6.html || { echo "Search Console の確認ファイルがありません"; exit 1; }
test -f dist/.htaccess || { echo ".htaccess がありません"; exit 1; }
if grep -rl "note-draft\|試作です" dist --include="*.html" >/dev/null 2>&1; then
  echo "下書きの印・試作の帯が残っているので止めます"; exit 1
fi
if grep -rIl "052-990-6159\|0529906159" dist >/dev/null 2>&1; then
  echo "旧番号が残っているので止めます"; exit 1
fi

if [ "${1:-}" = "--go" ]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  echo "== サーバー側にバックアップ：${REMOTE_ROOT}/_backup_${STAMP}"
  ${SSH_CMD} "${TARGET}" "cp -a ${REMOTE_ROOT}/public_html ${REMOTE_ROOT}/_backup_${STAMP} && ls -dt ${REMOTE_ROOT}/_backup_* | tail -n +6 | xargs -r rm -rf"
  echo "== 本番へ反映します（${TARGET}:${REMOTE_DIR}）"
  rsync -rlvzc --itemize-changes -e "${SSH_CMD}" dist/ "${TARGET}:${REMOTE_DIR}"
  for f in "${REMOVE_FILES[@]}"; do ${SSH_CMD} "${TARGET}" "rm -f ${REMOTE_DIR}${f}"; done
  echo "== 反映しました。外から確認：${SITE_URL}/"
  echo "   戻す：  ssh ${TARGET} \"rsync -a ${REMOTE_ROOT}/_backup_${STAMP}/ ${REMOTE_DIR}\""
else
  echo "== 確認のみ（反映しません）。内容が変わるファイル："
  rsync -rlnvzc --itemize-changes -e "${SSH_CMD}" dist/ "${TARGET}:${REMOTE_DIR}" | grep -E "^<|^\*|^>" || echo "   （変わるファイルはありません）"
  echo "== 問題なければ  ./deploy.sh --go  で反映します"
fi
