# LFグループ株式会社 ホームページ リニューアル試作

今のホームページ（STUDIO製、https://gray345542.studio.site ）に載っている情報だけを使って、
構成とデザインを作り直した試作です。新しい情報・実績・数値は足していません。

- 公開URL（GitHub Pages）：https://easywebcraft.github.io/lfgroup-design/
- 置き方はかみのて（`easywebcraft/kaminote-design`）と同じ。リポジトリ直下をそのまま配信する。
- 試作（このURL）には「試作です」の帯と `noindex` が付いている。**本番は `python3 build.py --release` で書き出した `dist/` を使う**（帯・`noindex`・HTMLのコメントは自動で外れる）。このリポジトリは公開されていて、直下の `README.md`・`build.py`・`src/`・`text/` も誰でも見られるため、本番の配信先にはリポジトリ直下ではなく `dist/` の中身だけを置く。

## 構成

| パス | 中身 |
| --- | --- |
| `build.py` | ページを書き出すスクリプト。共通のヘッダー・フッターと各ページの中身を組み合わせる |
| `src/` | 共通のCSS・JS、トップページの本文。`refine.css` が2026-10の全面見直し（余白・写真・文字）で、最後に読み込まれる |
| `text/` | 今のサイトから取得した各ページの本文（2026-10-02取得） |
| `index.html`・`about/` など | 書き出したサイト（生成物。直接編集しない） |
| `assets/` | 書き出したCSS・JS（生成物） |
| `images/` | 写真（ChatGPTで作ったイメージ素材。実在のスタッフ・お客様ではない。プロンプトは ewc-crm の `docs/LFグループ_画像生成プロンプト.md`） |

## 動きの試作（/motion/）

- URL：https://easywebcraft.github.io/lfgroup-design/motion/ （トップページだけ。今のトップと見比べてもらう用）
- 2026-10-05、お客さまから「careerscout.co.jp のようなトップの動きを」と要望があり作ったもの。動きは `src/motion.css`・`src/motion.js`（先頭のコメントに A〜E の一覧）
- `build.py` の `write_motion()` がトップページに動きの CSS・JS を足して書き出す。本番（`--release`）には出さない
- 採用が決まったら、motion.css・motion.js を本体（style.css・main.js）に移し、/motion/ を消す

## 季節の写真の試作（/season/）

- URL：https://easywebcraft.github.io/lfgroup-design/season/ （トップページだけ）
- 2026-10-05、お客さまから「トップの写真を春→夏→秋→冬とループさせたい」と要望があり作ったもの
- 春は今の `images/hero.jpg`。夏・秋・冬は `images/hero-summer.jpg`・`hero-autumn.jpg`・`hero-winter.jpg`（ChatGPTで、今の写真を添付して同じ家族・構図で季節だけ変えて生成）
- 6秒ごとにフェードで切り替え。写真の右下（スマホは写真の下端）に季節のボタンと一時停止。「動きを減らす」設定の端末では自動で切り替えない
- 動きは `src/season.css`・`src/season.js`、書き出しは `build.py` の `write_season()`。本番（`--release`）には出さない

## 書き出しと確認

```bash
python3 build.py                                  # 直下に全ページを書き出す
cd .. && python3 -m http.server 8010              # http://localhost:8010/lfgroup-design/ で確認
```

### 本番用の書き出し

```bash
python3 build.py --release --site-url https://（本番のドメイン）   # dist/ に本番用を書き出す
python3 -m http.server 8011 --directory dist                     # http://localhost:8011/ で確認
```

- `dist/` に入るのは、ページ・`assets/`・`images/`（顧客のロゴ元データ `images/logo/` は除く）・`404.html`・`robots.txt`・`sitemap.xml` だけ
- 試作の帯・`noindex`・HTMLのコメント・CSSのコメントを外す
- `--site-url` を付けると `canonical`・`og:url`・`og:image`（`images/ogp.jpg`、1200×630）・`sitemap.xml` が入る。ドメインが決まるまでは付けずに書き出せる
- `404.html` は、サイト直下（ドメイン直下）で配信する前提のリンクになっている
- `dist/` はコミットしない（`.gitignore` 済み）

書き出したページ（`index.html`・`about/index.html` など）を直接編集しないこと（次の書き出しで上書きされる）。
`build.py` か `src/` を直して書き出し直し、**原本と生成物を一緒にコミットする**（かみのてと同じ）。

原本では `/about/` のようにサイト直下から書き、書き出すときに相対パス（`../about/`）へ張り替える。
GitHub Pages は `easywebcraft.github.io/lfgroup-design/` の下で配信するため、`/` 始まりのままだと外れる。
ディレクトリのリンクなので、HTMLファイルを直接開くのではなくサーバー経由で見る。

## 公開前に残っていること

- ロゴ：`images/logo.png` は顧客からもらった正式ロゴ（元ファイル `images/logo/source-client.png`）の、金の輪の外側を透明にしたもの。ファビコンは `favicon.png`・`apple-touch-icon.png`
- 郵便番号：461-0004（2026-10-05 クライアントに確認済み。`build.py` の `POSTAL`）
- お問い合わせ：フォームは置かず、電話だけ（2026-10-05 決定）。お問い合わせページの受付時間 10:00～18:00 は仮の値
- 個人情報保護方針の「お問い合わせ窓口」：会社の代表連絡先（住所・052-846-2135）で埋めた（2026-10-05）。受付時間「10:00～18:00」は勤務時間に合わせた仮の値なので、部署名を入れるかと合わせて確認する
- 保険会社による掲載内容の確認
- 電話番号：お問い合わせは 052-846-2135、採用は 052-846-8224。052-990-6159 は使っていない番号なので載せない（2026-10-04 確認）
