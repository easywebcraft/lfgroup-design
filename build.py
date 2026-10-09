#!/usr/bin/env python3
"""LFグループ株式会社 サイト試作のページを書き出す。

  python3 build.py  →  リポジトリの直下に各ページの index.html と assets/ を作る（GitHub Pages でそのまま配信）
  python3 build.py --release [--site-url https://example.co.jp]
                    →  本番用を dist/ に書き出す。試作の帯・noindex・HTMLのコメントを外し、ページと画像だけを置く。
                       --site-url を付けると canonical・og:url・og:image・sitemap.xml も入る（公開URLが決まってから）

共通部分（head・ヘッダー・メニュー・フッター）はここで一度だけ定義し、各ページの中身と組み合わせる。
文言は今のサイト（text/ に保存した本文）にあるものだけを使う。足していない。
"""
import argparse
import hashlib
import html
import re
import shutil
from pathlib import Path

BASE = Path(__file__).parent
SRC = BASE / 'src'
SITE = BASE  # GitHub Pages はリポジトリ直下を配信する（かみのてと同じ）。--release のときは dist/
RELEASE = False  # 本番用の書き出し（試作の帯・noindex・コメントを外す）
SITE_URL = ''  # 本番の公開URL（末尾の / なし）。決まるまでは空で、canonical・og:url・og:image・sitemap を出さない
TEXT = BASE / 'text'

# 電話番号の使い分け（今のサイトから分かる範囲）
#   052-846-2135：お問い合わせ用。ヘッダー・CTA・フッター・会社概要・採用情報・お問い合わせページのすべてに使う
#   052-846-8224：採用の応募先として載せていたが、2026-10-09 松本さんの指示で 052-846-2135 に統一した（載せない）
#   052-990-6159：今は使っていない番号（2026-10-04 クライアント確認）。サイトには載せない
TEL = '052-846-2135'
TEL_HREF = 'tel:0528462135'
RECRUIT_TEL = TEL  # 採用の電話も、お問い合わせと同じ番号に統一
RECRUIT_TEL_HREF = TEL_HREF
# メールアドレス（2026-10-09 松本さん）：info は個人・法人のお客様の問い合わせ先、recruit は採用の問い合わせ先
MAIL = 'info@lfgroup.jp'
RECRUIT_MAIL = 'recruit@lfgroup.jp'
ALLIANCE_MAIL = 'alliance@lfgroup.jp'  # アライアンス事業の問い合わせ用（2026-10-09 松本さん）。メールは目的別：info＝個人・法人、alliance＝アライアンス事業、recruit＝採用
# お問い合わせフォーム（Googleフォーム。info@lfgroup.jp に通知。2026-10-09）
FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSd5O9G8vna7SE2T7kWOxYvuTFFN2HupM-mXSf5bzZB0Vasmaw/viewform'
ADDRESS = '愛知県名古屋市東区葵3-14-5 2F'  # 2026-10-09 松本さん「リッチコーポは外して 3-14-5 2F に」。元のサイトは「葵3丁目14-5 リッチコーポ2階」
POSTAL = '461-0004'  # 今のサイトに記載がなく、2026-10-05 にクライアントに確認
COMPANY = 'LFグループ株式会社'

# メインメニュー（ヘッダー・ドロワー・フッターで共通）
# 2026-10-06 お客さまの指定で、見る人ごとの構成にした（それまでは 私たちについて・事業内容・サービス・会社情報・採用情報）
NAV = [
    ('about', '私たちについて', '/about/'),
    ('personal', '個人のお客様', '/personal/'),
    ('corporate', '法人のお客様', '/corporate/'),
    ('partner', 'アライアンス事業', '/partner/'),  # 2026-10-07 「提携企業様」から名前を変えた（トップのタイルと同じ名前に）
    ('company', '会社概要', '/company/'),
    ('recruitment', '採用情報', '/recruitment/'),
]
POLICIES = [
    ('operation', 'お客様本位の業務運営方針', '/operation/'),
    ('solicitation', '勧誘方針', '/solicitation/'),
    ('privacyprotection', '個人情報保護方針', '/privacyprotection/'),
    ('informationsecurity', '情報セキュリティ基本方針', '/informationsecurity/'),
]

ASSET_V = ''  # main() で CSS・JS の中身から決める
ARROW = '<svg class="arw"><use href="#i-arrow"/></svg>'
# 事業のアイコン（トップのカードと事業内容ページで共通）
ICONS = {
    'financialplanning': '''<svg class="card-icon" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <circle cx="34" cy="14" r="6"/><path d="M24 34c0-6 4.5-10 10-10s10 4 10 10"/>
    <path d="M8 44h8l8 4h10a3.5 3.5 0 0 0 0-7h-7"/><path d="M8 54h22l20-9a3.5 3.5 0 0 0-3-6.3L35 44"/>
    </svg>''',
    'alliance': '''<svg class="card-icon" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path d="M4 26l10-8 8 3"/><path d="M60 26l-10-8-12 4-10 8a3.5 3.5 0 0 0 5 5l7-5"/>
    <path d="M14 18l-0 0M10 30l14 14a3 3 0 0 0 4.5-4l3 3a3 3 0 0 0 4.5-4l2 2a3 3 0 0 0 4.5-4l-1-1a3 3 0 0 0 4.5-4L50 22"/>
    <path d="M22 38l4 4"/>
    </svg>''',
    'insuranceagency': '''<svg class="card-icon" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path d="M40 22V10a2 2 0 0 0-2-2H14a2 2 0 0 0-2 2v44a2 2 0 0 0 2 2h16"/>
    <path d="M18 18h16M18 26h16M18 34h8"/>
    <path d="M46 30l12 4v8c0 7-5 11-12 14-7-3-12-7-12-14v-8z"/><path d="M41 43l4 4 7-8"/>
    </svg>''',
    'partner': '''<svg class="card-icon" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <circle cx="32" cy="20" r="7"/><path d="M20 46c0-7.5 5.4-13 12-13s12 5.5 12 13"/>
    <circle cx="14" cy="26" r="5"/><path d="M4 46c0-6 4-10 10-10 2 0 3.6.4 5 1.2"/>
    <circle cx="50" cy="26" r="5"/><path d="M60 46c0-6-4-10-10-10-2 0-3.6.4-5 1.2"/>
    </svg>''',
}
# トップの本文の {{icon:キー}} をアイコンに置き換える（事業内容ページと同じ絵を使う）
TOP = re.sub(r'\{\{icon:(\w+)\}\}', lambda m: ICONS[m.group(1)], (SRC / 'top.html').read_text())


def esc(s):
    return html.escape(s, quote=False)


# ───────────────────────── 共通部分 ─────────────────────────

def nav_items(current, cls=''):
    out = []
    for key, label, href in NAV:
        cur = ' aria-current="page"' if key == current else ''
        inner = f'{label}{ARROW}' if cls == 'drawer' else label
        out.append(f'<li><a href="{href}"{cur}>{inner}</a></li>')
    return '\n        '.join(out)


# 試作であることを示す帯。試作（GitHub Pages）にだけ出し、--release では出さない
PREVIEW_NOTE = '<div class="design-preview-note">LFグループ株式会社さま ホームページ リニューアルの試作です（EasyWebCraft）</div>\n'


def url_meta(page_path):
    """canonical・og:url・og:image。公開URL（--site-url）が決まっているときだけ出す（どれも絶対URLが要るため）。"""
    if not SITE_URL:
        return ''
    url = f'{SITE_URL}/{page_path}'
    return (f'<link rel="canonical" href="{url}">\n'
            f'<meta property="og:url" content="{url}">\n'
            f'<meta property="og:image" content="{SITE_URL}/images/ogp.jpg">\n'
            '<meta name="twitter:card" content="summary_large_image">\n')


def layout(page_title, body, current='', description='顧客満足度を最優先に人々の生活を向上させます。', loader=False):
    title = COMPANY if not page_title else f'{page_title}｜{COMPANY}'
    # 試作は検索に載せない。本番（--release）では外す
    robots = '' if RELEASE else '<meta name="robots" content="noindex,nofollow">\n'
    return f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{html.escape(description)}">
{robots}<meta property="og:type" content="website">
<meta property="og:site_name" content="{COMPANY}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{html.escape(description)}">
__URL_META__
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600&family=Noto+Sans+JP:wght@400;500;700&family=Noto+Serif+JP:wght@500;600&display=swap" rel="stylesheet">
<link rel="icon" href="/images/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="/images/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/style.css?v={ASSET_V}">
<script>
  // 表示前に「フェード待ち」の状態にする（本文の最後で付けると、文字が一度見えてから消えてフェードする）。
  // main.js が読み込めなかったときに文字が隠れたままにならないよう、3秒で解除する。
  document.documentElement.classList.add('js');
  setTimeout(function () {{ if (!window.LF_READY) document.documentElement.classList.remove('js'); }}, 3000);
</script>{LOADER_HEAD if loader else ''}
</head>
<body>
{SPRITE}{LOADER if loader else ''}
{'' if RELEASE else PREVIEW_NOTE}
<header class="header" id="header">
  <div class="wrap header-inner">
    <a class="logo" href="/" aria-label="{COMPANY} トップ">
      <img class="logo-mark" src="/images/logo.png" alt="" width="360" height="360" data-eager>{COMPANY}
    </a>
    <nav class="gnav" aria-label="メインメニュー">
      <ul>
        {nav_items(current)}
      </ul>
    </nav>
    <a class="btn btn-primary" href="/contact/">ご相談・お問い合わせ{ARROW}</a>
    <button class="menu-btn" id="menuBtn" type="button" aria-label="メニューを開く" aria-expanded="false" aria-controls="drawer">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>

<div class="drawer" id="drawer" aria-hidden="true">
  <nav aria-label="メニュー">
    <ul>
      <li><a href="/">トップ{ARROW}</a></li>
      {nav_items(current, 'drawer')}
    </ul>
  </nav>
  <a class="btn btn-primary" href="/contact/">ご相談・お問い合わせ{ARROW}</a>
  <a class="tel" href="{TEL_HREF}"><small>お電話でのお問い合わせ</small>{TEL}</a>
</div>

<main>
{body}
</main>

<footer class="footer">
  <div class="wrap">
    <div class="footer-top">
      <div class="footer-info">
        <a class="logo" href="/"><img class="logo-mark" src="/images/logo.png" alt="" width="360" height="360">{COMPANY}</a>
        <p>〒{POSTAL} {ADDRESS}</p>
        <p>TEL <a href="{TEL_HREF}">{TEL}</a></p>
        <p>MAIL <a href="mailto:{MAIL}">{MAIL}</a></p>
      </div>
      <nav class="footer-nav" aria-label="フッターメニュー">
        <ul>
          {nav_items('')}
          <li><a href="/contact/">お問い合わせ</a></li>
        </ul>
      </nav>
    </div>
    <div class="footer-policy">
      <ul>
        {''.join(f'<li><a href="{h}">{l}</a></li>' for _, l, h in POLICIES)}
      </ul>
      <small>&copy; <span id="year">2026</span> {COMPANY} All Rights Reserved.</small>
    </div>
  </div>
</footer>

<div class="sp-bar" id="spBar">
  <a class="c" href="/contact/">保険・お金の相談</a>
  <a class="t" href="{TEL_HREF}"><svg><use href="#i-tel"/></svg>電話する</a>
</div>

<script src="/assets/main.js?v={ASSET_V}"></script>
</body>
</html>
'''


SPRITE = (SRC / 'sprite.svg').read_text()

# トップだけの最初の演出（ロゴと進み具合の輪 → キャッチコピー → ヘッダーと見出しの位置へ吸い込まれる）。
# 動かすのは main.js。同じタブの中では1回だけ（2ページ目以降・トップへ戻ったときは出さない）。
# ★「動きを減らす」設定の人には出さない。main.js が読めなかったときに画面が塞がったままにならないよう、
#   3秒で演出の状態を解除する。
LOADER_HEAD = """
<script>
  (function () {
    var r = document.documentElement, played = false;
    try { played = sessionStorage.getItem('lf_loader') === '1'; } catch (e) {}
    if (played || (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches)) return;
    r.classList.add('is-loading');
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    setTimeout(function () { if (!window.LF_LOADER_RUN) r.classList.remove('is-loading'); }, 3000);
  })();
</script>"""

LOADER = """
<div class="lf-loader" id="lfLoader" aria-hidden="true">
  <div class="ll-p1">
    <svg class="ll-ring" viewBox="0 0 120 120"><circle class="t" cx="60" cy="60" r="54"/><circle class="f" cx="60" cy="60" r="54"/></svg>
    <img class="ll-mark" src="/images/logo.png" alt="" width="360" height="360" data-eager>
    <span class="ll-pct">0%</span>
  </div>
  <div class="ll-p2">
    <p class="ll-logo"><img class="logo-mark" src="/images/logo.png" alt="" width="360" height="360" data-eager>LFグループ株式会社</p>
    <p class="ll-catch"><span class="l1">人と企業の可能性を</span><br><span class="l2">その先へ</span></p>
  </div>
  <span class="ll-skip">タップでスキップ</span>
</div>"""


def page_hero(label, title, crumbs, lead='', photo=None, chips=(), extra='', h1=True, pos='50% 50%', compact=False, zoom=1, caption=''):
    """下層ページの冒頭（全ページ共通）。パンくず → 小さな英字 → 大きな日本語タイトル → 一文 → ページの目次など（extra）。
    photo を渡すと、その下に横長の大きな写真を置く。crumbs は (名前, URL) の並び。最後が今のページ。"""
    items = ['<li><a href="/">トップ</a></li>']
    for name, href in crumbs[:-1]:
        items.append(f'<li><a href="{href}">{name}</a></li>')
    items.append(f'<li aria-current="page">{crumbs[-1][0]}</li>')
    # 記事ページは記事タイトルを h1 にするので、ここは見た目だけ同じ p にする
    title_html = f'<h1 class="fade">{title}</h1>' if h1 else f'<p class="sub-hero-title fade">{title}</p>'
    lead_html = f'\n      <p class="hero-lead fade">{lead}</p>' if lead else ''
    chips_html = ('\n      <ul class="hero-chips fade">' + ''.join(f'<li>{c}</li>' for c in chips) + '</ul>') if chips else ''
    extra_html = f'\n{extra}' if extra else ''
    # 写真があるページは、採用情報のFVと同じく、見出しの右側に写真を敷き、左端を白へなじませる（2026-10-06。
    # それまでは見出しの下に横長の写真を置いていた）。スマホは写真が上・見出しが下
    photo_html = ''
    if photo:
        style = f'object-position:{pos}' + (f';transform:scale({zoom});transform-origin:{pos}' if zoom != 1 else '')
        photo_html = (f'\n    <figure class="ph-photo fade">'
                      f'<img src="/images/{photo}" alt="" data-eager style="{style}" onerror="this.remove()">'
                      + (f'<figcaption>{caption}</figcaption>' if caption else '') + '</figure>')
    cls = 'page-hero sub-hero' + (' has-photo ph-fv' if photo else '') + (' compact' if compact else '')
    return f'''  <section class="{cls}">{photo_html}
    <div class="wrap sub-hero-copy">
      <ol class="crumb fade" aria-label="パンくずリスト">{''.join(items)}</ol>
      <p class="eyebrow fade">{label}</p>
      {title_html}{lead_html}{chips_html}{extra_html}
    </div>
  </section>
'''


def policy_lines_html(items, fade=True):
    """「01 ── 本文」の縦ライン型。items は文字列、または改行位置で区切った文字列のタプル。"""
    out = []
    for i, it in enumerate(items):
        parts = it if isinstance(it, (tuple, list)) else (it,)
        text = ''.join(f'<span>{p}</span>' for p in parts)
        out.append(f'<li{" class=" + chr(34) + "fade" + chr(34) if fade else ""}><p class="pl-num">{i + 1:02d}</p><p class="pl-text">{text}</p></li>')
    return '<ol class="policy-lines">' + ''.join(out) + '</ol>'


def final_cta(title=None, text=None, button='お問い合わせ', eyebrow='Contact', mail=MAIL, mail_label='メールでのお問い合わせ'):
    """ページ最下部のお問い合わせ欄（全ページ共通）。ボタンは1つ、電話は小さく添える。
    title・text を渡すと、そのページ向けの文にできる（アライアンス事業：2026-10-07 お客様の要望）。
    電話の下にメールアドレスも添える（標準は MAIL、採用情報は RECRUIT_MAIL、アライアンス事業は ALLIANCE_MAIL。見出しは mail_label）。メールの案内が要らないページは mail=None。"""
    mail_line = f'\n      <p class="contact-cta-tel contact-cta-mail fade">{mail_label}<a href="mailto:{mail}">{mail}</a></p>' if mail else ''
    title = title or '<span>保険やお金について</span><br><span>気になることから</span><span>ご相談ください</span>'
    text = text or '保険の見直しや家計、これからのお金について、まずはお気軽にお問い合わせください。'
    return f'''  <section class="contact-cta" id="final-cta">
    <div class="wrap contact-cta-inner">
      <p class="eyebrow fade">{eyebrow}</p>
      <h2 class="fade">{title}</h2>
      <p class="text fade">{text}</p>
      <p class="contact-cta-actions fade">
        <a class="btn btn-primary" href="/contact/">{button}{ARROW}</a>
      </p>
      <p class="contact-cta-tel fade">お電話でのお問い合わせ<a href="{TEL_HREF}">{TEL}</a></p>{mail_line}
    </div>
  </section>
'''


# ───────────────────────── 各ページ ─────────────────────────

# ───── 私たちについて（2026-10-08 お客様の構成案で作り直し） ─────
# ①理念（冒頭。トップと同じキャッチ）②使命 ③3つの価値観 ④事業を通じた価値創造 ⑤強み ⑥目指す未来 ⑦企業文化（構成案の「必要に応じて」）。
# 「今後の事業展開」は構成案の「まだ始めていない事業は載せない」に合わせて入れていない。
# 見出しには「。」「、」を入れない。段の見出しのすぐ下に説明文を置かない（2026-10-08 松本さん）
AB_VALUES = [
    ('partner', 'Trust', '信頼', '誠実であること', 'お客様やパートナー企業との信頼関係を何よりも大切に。一つひとつの約束と期待に誠実に向き合い、長く選ばれ続ける企業を目指します。'),
    ('growth', 'Challenge', '挑戦', '変化を恐れないこと', '既存の枠組みにとらわれず、新しいサービスや事業の可能性を追求。時代とともに変化するニーズに応え、成長し続ける企業を目指します。'),
    ('network', 'Co-Creation', '共創', 'つながりを価値に変えること', '人と人、企業と企業。それぞれの強みをつなぎ、新たな価値を生み出す。一社だけでは実現できない可能性を広げていきます。'),
]

# 写真は仮（構成案の写真は手元にないので、今ある生成AIの写真から近いもの）
AB_BUSINESS = [
    ('Insurance Business', '保険事業', ('人生と経営に', '確かな安心を'), 'recruit-work-consult.jpg', '50% 55%', [
        '保険は、単に万が一に備えるためのものではありません。',
        '人生のさまざまな転機や企業の成長に寄り添い、安心して未来を描くための大切な選択肢の一つです。',
        '私たちは生命保険・損害保険を通じて、お客様一人ひとりの状況に合わせた保障とリスク対策を考えます。',
    ], [('個人のお客様', '/personal/'), ('法人のお客様', '/corporate/')]),
    ('Alliance Business', 'アライアンス事業', ('企業のつながりから', '暮らしに新しい価値を'), 'scene-home.jpg', '50% 60%', [
        'アライアンス事業では、不動産会社をはじめとするパートナー企業との連携を通じて、新生活に必要なライフラインサービスをご案内しています。',
        'お客様の利便性を高めるとともに、パートナー企業のサービス価値の向上にも貢献します。',
        '企業同士のつながりから、より良いサービスを生み出していきます。',
    ], [('アライアンス事業', '/partner/')]),
]

AB_STRENGTHS = [
    ('shield', '総合的な提案力', '生命保険・損害保険を通じて、個人と法人の多様なリスクに対応します。'),
    ('network', '企業間ネットワーク', '不動産関連企業との提携を生かし、サービスを必要とするお客様へ届けます。'),
    ('family', 'お客様に寄り添う姿勢', '一人ひとりの状況を丁寧に理解し、必要な選択肢を一緒に考えます。'),
    ('rocket', '新しい価値への挑戦', '既存事業の枠を超え、暮らしや企業活動を支える新たな領域へ挑戦します。'),
]


# トップの入口タイル（.entry）を小さくしたもの（2026-10-08 松本さん「ここにTOPページと同じタイルを小さめに。あまり強調しない程度に」）
# 写真はトップのタイルと同じ。見た目は src/refine.css の .mini-entry
MINI_TILES = {
    '/personal/': ('Personal', '個人のお客様', 'service-insurance.jpg'),
    '/corporate/': ('Corporate', '法人のお客様', 'cta-final.jpg'),
    '/partner/': ('Alliance', 'アライアンス事業', 'scene-home.jpg'),
    '/recruitment/': ('Recruit', '採用情報', 'cta.jpg'),
    '/about/': ('About Us', '私たちについて', 'mission-1.jpg'),
}


def mini_tiles(hrefs):
    tiles = ''.join(f'<a class="mini-entry" href="{h}"><img src="/images/{MINI_TILES[h][2]}" alt="" onerror="this.remove()">'
                    f'<span class="mini-entry-body"><span class="eyebrow">{MINI_TILES[h][0]}</span>'
                    f'<span class="mini-entry-title">{MINI_TILES[h][1]}</span></span>{ARROW}</a>' for h in hrefs)
    return f'<div class="mini-entries">{tiles}</div>'


def page_about():
    # 冒頭（2026-10-08 松本さん「トップと同じなので変えて。JSはそのままで写真とコピーだけ」）：
    # 動きは個人・法人と同じ rf_hero。コピー・英字は松本さん指定（見出しの「、」は外した）。
    # 写真はトップ（街の四季）・個人・法人の冒頭と重ならないもの：空と海・相談の席・家族・お店の店先
    hero = rf_hero('私たちについて', 'Our Philosophy', ('信頼を重ね', '挑戦から新たな価値を'),
                   ('一人ひとり、一社一社に向き合い', '期待のその先につながるサービスを届けます'),
                   'お問い合わせ', (('mission-1.jpg', '50% 60%'), ('about-hero.jpg', '50% 70%'),
                                   ('hero-summer.jpg', '60% 35%'), ('scene-shop.jpg', '60% 50%')),
                   ('TRUST', 'CHALLENGE', 'VALUE'))
    values = ''.join(f'''
        <li class="ab-value fade">
          <span class="ab-value-icon">{ps_icon(k)}</span>
          <div>
            <p class="ab-value-en">Value {i + 1:02d} — {en}</p>
            <h3>{ja}<span>{sub}</span></h3>
            <p>{text}</p>
          </div>
        </li>''' for i, (k, en, ja, sub, text) in enumerate(AB_VALUES))
    business = ''.join(f'''
        <article class="ab-biz fade">
          <div class="ab-biz-photo"><img src="/images/{img}" alt="" style="object-position:{pos}" onerror="this.remove()"></div>
          <div class="ab-biz-body">
            <p class="ab-biz-en">{en}<span>{ja}</span></p>
            <h3><span>{title[0]}</span><br><span>{title[1]}</span></h3>
            {''.join(f'<p>{t}</p>' for t in texts)}
            {mini_tiles([href for _, href in links])}
          </div>
        </article>''' for en, ja, title, img, pos, texts, links in AB_BUSINESS)
    strengths = ''.join(f'''
        <li class="fade">{ps_icon(k)}<h3>{t}</h3><p>{x}</p></li>''' for k, t, x in AB_STRENGTHS)
    return hero + f'''
  <section class="section ab-mission" id="mission">
    <div class="wrap">
      <p class="eyebrow fade">Our Mission</p>
      <h2 class="fade">私たちの使命</h2>
      <div class="ab-mission-grid">
        <p class="ab-mission-words fade"><span>安心を届ける</span><span>つながりを生み出す</span><span>未来を支える</span></p>
        <div class="ab-mission-body fade">
          <p>私たちLFグループは、保険とライフラインという、暮らしや企業活動に欠かせない分野で事業を展開しています。</p>
          <p>保険事業では、一人ひとりの人生や企業経営に寄り添い、将来への不安やリスクに備えるお手伝いを。</p>
          <p>アライアンス事業では、企業同士のつながりを生かし、新生活を迎えるお客様に必要なサービスを届けています。</p>
          <p>異なる事業に見えても、根底にある想いは同じです。</p>
          <p class="ab-mission-quote">人と企業が<br class="sp">より安心して未来に向かえる環境をつくること</p>
          <p>私たちは、その実現に向けて価値を提供し続けます。</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section bg-blue" id="values">
    <div class="wrap">
      <p class="eyebrow fade">Our Value</p>
      <h2 class="fade">大切にしている3つの価値観</h2>
      <ol class="ab-value-list">{values}
      </ol>
    </div>
  </section>

  <section class="section" id="business">
    <div class="wrap">
      <p class="eyebrow fade">Our Business</p>
      <h2 class="fade">事業を通じた価値創造</h2>
      <div class="ab-biz-list">{business}
      </div>
    </div>
  </section>

  <section class="section bg-blue" id="strength">
    <div class="wrap">
      <p class="eyebrow fade">Our Strength</p>
      <h2 class="fade">LFグループの強み</h2>
      <ul class="ab-strength-list">{strengths}
      </ul>
      <p class="ab-strength-link fade"><a class="link-arrow" href="/#numbers">数字で見るLFグループ{ARROW}</a></p>
    </div>
  </section>

  <section class="section ab-vision" id="vision">
    <div class="wrap">
      <p class="eyebrow fade">Our Vision</p>
      <h2 class="fade">私たちが目指す未来</h2>
      <div class="ab-vision-grid">
        <div class="ab-vision-photo fade"><img src="/images/city-autumn.jpg" alt="" onerror="this.remove()"></div>
        <div class="ab-vision-body fade">
          <h3><span>新しい挑戦が</span><br><span>新しい未来をつくる</span></h3>
          <p>社会の変化とともに、人々の暮らしや企業が抱える課題も変わり続けています。</p>
          <p>私たちは、保険事業とアライアンス事業で培う経験やつながりを基盤に、さらなる価値の創造に挑戦していきます。</p>
          <ul class="ab-vision-for">
            <li>お客様にとって<b>より身近で頼れる存在へ</b></li>
            <li>パートナー企業にとって<b>ともに成長できる存在へ</b></li>
            <li>働く仲間にとって<b>一人ひとりの可能性を発揮できる場所へ</b></li>
          </ul>
          <p class="ab-vision-catch">人と企業の可能性を<br class="sp">その先へ</p>
          <p>LFグループは、これからも挑戦を続けます。</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section bg-blue" id="culture">
    <div class="wrap">
      <p class="eyebrow fade">Our Culture</p>
      <h2 class="fade">働く仲間を大切にする企業文化</h2>
      <div class="ab-culture fade">
        <p class="ab-culture-catch">一人ひとりが自分らしく働き<br>挑戦できる環境を</p>
        <p>私たちは、個性と自主性を尊重し、仲間とともに成長できる組織を目指しています。</p>
        {mini_tiles(['/recruitment/'])}
      </div>
    </div>
  </section>

''' + ceo_message_block() + final_cta()


# ───── 個人のお客様（2026-10-08 お客様の構成案に合わせて作り直し） ─────
# お客様の「個人用のページをこんな構成にしたい、今の文は捨てても問題ない」から。文言はお客様の構成案のまま。
# ①ファーストビュー ②こんなお悩み ③6つの相談メニュー ④大切にしていること ⑤ご相談の流れ ⑥よくあるご質問 ⑦最後の問い合わせ
# それまでの「強み・サービス（取り扱い保険）・事故対応・アライアンスサービス・勧誘方針」は外した（勧誘方針はフッターから見られる）

# 線のアイコン（24×24。色は文字色に合わせる）
PS_ICONS = {
    'medical': '<path d="M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.8 0-3 .5-4.5 2-1.5-1.5-2.7-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4 3 5.5l7 7Z"/><path d="M3.5 12H9l1.5-2.5 2 4.5 1.5-2H20.5"/>',
    'family': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    'growth': '<path d="M22 7l-8.5 8.5-5-5L2 17"/><path d="M16 7h6v6"/>',
    'education': '<path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/><path d="M22 10v6"/>',
    'home': '<path d="m3 10 9-7 9 7v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/>',
    'wallet': '<path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v3"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-3"/><path d="M21 11h-4a2 2 0 0 0 0 4h4z"/>',
    'talk': '<path d="M14 9a2 2 0 0 1-2 2H6l-4 4V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2z"/><path d="M18 9h2a2 2 0 0 1 2 2v11l-4-4h-6a2 2 0 0 1-2-2v-1"/>',
    'balance': '<path d="M12 3v18"/><path d="M7 21h10"/><path d="M3 7h18"/><path d="M6 7l-3 7a3 3 0 0 0 6 0z"/><path d="M18 7l-3 7a3 3 0 0 0 6 0z"/>',
    'person': '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/>',
    'helmet': '<path d="M2 18h20"/><path d="M4 18v-2a8 8 0 0 1 16 0v2"/><path d="M10 9V5h4v4"/>',
    'factory': '<path d="M2 21h20"/><path d="M3 21V10l6 4v-4l6 4V4h6v17"/><path d="M8 18h1M13 18h1"/>',
    'alert': '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
    'shield': '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    'chart': '<path d="M3 3v18h18"/><path d="M8 17v-4"/><path d="M13 17V9"/><path d="M18 17V5"/>',
    'network': '<circle cx="12" cy="5" r="2.5"/><circle cx="5" cy="18" r="2.5"/><circle cx="19" cy="18" r="2.5"/><path d="M12 7.5v4M12 11.5 6.5 16M12 11.5l5.5 4.5"/>',
    'rocket': '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>',
    'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'phone': '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>',
    'yen': '<circle cx="12" cy="12" r="9"/><path d="m8.5 7 3.5 5 3.5-5M12 12v6M9 13h6M9 16h6"/>',
    'smile': '<circle cx="12" cy="12" r="9"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><path d="M9 9h.01M15 9h.01"/>',
    'bolt': '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    'flame': '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.4-.5-2-1-3-1.1-2.1-.2-4 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.2.4-2.3 1-3.2.3 1.6 1.4 2.7 2.5 2.7z"/>',
    'drop': '<path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5S12.5 5.5 12 3c-.5 2.5-2 4.9-4 6.5S5 13 5 15a7 7 0 0 0 7 7z"/>',
    'wifi': '<path d="M5 12.6a10 10 0 0 1 14 0"/><path d="M8.5 16.1a5 5 0 0 1 7 0"/><path d="M2 8.8a15 15 0 0 1 20 0"/><path d="M12 20h.01"/>',
    'glass': '<path d="M6 3h12l-1.5 17a2 2 0 0 1-2 1.8h-5a2 2 0 0 1-2-1.8z"/><path d="M6.5 9h11"/>',
    'building': '<path d="M3 21h18"/><path d="M5 21V5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v16"/><path d="M16 9h3a1 1 0 0 1 1 1v11"/><path d="M9 7h3M9 11h3M9 15h3"/>',
    'partner': '<path d="m11 17 2 2a1 1 0 1 0 3-3"/><path d="m14 14 2.5 2.5a1 1 0 1 0 3-3l-3.88-3.88a3 3 0 0 0-4.24 0l-.88.88a1 1 0 1 1-3-3l2.81-2.81a5.79 5.79 0 0 1 7.06-.87l.47.28a2 2 0 0 0 1.42.25L21 4"/><path d="m21 3 1 11h-2"/><path d="M3 3 2 14l6.5 6.5a1 1 0 1 0 3-3"/><path d="M3 4h8"/>',
}


def ps_icon(key):
    return (f'<svg class="ps-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{PS_ICONS[key]}</svg>')


PS_WORRIES = [
    ('medical', '今の医療保険で十分なのか分からない'),
    ('family', '万が一のとき、家族の生活が心配'),
    ('growth', '将来のために資産形成を始めたい'),
    ('education', '子どもの教育費を準備したい'),
    ('home', '相続について何から始めればいいか分からない'),
    ('wallet', '毎月の固定費や保険料を見直したい'),
]

# 写真は仮（2026-10-08）：お客様の構成案の写真は手元にないので、今ある生成AIの写真から近いものを当てている。
# 写真をいただいたら images/ に置いてここを差し替える
PS_MENUS = [
    ('Medical', '医療・がんへの備え', '病気やケガによる入院・治療費など、もしもの医療費に備えるためのご相談。', 'scene-kitchen.jpg', '50% 50%'),
    ('Family', '死亡保障・家族への備え', '大切な家族の暮らしを守るために、必要な保障を一緒に考えます。', 'service-insurance.jpg', '50% 60%'),
    ('Asset', '資産形成・老後資金', '将来の生活や老後に向けた資金準備について、目的に合った方法を考えます。', 'life-winter.jpg', '62% 35%'),
    ('Inheritance', '相続・資産承継', '大切な財産と想いを次の世代へ。相続に向けた備えをサポートします。', 'life-spring2.jpg', '70% 45%'),
    ('Education', '教育資金の準備', '進学や将来の教育費に向けて、無理のない資金準備を考えます。', 'life-autumn.jpg', '62% 50%'),
    ('Household', '家計診断・保険の見直し', '収入・支出・保障内容を整理して、家計に合った備え方を見つけます。', 'scene-dining.jpg', '60% 60%'),
]

PS_VALUES = [
    ('talk', '<span>まずはお話を</span><span>聞くことから</span>', 'お客様のライフスタイルや将来の希望を丁寧にお伺いし、今必要な備えを一緒に考えます。'),
    ('balance', '<span>必要なものを</span><span>　必要な分だけ</span>', '現在の保障や公的制度も踏まえ、過不足のない保障設計を目指します。'),
    ('partner', '<span>契約後も続く</span><span>パートナーシップ</span>', '結婚・出産・住宅購入など、ライフステージの変化に応じた見直しをサポートします。'),
]

PS_FLOW = [
    ('お問い合わせ・ご予約', 'WEBフォームなどから、ご希望の相談内容をお知らせください。'),
    ('ヒアリング・現状確認', '家計や保険の加入状況、将来の希望などを整理します。'),
    ('プランのご提案', '必要に応じて保障や資金準備の方法をご案内します。'),
    ('アフターフォロー', 'ご契約後も状況の変化に合わせてサポートします。'),
]

# ★要確認：質問はお客様の構成案のまま。回答は構成案になかったので、こちらで書いた下書き（.note-draft の印付き）
PS_FAQ = [
    ('相談だけでも大丈夫ですか？',
     'はい、ご相談だけでも大丈夫です。お話を伺ったうえで、必要な場合にだけご提案します。無理にご契約をおすすめすることはありません。'),
    ('すでに加入している保険の見直しもできますか？',
     'はい、できます。今ご加入の保険の内容を一緒に確認し、今の暮らしやご家族の状況に合っているかを整理します。'),
    ('資産形成についても相談できますか？',
     'はい、ご相談いただけます。将来の生活や老後に向けた資金準備について、目的に合った方法を一緒に考えます。'),
    ('相談には何を用意すればいいですか？',
     '特別なご用意は必要ありません。保険の見直しをご希望の場合は、今ご加入の保険証券などをお持ちいただくと、スムーズにご案内できます。'),
]


def rf_hero(crumb, eyebrow, title, lead, button, photos, big, still=False):
    """個人・法人のお客様の冒頭（2026-10-08 松本さん「TOPページのFVの見せ方を取り入れて」）。
    トップと同じ部品（src/recruit-fv.css・recruit-fv.js）：写真が4.5秒ごとに斜めのマスクで切り替わり金の光が走る、
    大きな英字（明朝体系）、1文字ずつ出る白い明朝の見出し、マウスとスクロールで奥行き。
    トップ専用の指定（ページ全体を紺にする等）は .rf-sub で外す。title・lead は2行（(1行目, 2行目)）
    still=True：写真のカメラワーク（マウス・スクロールで写真だけずれる動きと拡大）を止める（会社概要。2026-10-09 松本さん）"""
    imgs = ''.join('<img class="%s" src="/images/%s" alt="" style="object-position:%s" %s onerror="this.remove()">'
                   % ('is-on' if n == 0 else '', f, pos, 'fetchpriority="high"' if n == 0 else 'data-eager') for n, (f, pos) in enumerate(photos))
    words = ''.join(f'<span>{w}</span>' for w in big)
    return f'''  <section class="rf rf-a rf-v rf-top rf-wipe rf-serif rf-sub{' rf-still' if still else ''}" data-fx="a" data-stay="4500">
    <div class="rf-media">{imgs}</div>
    <p class="rv-big" aria-hidden="true">{words}</p>
    {GOLD_WIPE}
    <div class="wrap rc-fv-copy">
      <ol class="crumb" aria-label="パンくずリスト"><li><a href="/">トップ</a></li><li aria-current="page">{crumb}</li></ol>
      <p class="eyebrow">{eyebrow}</p>
      <h1 class="rc-fv-title rv-title"><span>{title[0]}</span><span>{title[1]}</span></h1>
      <p class="rc-fv-lead">{lead[0]}<br>{lead[1]}</p>
      <p class="rc-links"><a class="btn btn-primary" href="/contact/">{button}{ARROW}</a></p>
    </div>
    <small class="rf-photo-note">写真はイメージです</small>
  </section>
'''


def with_rf(html_):
    """トップのFVの部品（CSS・JS・英字のフォント）を読み込ませる"""
    v = hashlib.sha1(((SRC / 'recruit-fv.css').read_text() + (SRC / 'recruit-fv.js').read_text()).encode()).hexdigest()[:8]
    return (html_.replace('</head>', f'<link rel="stylesheet" href="/assets/recruit-fv.css?v={v}">\n</head>', 1)
                 .replace('</body>', f'<script src="/assets/recruit-fv.js?v={v}"></script>\n</body>', 1)
                 .replace('family=Montserrat:wght@500;600', 'family=Cormorant+Garamond:wght@300;400;500&family=Montserrat:wght@500;600', 1))


def ps_worries(title, items, answer, bg='bg-blue', band=False, eyebrow='Worries'):
    """お悩みの段（個人・法人で共通）。items は (アイコン, 一文)。
    band=True：段の頭を、トップの「FIND YOUR PAGE」のような狭い見出しの帯にする（2026-10-08 松本さん「TOPのような狭めに」「色はそのままでOK」。個人・法人のお客様）。
    問いかけの見出しは帯の中に残す"""
    lis = ''.join(f'''
          <li class="fade">{ps_icon(k)}<p>{t}</p></li>''' for k, t in items)
    if band:
        head = f'''  <div class="ps-band" id="worries">
    <div class="wrap">
      <p class="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
    </div>
  </div>
  <section class="section {bg} ps-worries ps-worries-banded">
    <div class="wrap">'''
    else:
        head = f'''  <section class="section {bg} ps-worries" id="worries">
    <div class="wrap">
      <p class="eyebrow fade">{eyebrow}</p>
      <h2 class="fade">{title}</h2>'''
    return f'''
{head}
      <ul class="ps-worry-list">{lis}
      </ul>
      <p class="ps-worries-answer fade">{answer}</p>
    </div>
  </section>
'''


def ps_values(eyebrow, title, items, bg='bg-blue'):
    """大切にしていること・選ばれる理由（3つのカード）。items は (アイコン, 見出し, 本文)"""
    cards = ''.join(f'''
        <article class="ps-value fade">
          <p class="ps-value-head">{ps_icon(k)}<span>{i + 1:02d}</span></p>
          <h3>{t}</h3>
          <p>{x}</p>
        </article>''' for i, (k, t, x) in enumerate(items))
    return f'''
  <section class="section {bg}" id="values">
    <div class="wrap">
      <p class="eyebrow fade">{eyebrow}</p>
      <h2 class="fade">{title}</h2>
      <div class="ps-value-list">{cards}
      </div>
    </div>
  </section>
'''


def ps_flow(items, bg='', eyebrow='Flow', title='ご相談の流れ'):
    steps = ''.join(f'''
        <li class="fade"><p class="ps-step">STEP<b>{i + 1:02d}</b></p><h3>{t}</h3><p>{x}</p></li>''' for i, (t, x) in enumerate(items))
    return f'''
  <section class="section {bg}" id="flow">
    <div class="wrap">
      <p class="eyebrow fade">{eyebrow}</p>
      <h2 class="fade">{title}</h2>
      <ol class="ps-flow">{steps}
      </ol>
    </div>
  </section>
'''


def ps_faq(items, bg='bg-blue'):
    """よくあるご質問（開け閉めできる）。回答は下書きなので .note-draft の印を付ける"""
    qa = ''.join(f'''
        <details class="ps-faq-item fade">
          <summary><span class="ps-q">Q</span><span class="ps-faq-q">{q}</span><span class="ps-faq-mark" aria-hidden="true"></span></summary>
          <div class="ps-faq-a"><span class="ps-a">A</span><p>{a}</p></div>
        </details>''' for q, a in items)
    return f'''
  <section class="section {bg}" id="faq">
    <div class="wrap">
      <p class="eyebrow fade">FAQ</p>
      <h2 class="fade">よくあるご質問</h2>
      <div class="ps-faq-list">
        <p class="note-draft fade">回答は下書きです（ご確認ください）</p>{qa}
      </div>
    </div>
  </section>
'''


def page_personal():
    hero = rf_hero('個人のお客様', 'Personal Financial Consulting', ('これからの人生に', 'お金の安心を'),
                   ('保険の見直しから資産形成・教育資金・相続まで', '一人ひとりのライフプランに合わせて一緒に考えます'),
                   '無料相談はこちら', (('hero.jpg', '72% 40%'), ('service-insurance.jpg', '50% 60%'),
                                       ('life-autumn.jpg', '62% 45%'), ('life-spring2.jpg', '70% 45%')),
                   ('PEACE', 'OF MIND', 'FOR LIFE.'))
    menus = ''.join(f'''
        <article class="ps-menu fade">
          <div class="ps-menu-photo"><img src="/images/{img}" alt="" style="object-position:{pos}" onerror="this.remove()"></div>
          <p class="ps-menu-num">{i + 1:02d}<span>{en}</span></p>
          <h3>{title}</h3>
          <p>{text}</p>
        </article>''' for i, (en, title, text, img, pos) in enumerate(PS_MENUS))
    return (hero
            + ps_worries('<span>お金や将来のこと</span><br><span>こんな不安は</span><span>ありませんか？</span>', PS_WORRIES,
                         'そんなお悩みを<span class="pc">　</span><br class="sp">LFグループが一緒に整理します', band=True)
            + f'''
  <section class="section" id="menu">
    <div class="wrap">
      <p class="eyebrow fade">Consultation Menu</p>
      <h2 class="fade">6つの相談メニュー</h2>
      <div class="ps-menu-list">{menus}
      </div>
    </div>
  </section>
'''
            + ps_values('Our Approach', 'LFグループが<br class="sp">大切にしていること', PS_VALUES)
            + ps_flow(PS_FLOW) + ps_faq(PS_FAQ) + '\n'
            + final_cta(title='<span>お金の不安を</span><br><span>未来の安心へ</span>',
                        text='保険のことも、将来のお金のことも。<br>まずはお気軽にご相談ください。',
                        button='無料相談を予約する', mail=MAIL))


# ───── 法人のお客様（2026-10-08 お客様の構成案で作り直し） ─────
# お客様の「法人のお客様も同様に構成の見直しをして、文章は作り直してオッケー」から。文言は構成案をもとにした。
# ①ファーストビュー ②経営者のお悩み ③法人向けサービス（3つの分類・13項目）④選ばれる理由 ⑤経営ステージ別のご提案
# ⑥ご相談の流れ ⑦よくあるご質問 ⑧最後の問い合わせ。
# 構成案の「保険代理店として注意したい表現」に合わせ、節税をうたわない・採用や定着が上がると断定しない・
# 「すべてのリスクをカバー」と書かない。公開前に、保険会社の募集文書のルールで確認していただく
CO_WORRIES = [
    ('person', '経営者に万が一のことがあった場合、事業を継続できるか不安'),
    ('wallet', '役員退職金や従業員の退職金を計画的に準備したい'),
    ('family', '福利厚生を充実させ、人材の採用・定着につなげたい'),
    ('partner', '後継者への事業承継や相続対策を考えたい'),
    ('balance', '事故やトラブルによる高額な損害賠償に備えたい'),
    ('helmet', '従業員の労災事故や雇用トラブルに備えたい'),
    ('factory', '火災・自然災害で事業が止まるリスクを減らしたい'),
    ('alert', 'サイバー攻撃や情報漏えいへの対策が心配'),
]

# 3つの分類と13の相談領域。写真は分類ごとに1枚（今ある生成AIの写真。いただいたら差し替える）
CO_SERVICES = [
    ('A', 'Protect the Future', '経営者・企業の未来を守る', 'recruit-work-consult.jpg', '50% 55%', [
        ('経営者の死亡保障', '経営者に万が一のことがあった際の運転資金や借入金の返済など、事業の継続に必要な資金への備えを考えます。'),
        ('経営者・役員の医療保障', '病気やケガによる入院・治療に備え、経営者や役員の健康リスクを踏まえた保障を検討します。'),
        ('役員退職金・退職慰労金の準備', '将来の役員退職金に向けた、計画的な資金準備をサポートします。資金が必要になる時期や、保険商品の特性を踏まえて検討します。'),
        ('事業承継・相続対策', '後継者への円滑な事業承継に向けて、納税資金や株式の承継に伴う資金需要への備えを考えます。'),
    ]),
    ('B', 'Protect the Team', '従業員と組織を守る', 'recruit-work-team.jpg', '50% 50%', [
        ('福利厚生制度の充実', '従業員の医療保障や万が一への備えなど、安心して働ける環境づくりを支援します。'),
        ('従業員退職金の積立・準備', '従業員の将来を支える退職金制度について、企業の財務状況や制度設計に合わせた準備の方法を検討します。'),
        ('労働災害への備え', '業務中の事故や従業員のケガなどに備え、政府労災保険を補完する民間の保険を検討します。'),
        ('雇用関連賠償責任', 'ハラスメントや不当解雇など、雇用に関するトラブルによって企業が負う賠償責任への備えを検討します。'),
    ]),
    ('C', 'Protect the Business', '事業活動のリスクを守る', 'scene-shop.jpg', '60% 50%', [
        ('損害賠償責任への備え', '施設内の事故、業務上の過失、製造物による事故など、第三者への賠償リスクに備えます。'),
        ('火災・自然災害への備え', '建物や設備、商品などの財産を、火災・風災・水災などのリスクから守るための対策を考えます。'),
        ('休業損失・事業中断への備え', '事故や災害によって事業が止まった場合の利益の減少や、その間も発生する費用への備えを検討します。'),
        ('サイバーリスク・情報漏えい対策', 'サイバー攻撃や個人情報の漏えいによる賠償責任、事故対応の費用などへの備えを検討します。'),
        ('社用車・営業車両の自動車保険', '社用車や営業車両の事故に備え、台数や使い方に合わせた自動車保険をご提案します。'),
    ]),
]

CO_REASONS = [
    ('shield', '<span>生命保険・損害保険の</span><span>両面からサポート</span>', '経営者の万が一への備えから、従業員の福利厚生、事業活動に伴う賠償リスクまで。企業を取り巻くさまざまなリスクを幅広く検討します。'),
    ('chart', '<span>企業の成長段階に</span><span>合わせた保障設計</span>', '創業期、成長期、成熟期、事業承継期。企業の成長とともに変化するリスクや資金需要を踏まえ、適切な備えを一緒に考えます。'),
    ('partner', '<span>長期的な</span><span>経営パートナーとして</span>', '保険の加入時だけでなく、事業環境や組織体制の変化に応じた保障の見直しをサポートします。企業の未来を見据えた関係づくりを大切にします。'),
]

CO_STAGES = [
    ('Startup', '創業期', '限られた資金の中で、経営上の重大なリスクに優先順位をつける。', '経営者の死亡保障・賠償責任・事業用の火災保険'),
    ('Growth', '成長期', '事業の拡大や従業員の増加に伴うリスクに備える。', '福利厚生・労働災害・雇用関連賠償・休業損失'),
    ('Stability', '成熟期', '経営基盤の安定と、将来に向けた資金準備を進める。', '役員退職金・従業員退職金・保障全体の見直し'),
    ('Succession', '事業承継期', '次の世代への円滑な引き継ぎと、必要な資金の確保を考える。', '事業承継・相続・死亡保障・退職慰労金'),
]

CO_FLOW = [
    ('お問い合わせ', '経営上のお悩みや、見直したい保険について、お気軽にご相談ください。'),
    ('経営課題・リスクのヒアリング', '業種、事業の規模、従業員数、加入中の保険などを確認します。'),
    ('リスク分析・保障のご提案', '今の備えを整理し、優先順位を踏まえた対策をご案内します。'),
    ('ご契約・継続的なサポート', 'ご契約後も、事業環境の変化に応じて、保障内容の確認や見直しを行います。'),
]

# ★要確認：質問は構成案のまま。回答は構成案になかったので、こちらで書いた下書き
CO_FAQ = [
    ('現在加入している法人保険の見直しだけでも相談できますか？',
     'はい、見直しだけのご相談も承ります。今ご加入の保険の内容を一緒に確認し、今の事業の状況に合っているかを整理します。'),
    ('生命保険と損害保険をまとめて相談できますか？',
     'はい、まとめてご相談いただけます。経営者や従業員の保障から、事業活動に伴う賠償や財産のリスクまで、全体を見渡して整理します。'),
    ('法人保険を活用した退職金準備はできますか？',
     'はい、ご相談いただけます。資金が必要になる時期や保険商品の特性を踏まえて、準備の方法を一緒に検討します。税務上の取り扱いは契約内容などによって異なるため、必要に応じて税理士などの専門家にご確認ください。'),
    ('小規模な会社でも相談できますか？',
     'はい、会社の規模にかかわらずご相談いただけます。業種や従業員数に合わせて、優先して備えたいリスクから一緒に考えます。'),
    ('相談すると必ず保険に加入しなければいけませんか？',
     'いいえ、ご相談だけでも大丈夫です。お話を伺ったうえで、必要な場合にだけご提案します。無理にご契約をおすすめすることはありません。'),
]


def page_corporate():
    hero = rf_hero('法人のお客様', 'Corporate Risk &amp; Financial Solutions', ('企業の未来を守り', '挑戦を支える'),
                   ('経営者の保障から福利厚生・事業リスク・事業承継まで', '生命保険と損害保険の両面から企業の成長を支えます'),
                   '法人保険について相談する', (('cta-final.jpg', '62% 50%'), ('cta.jpg', '50% 50%'),
                                               ('mission-2.jpg', '50% 50%'), ('recruit-work-team.jpg', '60% 50%')),
                   ('PROTECT', 'YOUR', 'BUSINESS.'))
    n = 0
    groups = []
    for key, en, title, img, pos, items in CO_SERVICES:
        rows = ''
        for t, x in items:
            n += 1
            rows += f'''
            <li class="fade"><p class="co-svc-num">{n:02d}</p><div><h4>{t}</h4><p>{x}</p></div></li>'''
        groups.append(f'''
      <div class="co-svc-group">
        <div class="co-svc-head fade">
          <div class="co-svc-photo"><img src="/images/{img}" alt="" style="object-position:{pos}" onerror="this.remove()"></div>
          <p class="co-svc-en"><b>{key}</b>{en}</p>
          <h3>{title}</h3>
        </div>
        <ol class="co-svc-list">{rows}
        </ol>
      </div>''')
    stages = ''.join(f'''
        <article class="co-stage fade">
          <p class="co-stage-en">{en}</p>
          <h3>{t}</h3>
          <p class="co-stage-text">{x}</p>
          <dl><dt>主なご相談</dt><dd>{c}</dd></dl>
        </article>''' for en, t, x, c in CO_STAGES)
    return (hero
            + ps_worries('<span>企業経営に潜むリスク</span><br><span>その備えは</span><span>万全ですか？</span>', CO_WORRIES,
                         '当てはまる課題から<span class="pc">　</span><br class="sp">LFグループが一緒に整理します', band=True)
            + f'''
  <section class="section" id="service">
    <div class="wrap">
      <p class="eyebrow fade">Service</p>
      <h2 class="fade">法人向けサービス</h2>
      {''.join(groups)}
      <p class="co-svc-note fade">※補償・保障の内容や保険金のお支払いの対象は、保険の種類や契約の条件によって異なります。</p>
    </div>
  </section>
'''
            + ps_values('Why LF Group', 'LFグループが<br class="sp">選ばれる理由', CO_REASONS)
            + f'''
  <section class="section co-stages" id="stage">
    <div class="wrap">
      <p class="eyebrow fade">Business Stage</p>
      <h2 class="fade">経営ステージ別のご提案</h2>
      <div class="co-stage-list">{stages}
      </div>
    </div>
  </section>
'''
            + ps_flow(CO_FLOW) + ps_faq(CO_FAQ) + '\n'
            + final_cta(title='<span>企業の未来に</span><br><span>確かな備えを</span>',
                        text='経営者の保障、従業員の福利厚生、<br>事業活動に伴うさまざまなリスクまで。<br>企業の状況に合わせた対策を一緒に考えます。',
                        button='法人保険の相談を申し込む', eyebrow='Your Business, Our Commitment.', mail=MAIL))


# ───── アライアンス事業（2026-10-08 お客様の構成案で作り直し） ─────
# 不動産会社の経営者・店舗責任者に「提携してみたい」と感じてもらう営業ページ。
# ①ファーストビュー ②アライアンス事業について ③不動産会社のお悩み ④提携による3つのメリット ⑤取扱サービス
# ⑥サービス提供の仕組み ⑦実績 ⑧提携開始までの流れ ⑨よくあるご質問 ⑩提携のお問い合わせ。
# 見出しに「。」「、」を入れない。段の見出しのすぐ下に説明文を置かない（2026-10-08 松本さん）
AL_WORRIES = [
    ('clock', 'ライフラインの案内に時間がかかっている'),
    ('family', '契約業務に集中できる環境をつくりたい'),
    ('phone', '入居者からの問い合わせ対応を減らしたい'),
    ('yen', '仲介業務以外の収益機会を増やしたい'),
    ('smile', '入居者へのサービスを充実させたい'),
    ('partner', '安心して紹介できる提携先を探している'),
]

# 写真は仮（構成案の人物写真は手元にないので、今ある生成AIの写真から近いもの）
AL_MERITS = [
    ('Merit', '業務負担の軽減', '入居者へのライフライン案内をLFグループがサポート。不動産会社のスタッフが本来の仲介業務に集中しやすい環境づくりに貢献します。', 'recruit-work-prepare.jpg', '50% 50%'),
    ('Merit', '顧客満足度の向上', '新生活に必要なサービスをまとめてご案内。入居者が複数の事業者へ個別に問い合わせる手間を減らし、スムーズな新生活のスタートを支援します。', 'scene-kitchen.jpg', '50% 50%'),
    ('Merit', '新たな収益機会の創出', 'ライフラインサービスの紹介を通じて、仲介業務以外の収益機会を創出。提携条件に応じた紹介手数料など、新しい収益モデルの構築をサポートします。', 'recruit-work-learn.jpg', '50% 50%'),
]

AL_SERVICES = [
    ('bolt', 'Electricity', '電気', '新居での電気利用に関するご案内'),
    ('flame', 'Gas', 'ガス', 'ガスの利用開始に関するご案内'),
    ('drop', 'Water', '水道', '水道の利用開始手続きのご案内'),
    ('wifi', 'Internet', 'インターネット', '住環境に合わせた通信サービスのご案内'),
    ('glass', 'Water Server', 'ウォーターサーバー', '暮らしをより快適にするサービスのご案内'),
]

# 実績（2026-10-08 松本さんからいただいた数字）。集計基準日は未定
AL_NUMBERS = [('提携店舗数', '126', '店舗'), ('累計ご案内件数', '6,230', '件'), ('月間ご案内件数', '260', '件'), ('前年比取扱件数', '133', '%')]

AL_FLOW = [
    ('お問い合わせ', '事業提携に関するご相談を、お問い合わせページ・お電話・メールからお寄せください。'),
    ('サービス・提携条件のご説明', 'サービス内容や紹介方法、提携条件などをご説明します。'),
    ('提携契約・運用方法の確認', '契約内容やお客様へのご案内方法、情報連携の流れなどを確認します。'),
    ('サービス提供開始', '提携開始後も、運用上のご相談や改善に向けたサポートを行います。'),
]

# ★要確認：質問は構成案のまま。回答は構成案になかったので、こちらで書いた下書き
AL_FAQ = [
    ('提携にあたって初期費用は必要ですか？',
     '提携の条件によって異なります。サービス内容や紹介方法とあわせてご説明しますので、まずはお気軽にお問い合わせください。'),
    ('小規模な不動産会社でも提携できますか？',
     'はい、店舗の規模にかかわらずご相談いただけます。ご案内の件数や運用方法に合わせて、無理のない形を一緒に考えます。'),
    ('お客様への案内はどこまで対応してもらえますか？',
     'サービスのご案内から、ご希望の確認、各サービスのお申し込みのサポートまでをLFグループが行います。店舗の皆様にお願いする作業は、提携の際にご説明します。'),
    ('既に他社のライフライン紹介サービスを利用していますが、相談できますか？',
     'はい、ご相談いただけます。今の運用を伺ったうえで、併用や切り替えの方法を一緒に検討します。'),
    ('提携後のサポートはありますか？',
     'はい。提携開始後も、運用上のご相談や改善に向けたサポートを継続して行います。'),
]


def page_partner():
    hero = rf_hero('アライアンス事業', 'Alliance Business', ('企業のつながりを', '新たな価値へ'),
                   ('不動産会社とともに新生活をもっと快適に', 'ライフラインのご案内で新たな価値創出を支えます'),
                   '事業提携について相談する', (('scene-home.jpg', '60% 55%'), ('service-lifeline.jpg', '50% 50%'),
                                               ('service-internet.jpg', '50% 40%'), ('mission-2.jpg', '50% 50%')),
                   ('CONNECT', 'FOR NEW', 'VALUE.'))
    merits = ''.join(f'''
        <article class="ps-menu fade">
          <div class="ps-menu-photo"><img src="/images/{img}" alt="" style="object-position:{pos}" onerror="this.remove()"></div>
          <p class="ps-menu-num">{i + 1:02d}<span>{en}</span></p>
          <h3>{title}</h3>
          <p>{text}</p>
        </article>''' for i, (en, title, text, img, pos) in enumerate(AL_MERITS))
    services = ''.join(f'''
        <li class="fade">{ps_icon(k)}<p class="al-svc-en">{en}</p><h3>{ja}</h3><p>{x}</p></li>''' for k, en, ja, x in AL_SERVICES)
    numbers = ''.join(f'''
        <li class="fade"><p class="al-num-label">{label}</p><p class="al-num-value">{value}<small>{unit}</small></p></li>''' for label, value, unit in AL_NUMBERS)
    return (hero + f'''
  <section class="section" id="about-alliance">
    <div class="wrap">
      <p class="eyebrow fade">About Alliance</p>
      <h2 class="fade">アライアンス事業について</h2>
      <div class="ab-biz-list">
        <article class="ab-biz fade">
          <div class="ab-biz-photo"><img src="/images/scene-dining.jpg" alt="" style="object-position:60% 55%" onerror="this.remove()"></div>
          <div class="ab-biz-body">
            <p class="ab-biz-en">About Our Business</p>
            <h3><span>新生活のスタートを</span><br><span>もっとスムーズに</span></h3>
            <p>LFグループのアライアンス事業は、不動産会社との提携を通じて、新生活を迎えるお客様に必要なライフラインサービスをご案内する事業です。</p>
            <p>電気・ガス・水道・インターネットなど、引越しに伴うさまざまな手続きをサポート。</p>
            <p>不動産会社の業務効率化と、お客様の利便性向上を両立するサービスを提供します。</p>
          </div>
        </article>
      </div>
    </div>
  </section>
'''
            + ps_worries('<span>入居者対応に関する</span><br><span>こんな課題を</span><span>感じていませんか？</span>', AL_WORRIES,
                         'その課題を<span class="pc">　</span><br class="sp">LFグループとの提携で一緒に解決します', band=True, eyebrow='Your Challenges')
            + f'''
  <section class="section" id="merit">
    <div class="wrap">
      <p class="eyebrow fade">Our Solutions</p>
      <h2 class="fade">提携による3つのメリット</h2>
      <div class="ps-menu-list al-merits">{merits}
      </div>
    </div>
  </section>

  <section class="section bg-blue" id="services">
    <div class="wrap">
      <p class="eyebrow fade">Our Services</p>
      <h2 class="fade"><span>新生活に必要なサービスを</span><br class="sp"><span>ワンストップで</span></h2>
      <ul class="al-svc-list">{services}
      </ul>
    </div>
  </section>

  <section class="section" id="how-it-works">
    <div class="wrap">
      <p class="eyebrow fade">How It Works</p>
      <h2 class="fade">サービス提供の仕組み</h2>
      <ol class="al-how fade">
        <li>{ps_icon('building')}<h3>不動産会社</h3><p>新生活を迎えるお客様へサービスをご紹介</p></li>
        <li class="al-how-lf"><p class="al-how-en">Alliance Partner</p><h3>LF GROUP</h3><p>お客様へのご案内・ご希望の確認・各サービスへのお申し込みサポート</p></li>
        <li>{ps_icon('home')}<h3>新生活を迎えるお客様</h3><p>必要なライフラインサービスをまとめて検討・お申し込み</p></li>
      </ol>
      <p class="co-svc-note fade">※お客様の同意の取得、情報共有の方法、各サービスのお申し込み手続きについては、提携の際にご説明します。</p>
    </div>
  </section>

  <section class="section co-stages al-perf" id="performance">
    <div class="wrap">
      <p class="eyebrow fade">Our Performance</p>
      <h2 class="fade">信頼と実績を数字で</h2>
      <ul class="al-num-list">{numbers}
      </ul>
    </div>
  </section>
'''
            + ps_flow(AL_FLOW, eyebrow='Partnership Flow', title='提携開始までの流れ') + ps_faq(AL_FAQ) + '\n'
            + final_cta(title='<span>新しい価値を</span><br><span>ともに創る</span>',
                        text='不動産会社の皆様へ<br>ライフラインサービスを通じた新たな価値創出を<br>LFグループとともに始めませんか',
                        button='事業提携について問い合わせる', eyebrow='Become Our Partner',
                        mail=ALLIANCE_MAIL, mail_label='アライアンス事業に関するメール'))


def ceo_message_block():
    """代表挨拶（「私たちについて」の末尾）。本文はお客様（LFグループ）からいただいた正式な文章（2026-10-09）。
    写真と直筆サインは images/ceo-photo.jpg・ceo-sign.png（同日受領）。"""
    return f'''
  <section class="section bg-blue" id="message">
    <div class="wrap ceo-msg">
      <div class="ceo-msg-side">
        <p class="eyebrow fade">Message</p>
        <h2 class="fade">代表挨拶</h2>
        <figure class="co-message-photo fade"><img loading="lazy" src="/images/ceo-photo.jpg" alt="代表取締役 遠藤 昇平" onerror="this.closest('figure').remove()"></figure>
      </div>
      <div class="ceo-msg-main fade">
        <p class="co-message-lead">人と企業の可能性を、<br>その先へ。</p>
        <div class="co-message-body">
          <p>私たちLFグループは、「人と企業の可能性を、その先へ。」という想いのもと、お客様一人ひとり、そしてパートナー企業との信頼関係を大切にしながら事業を展開しています。</p>
          <p>社会や経済環境が目まぐるしく変化する現代において、人々の暮らしや企業経営を取り巻く課題は、ますます多様化しています。</p>
          <p>私たちは、こうした変化を新たな可能性と捉え、既存の枠組みにとらわれない柔軟な発想と行動力で、お客様にとって本当に価値のあるサービスを追求していきたいと考えています。</p>
          <div class="co-message-group">
            <p>保険事業では、人生や企業経営におけるさまざまなリスクに向き合い、将来への安心を支えること。</p>
            <p>アライアンス事業では、企業同士のつながりを生かし、新たな価値を生み出すこと。</p>
          </div>
          <p>事業の形は異なっても、その根底にあるのは「人と企業のより良い未来に貢献したい」という変わらぬ想いです。</p>
          <p>そして、私たちが大切にしているのは、サービスの質だけではありません。</p>
          <p>ともに働く仲間が一人ひとりの個性や強みを発揮し、自ら考え、挑戦できる組織であること。社員の成長こそが、企業の成長につながると考えています。</p>
          <p>これからも、目の前のお客様との信頼を一つひとつ積み重ねながら、変化を恐れず、新たな事業や価値の創造に挑戦し続けてまいります。</p>
          <div class="co-message-group">
            <p>お客様にとって、安心して相談できる存在であること。</p>
            <p>パートナー企業にとって、ともに成長できる存在であること。</p>
            <p>そして、社会から必要とされ、信頼され続ける企業であること。</p>
          </div>
          <p>その実現に向けて、LFグループはこれからも歩み続けます。</p>
          <p>今後とも、より一層のご支援とご愛顧を賜りますよう、よろしくお願い申し上げます。</p>
        </div>
        <p class="co-message-company">{COMPANY}</p>
        <p class="co-message-name"><span>代表取締役</span><img class="co-message-sign" loading="lazy" src="/images/ceo-sign.png" alt="遠藤 昇平" onerror="this.replaceWith(document.createTextNode('遠藤 昇平'))"></p>
      </div>
    </div>
  </section>
'''


def page_company():
    # 2026-10-09 お客様の構成案（ChatGPTの共有）で作り直し：①メインビジュアル ②会社情報 ③事業紹介 ④アクセス ⑤代表メッセージへの導線。
    # 「私たちについて」は理念・価値観、「会社概要」は基本情報で信頼を確かめてもらうページ、と役割を分ける。
    # 構成案の［代表者氏名］［設立年月日］［資本金］［代表電話番号］［取引先・提携先］［最寄り駅］は未入力のため、確認できるまで載せない。
    # 代表者名・電話番号・住所・適格請求書番号は、今のサイトにある情報。代表挨拶は「私たちについて」の末尾へ移した
    q = 'https://www.google.com/maps/embed?origin=mfe&amp;pb=!1m3!2m1!1z5oSb55-l55yM5ZCN5Y-k5bGL5biC5p2x5Yy66JG1M-S4geebrjE0LTU!6i16'
    links = ''.join(f'<a href="{h}">{l}{ARROW}</a>' for _, l, h in POLICIES)
    # 冒頭は個人・法人・私たちについてと同じ rf_hero（トップのFVの見せ方。2026-10-09 松本さん「会社概要のTOPページの見せ方も他のページと同様に」）
    hero = rf_hero('会社概要', 'Company Profile', ('信頼を礎に', '新たな価値を創造する'),
                   ('LFグループ株式会社の', '企業情報をご紹介します'),
                   'お問い合わせ', (('recruit-city-1000.jpg', '60% 50%'),),  # 写真の切り替えはなし（2026-10-09 松本さん）。cta-final.jpg は横1280pxで粗く見えたので、横1536pxのこの写真に替えた（採用情報と同じ写真）
                   ('OUR', 'COMPANY', 'PROFILE.'), still=True)
    return hero + f'''
  <section class="section" id="profile">
    <div class="wrap">
      <p class="eyebrow fade">Company Information</p>
      <h2 class="fade">会社情報</h2>
      <!-- ★要確認：構成案にある 設立・資本金・取引先／提携先 は、今のサイトに記載がないため載せていない。確認できたら下の表に足す -->
      <dl class="company-list full fade" style="margin-top:40px">
        <div><dt>会社名</dt><dd>{COMPANY}</dd></div>
        <div><dt>代表者</dt><dd>遠藤 昇平</dd></div>
        <div><dt>所在地</dt><dd>〒{POSTAL}<br>{ADDRESS}</dd></div>
        <!-- ★要確認：2つの番号の用途（代表／お問い合わせ）が今のサイトに書かれていない。確認できたら「代表」などを添える -->
        <div><dt>電話番号</dt><dd><a href="{TEL_HREF}">{TEL}</a></dd></div>
        <div><dt>メールアドレス</dt><dd><a href="mailto:{MAIL}">{MAIL}</a></dd></div>
        <div><dt>事業内容</dt><dd>生命保険代理店事業<br>損害保険代理店事業<br>アライアンス事業<br>ライフラインサービスの取次・紹介</dd></div>
        <div><dt>適格請求書発行<br>事業者登録番号</dt><dd>T4180001157727</dd></div>
      </dl>
    </div>
  </section>

  <section class="section bg-blue" id="business">
    <div class="wrap">
      <p class="eyebrow fade">Our Business</p>
      <h2 class="fade">事業紹介</h2>
      <div class="co-biz-grid">
        <article class="co-biz-card fade">
          <div class="co-biz-photo"><img loading="lazy" src="/images/service-insurance.jpg" alt="" style="object-position:50% 60%" onerror="this.remove()"></div>
          <p class="co-biz-en">Insurance Business</p>
          <h3>保険代理店事業</h3>
          <p>個人・法人のお客様を対象に、生命保険・損害保険のご提案を行っています。</p>
          <p>医療保障や死亡保障、資産形成に向けた保険の活用、企業のリスク対策や福利厚生など、幅広いご相談に対応します。</p>
          <p class="co-biz-links"><a class="link-arrow" href="/personal/">個人のお客様{ARROW}</a><a class="link-arrow" href="/corporate/">法人のお客様{ARROW}</a></p>
        </article>
        <article class="co-biz-card fade">
          <div class="co-biz-photo"><img loading="lazy" src="/images/scene-home.jpg" alt="" onerror="this.remove()"></div>
          <p class="co-biz-en">Alliance Business</p>
          <h3>アライアンス事業</h3>
          <p>不動産会社をはじめとする提携企業との連携を通じて、新生活に必要なライフラインサービスをご案内しています。</p>
          <p>お客様の利便性向上と、パートナー企業の業務効率化・新たな価値創出を支援します。</p>
          <p class="co-biz-links"><a class="link-arrow" href="/partner/">アライアンス事業{ARROW}</a></p>
        </article>
      </div>
    </div>
  </section>

  <section class="section" id="access">
    <div class="wrap">
      <p class="eyebrow fade">Access</p>
      <h2 class="fade">アクセス</h2>
      <!-- ★要確認：構成案の「最寄り駅・徒歩所要時間」は未確認のため載せていない。確認できたら下の住所の下に足す -->
      <div class="co-access fade">
        <p class="co-access-name">{COMPANY}</p>
        <p class="co-access-addr">〒{POSTAL}<br>{ADDRESS}</p>
      </div>
      <div class="map-frame fade">
        <iframe src="{q}" title="LFグループ株式会社の地図" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
      </div>
    </div>
  </section>

  <section class="section bg-blue">
    <div class="wrap">
      <p class="eyebrow fade">Policy</p>
      <h2 class="fade">各種方針</h2>
      <div class="link-list fade" style="margin-top:40px">{links}</div>
    </div>
  </section>

  <section class="section" id="ceo">
    <div class="wrap">
      <div class="co-ceo fade">
        <figure class="co-ceo-photo"><img loading="lazy" src="/images/ceo-photo.jpg" alt="" onerror="this.closest('figure').remove()"></figure>
        <div class="co-ceo-copy">
          <p class="eyebrow">Message from the Representative</p>
          <h2><span>信頼を積み重ね、</span><span>新しい可能性へ。</span></h2>
          <p class="text">LFグループが大切にしている想いや、これから目指す未来について。<br>代表からのメッセージをご紹介します。</p>
          <p class="co-ceo-link"><a class="btn btn-primary" href="/about/#message">代表挨拶を見る{ARROW}</a></p>
        </div>
      </div>
    </div>
  </section>

''' + final_cta()


def page_contact():
    # 電話のみの受付。受付時間は既存の表示を維持（公開前に要確認）。
    contacts = f'''      <div class="contact-tel contact-first">
        <div class="tel-box tel-main">
          <h2>お電話でのお問い合わせ</h2>
          <a class="tel-number" href="{TEL_HREF}">{TEL}</a>
          <p class="tel-hours">受付時間 10:00～19:00</p>
          <a class="btn btn-primary" href="{TEL_HREF}">電話で相談する{ARROW}</a>
        </div>
        <div class="tel-box tel-mails">
          <h2>メールでのお問い合わせ</h2>
          <dl class="mail-list">
            <div><dt>保険・固定費のご相談</dt><dd><a href="mailto:{MAIL}">{MAIL}</a></dd></div>
            <div><dt>アライアンス事業のご相談</dt><dd><a href="mailto:{ALLIANCE_MAIL}">{ALLIANCE_MAIL}</a></dd></div>
            <div><dt>採用関連のお問い合わせ</dt><dd><a href="mailto:{RECRUIT_MAIL}">{RECRUIT_MAIL}</a></dd></div>
          </dl>
        </div>
      </div>
      <div class="contact-form fade">
        <h2>メールでのお問い合わせ</h2>
        <p>下のフォームからお送りください。担当者より2営業日以内にご連絡いたします。</p>
        <iframe src="{FORM_URL}?embedded=true" title="LFグループ お問い合わせフォーム" loading="lazy" width="100%" height="1500" frameborder="0" marginheight="0" marginwidth="0">読み込んでいます…</iframe>
        <p class="contact-form-note">フォームが表示されない場合は、<a href="{FORM_URL}" target="_blank" rel="noopener">こちらから開いてください</a>。</p>
      </div>'''
    return page_hero('Contact', 'お問い合わせ', [('お問い合わせ', '/contact/')],
                     lead='保険や固定費の見直しについて、お電話・メールでご相談を承っています。',
                     compact=True, extra=contacts).replace('sub-hero compact', 'sub-hero compact contact-intro', 1)


# ───── 採用情報（2026-10-08 お客様の構成案で作り直し） ─────
# ①採用メッセージ（冒頭。写真4枚と動きはそのまま）②LFグループについて ③働く環境 ④成長と評価 ⑤募集職種
# ⑥働き方（数字）（構成案の社員紹介は 2026-10-08 松本さんの指示で外した）⑧キャリアステップ ⑨募集要項・選考フロー ⑩よくあるご質問 ⑪応募。
# 見出しに「。」「、」を入れない。段の見出しのすぐ下に説明文を置かない（2026-10-08 松本さん）
# ★要確認：一般事務・営業サポートの募集、完全週休2日制・年間休日120日は構成案にあるが今のサイトにない。印（.note-draft）を付けている
RC_CULTURE = [
    ('Culture', '自分らしく働ける環境', '一人ひとりの個性や考え方を尊重し、自主性を大切にする組織を目指しています。必要以上の制約にとらわれず、自分の強みを発揮できる環境づくりを大切にしています。', 'about-hero.jpg', '50% 65%'),
    ('Culture', '互いを尊重する組織', '立場や役職に関係なく、意見を交わしながらより良い仕事を目指す。一人ひとりが安心して働ける、風通しの良い組織づくりに取り組んでいます。', 'recruit-work-team.jpg', '50% 50%'),
    ('Culture', '挑戦を後押しする文化', '年齢や経験だけにとらわれず、新しいアイデアや挑戦を歓迎。会社の成長とともに、自分自身の可能性も広げていける環境を目指しています。', 'mission-2.jpg', '50% 50%'),
]

RC_JOBS = [
    ('Insurance Sales', '保険コンサルティング営業', '成果が自分の可能性を広げる', 'recruit-work-consult.jpg',
     ['個人・法人のお客様に対して、生命保険・損害保険を活用した保障やリスク対策をご提案します。',
      '法人マーケットへの営業活動や、既存のお客様との関係づくりを通じて、専門性と営業力を磨ける仕事です。'],
     ['成果連動型報酬', '法人営業', '専門知識の習得', '成長機会'], False),
    ('Office Administration', '一般事務・営業サポート', '働きやすさもやりがいも', 'recruit-work-prepare.jpg',
     ['保険事業やアライアンス事業を支える事務業務を担当します。',
      '書類作成やデータ管理、お客様対応などを通じて、会社の円滑な運営をサポートします。'],
     ['働きやすい環境', '事務スキルの向上', '組織への貢献'], True),
]

# 2026-10-09 お客様から採用の情報をいただいた：年間休日120日以上・勤務時間10〜19時。評価制度は載せない。
# 休日は「完全週休2日制」の書き方（2026-10-09 松本さん。一度「制」を外してしまったが、「制」ありに戻した）
RC_NUMBERS = [('休日制度', '完全週休', '2日制'), ('年間休日', '120', '日以上'), ('勤務時間', '10–19', '時')]

RC_STEPS = [
    ('基礎を身につける', '商品知識・業務知識・仕事の進め方を学びます。'),
    ('専門性を高める', '経験を積み、自分の強みや得意分野を伸ばします。'),
    ('新しい役割に挑戦する', '後輩の育成やチーム運営、新しい業務への挑戦など。'),
]

RC_SELECT = [
    ('お問い合わせ・ご応募', f'お問い合わせフォーム、お電話（{RECRUIT_TEL}）、メール（{RECRUIT_MAIL}）のいずれかでご連絡ください。'),
    ('書類選考', 'ご経験やご希望の条件を確認します。'),
    ('面接（1〜2回）', '仕事内容や働き方について、お互いに理解を深めます。'),
    ('内定・入社', '条件を確認し、入社の手続きを進めます。'),
]

# ★要確認：質問は構成案のまま。回答は構成案になかったので、今の募集要項の範囲でこちらで書いた下書き
RC_FAQ = [
    ('保険業界が未経験でも応募できますか？',
     '応募資格は学歴・性別・国籍不問です。これまでのご経験については、お問い合わせフォーム・お電話・メールで気軽にご相談ください。'),
    ('営業職の給与はどのように決まりますか？',
     '営業成績に応じた成果報酬で、最低保証は400,000円です。年収1,000万円以上も可能です。詳しい仕組みは面接でご説明します。'),
    ('どのような人物を求めていますか？',
     'お客様一人ひとりに誠実に向き合える方、自ら考えて行動し、新しいことに挑戦したい方を歓迎します。'),
]


def page_recruitment():
    rows = [
        ('職務内容', '生命保険・損害保険などの金融商品のご提案・販売と、ご契約後のアフターサービス'),
        ('雇用形態', '契約社員<br>※試用期間3カ月　正社員登用制度あり（成績基準あり）'),
        ('応募資格', '学歴・性別・国籍不問'),
        ('勤務地', '愛知県名古屋市東区'),
        ('勤務時間', '10時～19時'),
        ('休日・休暇', '完全週休2日制（年間休日120日以上）'),
        ('給与', '成果報酬<br>最低保証400,000円<br>年収1,000万円以上も可能'),
        ('選考方法', '書類面接・面接試験（1～2回）'),
        ('応募方法', 'お問い合わせフォーム・お電話・メールにてご応募ください'),
        ('郵送先・応募先', f'〒{POSTAL} {ADDRESS}'),
    ]
    dl = ''.join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in rows)
    culture = ''.join(f'''
        <article class="ps-menu fade">
          <div class="ps-menu-photo"><img src="/images/{img}" alt="" style="object-position:{pos}" onerror="this.remove()"></div>
          <p class="ps-menu-num">{i + 1:02d}<span>{en}</span></p>
          <h3>{t}</h3>
          <p>{x}</p>
        </article>''' for i, (en, t, x, img, pos) in enumerate(RC_CULTURE))
    jobs = ''.join(f'''
        <article class="rc-job fade">
          <div class="rc-job-photo"><img src="/images/{img}" alt="" onerror="this.remove()"></div>
          <div class="rc-job-body">
            <p class="ab-biz-en">{en}</p>
            <h3>{t}</h3>
            <p class="rc-job-catch">{c}</p>
            {''.join(f'<p>{x}</p>' for x in texts)}
            <ul class="rc-job-tags">{''.join(f'<li>{p}</li>' for p in points)}</ul>
            {'<p class="note-draft">募集の有無・条件は確認中です</p>' if draft else f'<p><a class="link-arrow" href="#requirements">募集要項を見る{ARROW}</a></p>'}
          </div>
        </article>''' for en, t, c, img, texts, points, draft in RC_JOBS)
    numbers = ''.join(f'''
        <li class="fade"><p class="al-num-label">{label}</p><p class="al-num-value">{value}<small>{unit}</small></p></li>''' for label, value, unit in RC_NUMBERS)
    select = ''.join(f'''
          <li><b>{i + 1:02d}</b><h4>{t}</h4><p>{x}</p></li>''' for i, (t, x) in enumerate(RC_SELECT))
    # FV（冒頭）は write_recruit_trials() がトップと同じ動きの形に差し替える。ここはその元になる見出し・説明文・ボタン
    return f'''  <section class="rc-fv">
    <div class="rc-fv-photo fade"><img src="/images/about-hero.jpg" alt="" data-eager onerror="this.remove()"><span class="rc-photo-todo">写真は仮</span></div>
    <div class="wrap rc-fv-copy">
      <ol class="crumb fade" aria-label="パンくずリスト"><li><a href="/">トップ</a></li><li aria-current="page">採用情報</li></ol>
      <p class="eyebrow fade">Recruitment<span class="rc-fv-ja">採用情報</span></p>
      <h1 class="rc-fv-title fade"><span>人の人生に向き合いながら</span><span>自分の未来も変えていく</span></h1>
      <p class="rc-fv-lead fade">決められた道を歩むだけではなく<br>自分の可能性を自分の手で広げていく</p>
      <p class="rc-status fade"><span class="dot"></span>Entry Open<b>エントリー受付中</b></p>
      <p class="rc-links fade"><a class="btn btn-primary" href="#jobs">募集職種を見る{ARROW}</a><a class="link-arrow" href="/contact/">応募・お問い合わせ{ARROW}</a></p>
    </div>
  </section>

  <section class="section" id="about-us">
    <div class="wrap">
      <p class="eyebrow fade">About Us</p>
      <h2 class="fade">LFグループについて</h2>
      <div class="ab-biz-list">
        <article class="ab-biz fade">
          <div class="ab-biz-photo"><img src="/images/cta.jpg" alt="" style="object-position:50% 50%" onerror="this.remove()"></div>
          <div class="ab-biz-body">
            <p class="ab-biz-en">Who We Are</p>
            <h3><span>一人ひとりの可能性が</span><br><span>会社の未来をつくる</span></h3>
            <p>LFグループは、保険事業とアライアンス事業を中心に、人々の暮らしと企業活動を支えるサービスを展開しています。</p>
            <p>私たちが目指すのは、会社の成長だけではありません。働く一人ひとりが自分の強みを生かし、仕事にやりがいを感じながら成長できる組織です。</p>
            <p>決められたことをこなすだけではなく、自ら考え、行動し、新しい価値を生み出していく。そんな仲間とともに、LFグループの未来をつくっていきたいと考えています。</p>
            {mini_tiles(['/about/'])}
          </div>
        </article>
      </div>
    </div>
  </section>

  <section class="section bg-blue" id="culture">
    <div class="wrap">
      <p class="eyebrow fade">Our Culture</p>
      <h2 class="fade">LFグループの働く環境</h2>
      <div class="ps-menu-list">{culture}
      </div>
    </div>
  </section>

  <section class="section ab-mission" id="career">
    <div class="wrap">
      <p class="eyebrow fade">Career &amp; Reward</p>
      <h2 class="fade">成長と評価の仕組み</h2>
      <div class="ab-mission-grid">
        <p class="ab-mission-words fade"><span>努力と成果が</span><span>正当に評価される</span><span>環境へ</span></p>
        <div class="ab-mission-body fade">
          <p>LFグループでは、役割や仕事内容に応じた評価を大切にしています。</p>
          <p>営業職では、成果に応じた報酬制度を設け、一人ひとりの頑張りを収入に反映します。</p>
          <p>事務職では、日々の業務への取り組みや組織への貢献を大切にしながら、安心して長く働ける環境づくりを目指します。</p>
          <ul class="rc-reward">
            <li>{ps_icon('chart')}<div><h3>成果に応じた報酬</h3><p>営業職は、実績を報酬に反映する仕組みです。</p></div></li>
            <li>{ps_icon('growth')}<div><h3>成長を支える環境</h3><p>経験やスキルに応じて、新しい役割や仕事に挑戦できます。</p></div></li>
          </ul>
        </div>
      </div>
    </div>
  </section>

  <section class="section bg-blue" id="jobs">
    <div class="wrap">
      <p class="eyebrow fade">Our Work</p>
      <h2 class="fade">募集職種</h2>
      <div class="rc-job-list">{jobs}
      </div>
    </div>
  </section>

  <section class="section co-stages al-perf" id="work-style">
    <div class="wrap">
      <p class="eyebrow fade">Work Style in Numbers</p>
      <h2 class="fade">働く環境を数字で</h2>
      <ul class="al-num-list is-three">{numbers}
      </ul>
    </div>
  </section>
''' + ps_flow(RC_STEPS, eyebrow='Career Path', title='キャリアステップ') + f'''
  <section class="section bg-blue" id="requirements">
    <div class="wrap">
      <p class="eyebrow fade">Recruitment</p>
      <h2 class="fade">募集要項</h2>
      <p class="rc-req-job fade">保険コンサルティング営業</p>
      <dl class="company-list full fade">{dl}</dl>
      <h3 class="rc-select-title fade">選考フロー</h3>
      <ol class="rc-select fade">{select}
      </ol>
    </div>
  </section>
''' + ps_faq(RC_FAQ, bg='') + '\n' + final_cta(
        title='<span>あなたの可能性を</span><br><span>LFグループで</span>',
        text='新しい挑戦も、自分らしい働き方も。<br>一人ひとりの可能性を大切にする場所で、<br>次の一歩を踏み出しませんか。',
        button='応募・お問い合わせ', eyebrow='Your Future Starts Here.', mail=RECRUIT_MAIL, mail_label='採用に関するメール')


# ───────────── 方針ページ：保存した本文を見出し・箇条書きに組み直す ─────────────

NAV_NOISE = {'HOME', 'COMPANY', 'SERVICE', 'NEWS', 'CONTACT', 'RECURUITMENT', 'RECRUITMENT', 'ＬＦグループ株式会社',
             '052-990-6159', 'お問い合わせはこちらから', 'エントリー受付中！', '採用情報はこちらから'}

# 今のサイトの誤字。意味は変えずに直す
TYPO = [
    ('提供し続きます', '提供し続けます'), ('幣社', '弊社'),
    ('法令等遵守に係る基本方針を定めています', '法令等遵守に係る基本方針を定めています。'),
    ('アドバイスし事故処理完了まで', 'アドバイスし、事故処理完了まで'),
    ('休日・夜間の事故対応。', '休日・夜間も事故に対応します。'),
    ('お客さまの金融商品に関するお客さまの知識・経験', '金融商品に関するお客さまの知識・経験'),
    ('お客さまの意向と実情に沿った適切な最大限配慮した商品設計、販売・勧誘活動',
     'お客さまの意向と実情に最大限配慮し、適切な商品設計と販売・勧誘活動'),
    ('勘案し十分把握したうえで', '勘案し、十分に把握したうえで'),
    ('ご意見等の収集に努め現状を把握し', 'ご意見等の収集に努め、現状を把握し'),
    ('これらの取組みを定期的または不定期に監査を実施し',
     'これらの取組みについて定期的または不定期に監査を実施し'),
]


def policy_lines(name, title):
    lines = (TEXT / f'{name}.txt').read_text().splitlines()
    i = lines.index(title)
    out = []
    for l in lines[i + 1:]:
        if l in NAV_NOISE:
            break
        for a, b in TYPO:
            l = l.replace(a, b)
        out.append(l)
    return out


def render_policy(lines, heading_rule, sub_rule=lambda l: False):
    """heading_rule(l) が真の行を h2、sub_rule を h3、「・」で始まる行を箇条書き、それ以外を段落にする。"""
    out, ul = [], []

    def flush():
        if ul:
            out.append('<ul>' + ''.join(f'<li>{esc(x)}</li>' for x in ul) + '</ul>')
            ul.clear()
    for l in lines:
        if l.startswith('・'):
            ul.append(l[1:])
            continue
        flush()
        if heading_rule(l):
            out.append(f'<h2>{esc(l)}</h2>')
        elif sub_rule(l):
            out.append(f'<h3>{esc(l)}</h3>')
        elif l.startswith('http'):
            out.append(f'<p><a href="{l}" target="_blank" rel="noopener">{l}</a></p>')
        else:
            out.append(f'<p>{esc(l)}</p>')
    flush()
    return '\n'.join(out)


def policy_operation():
    lines = policy_lines('operation', 'お客様本位の運営方針')
    # 1行目「４．…アドバイスし」と次の行は1文なのでつなぐ
    joined = []
    for l in lines:
        if joined and joined[-1].endswith('アドバイスし'):
            joined[-1] += '、' + l
        else:
            joined.append(l)
    out, i = [], 0
    nums = [l for l in joined if re.match(r'^[１２３４５]．', l)]
    out.append('<h2>お客様本位の業務運営方針《FD方針》</h2>')
    out.append(policy_lines_html([esc(re.sub(r'^[１-９]．', '', l)) for l in nums], fade=False))
    out.append('<h2>お客様本位の業務運営方針と主な取組内容</h2>')
    rest = joined[joined.index('お客様本位の業務運営方針と主な取組内容') + 1:]
    for l in rest:
        if l.startswith('-----') or l == '以上':
            continue
        if l.startswith('≪'):
            out.append(f'<h3>{esc(l)}</h3>')
        elif l == '〈主な取組内容〉':
            out.append('<h4>主な取組内容</h4><ul>')
        elif out[-1].startswith('<h4>') or (out[-1].startswith('<li>') and not out[-1].endswith('</ul>')):
            out.append(f'<li>{esc(l)}</li>')
        else:
            out.append(f'<p>{esc(l)}</p>')
        # 次の見出しの前で箇条書きを閉じる
    html_ = '\n'.join(out)
    html_ = re.sub(r'(<li>[^<]*</li>)\n(<h3>|$)', r'\1</ul>\n\2', html_)
    if html_.rstrip().endswith('</li>'):
        html_ += '</ul>'
    return html_ + '<p class="end">以上</p>'


def policy_solicitation():
    lines = policy_lines('solicitation', '勧誘方針')
    return '<div class="numbered">' + render_policy(lines, heading_rule=lambda l: not l.startswith('・')) + '</div>'


def policy_privacy():
    lines = policy_lines('privacyprotection', '個人情報保護方針')
    # ①②… は（５）（８）（９）では小見出し、（６）（７）（１０）では列挙の項目
    state = {'sec': ''}

    def heading(l):
        m = re.match(r'^（([０-９]+)）', l)
        if m:
            state['sec'] = m.group(1)
        return bool(m)

    def sub(l):
        if l == '【弊社と取引のある会社】':
            return True
        return state['sec'] in ('５', '８', '９') and bool(re.match(r'^[①-⑧]', l))

    body = render_policy(lines, heading_rule=heading, sub_rule=sub)
    # 利用目的の内容は保ち、長い説明を段落に分ける。
    body = body.replace('利用します。また、弊社は複数の保険会社と取引があり、',
                        '利用します。</p>\n<p>また、弊社は複数の保険会社と取引があり、')
    # 本文の「下記のお問い合わせ窓口」。今のサイトに記載がないため、会社の代表連絡先を窓口にする（2026-10-05）
    # ★公開前に確認：受付時間は勤務時間（10時～18時）に合わせた仮の値。部署名を入れるかもクライアントに確認する
    body += f'''<div class="policy-contact">
  <h2><span>個人情報に関する</span><span>お問い合わせ窓口</span></h2>
  <dl>
    <div><dt>会社名</dt><dd>{COMPANY}</dd></div>
    <div><dt>所在地</dt><dd>〒{POSTAL} {ADDRESS}</dd></div>
    <div><dt>電話番号</dt><dd><a href="{TEL_HREF}">{TEL}</a></dd></div>
    <div><dt>メールアドレス</dt><dd><a href="mailto:{MAIL}">{MAIL}</a></dd></div>
    <div><dt>受付時間</dt><dd>10:00～19:00</dd></div>
  </dl>
</div>'''
    return body


def policy_security():
    lines = policy_lines('informationsecurity', '情報セキュリティ基本方針')
    return render_policy(lines, heading_rule=lambda l: bool(re.match(r'^（[０-９]+）', l)))


def page_policy(key, label, render):
    return page_hero('Policy', label, [(label, f'/{key}/')], compact=True) + f'''
  <section class="section">
    <div class="wrap reading policy">
{render()}
    </div>
  </section>
'''


# ───────────────────────── 書き出し ─────────────────────────

def relative(path, content):
    """「/about/」のようなサイト直下からのリンクを、そのページから見た相対パスにする。
    GitHub Pages は easywebcraft.github.io/リポジトリ名/ の下で配信するため、先頭が / のままだと外れる。"""
    depth = path.count('/')
    prefix = '../' * depth if depth else './'
    return re.sub(r'(href|src)="/(?!/)', lambda m: f'{m.group(1)}="{prefix}', content)


def image_version(content):
    """写真も同じ名前のまま差し替えるので、中身から作った番号を URL に付ける（ブラウザが古い写真を出し続けないように）。"""
    def add(m):
        f = SITE / 'images' / m.group(2)
        if not f.exists():
            return m.group(0)
        v = hashlib.sha1(f.read_bytes()).hexdigest()[:8]
        return f'{m.group(1)}{m.group(2)}?v={v}"'
    return re.sub(r'(src="/images/)([^"?]+)"', add, content)


def jpeg_size(f):
    """JPEG の幅・高さを読む（ライブラリを足さずに済むよう、SOF マーカーだけを見る）。"""
    b = f.read_bytes()
    i = 2
    while i < len(b):
        marker, length = b[i + 1], int.from_bytes(b[i + 2:i + 4], 'big')
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            return int.from_bytes(b[i + 7:i + 9], 'big'), int.from_bytes(b[i + 5:i + 7], 'big')
        i += 2 + length
    return None


def image_attrs(content):
    """写真に幅・高さ（表示前に場所を確保して、読み込み時のガタつきを防ぐ）と読み込み方を付ける。
    最初に見える写真（fetchpriority="high" を付けたもの・下層ページ冒頭の写真）以外は遅延読み込み。"""
    def add(m):
        tag, name = m.group(0), m.group(1)
        f = SITE / 'images' / name
        if 'width=' not in tag and f.exists() and (size := jpeg_size(f)):
            tag = tag.replace('<img ', f'<img width="{size[0]}" height="{size[1]}" ', 1)
        if 'loading=' not in tag:
            eager = 'fetchpriority=' in tag or 'data-eager' in tag
            tag = tag.replace('<img ', '<img decoding="async" ' if eager else '<img loading="lazy" decoding="async" ', 1)
        return tag.replace(' data-eager', '')
    return re.sub(r'<img [^>]*src="/images/([^"?]+)"[^>]*>', add, content)


SEC_HEAD = re.compile(r'<section class="(section[^"]*)"((?:(?!>).)*)>(\s*<div class="wrap[^"]*">\s*<p class="eyebrow)', re.S)


def compact_heads(html_):
    """段の頭（英字の小見出し＋見出し）を、トップの「FIND YOUR PAGE」の帯のように中央にまとめて狭くする印 sec-c を付ける
    （2026-10-08 松本さん「他のメニューも同じ方式で。余白はなるべく消したい」）。見た目は src/refine.css の .sec-c"""
    return SEC_HEAD.sub(lambda m: f'<section class="{m.group(1).strip()} sec-c"{m.group(2)}>{m.group(3)}', html_)


def write(path, content):
    if path.endswith('.html'):
        page = path.removesuffix('index.html')
        content = image_version(image_attrs(content)).replace('__URL_META__\n', url_meta(page))
        content = compact_heads(content)
        if RELEASE:
            # 内部向けのメモ（★公開前… など）を本番のソースに残さない
            content = re.sub(r'\n?[ \t]*<!--[\s\S]*?-->', '', content)
        # 404 ページはどの深さの URL でも出るので、サイト直下からのリンクのままにする（本番はドメイン直下で配信する前提）
        if path != '404.html':
            content = relative(path, content)
    p = SITE / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    print('  ', path)


def page_404():
    return page_hero('404 Not Found', 'ページが見つかりません', [('ページが見つかりません', '/404.html')],
                     lead='お探しのページは、移動または削除された可能性があります。<br class="pc">お手数ですが、トップページからお探しください。',
                     extra=f'      <p class="fade" style="margin-top:32px"><a class="btn btn-primary" href="/">トップページへ{ARROW}</a></p>',
                     compact=True)


PAGES = ['', 'about/', 'personal/', 'corporate/', 'partner/', 'company/', 'contact/', 'recruitment/',
         'operation/', 'solicitation/', 'privacyprotection/', 'informationsecurity/']


def release_files():
    """本番用：画像（顧客からもらったロゴの元データ images/logo/ は除く）・robots.txt・sitemap.xml。"""
    shutil.copytree(BASE / 'images', SITE / 'images', ignore=lambda d, names: ['logo'] if Path(d) == BASE / 'images' else [])
    robots = 'User-agent: *\nAllow: /\n'
    if SITE_URL:
        robots += f'\nSitemap: {SITE_URL}/sitemap.xml\n'
        urls = ''.join(f'  <url><loc>{SITE_URL}/{p}</loc></url>\n' for p in PAGES)
        write('sitemap.xml', f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    else:
        print('   ※ --site-url がないため sitemap.xml・canonical・og:image は出していません')
    write('robots.txt', robots)


GOLD_WIPE = '<span class="rv-sweep" aria-hidden="true"><svg class="rv-edge" viewBox="0 0 100 100" preserveAspectRatio="none"><defs><linearGradient id="rvEdgeG" gradientUnits="userSpaceOnUse" x1="-10" y1="0" x2="-0.42" y2="2.87"><stop offset="0" stop-color="#F2B63C" stop-opacity="0"/><stop offset="0" stop-color="#F2B63C" stop-opacity="0"/><stop offset="1" stop-color="#FFE6B0" stop-opacity=".6"/></linearGradient></defs><polygon points="-10,0 0,0 -30,100 -40,100" fill="url(#rvEdgeG)"/><polygon points="-0.5,0 0,0 -30,100 -30.5,100" fill="#FFF3D6"/></svg></span>'


def write_recruit_trials():
    """採用情報のFVの試作（2026-10-06「人を写さなくても成立する採用ページ」）。/recruitment-a/・-b/・-c/ に、
    今の採用情報ページの FV だけを差し替えて書き出す。写真は生成AIの素材ができるまで、今ある人物なしの写真で仮。
    見た目と動きは src/recruit-fv.css・recruit-fv.js。本番（--release）には出さない。
      A オフィスの1日：同じオフィスの写真が朝→昼→夕方→夜と斜めに切り替わり、時刻が変わる
      B 仕事の道具：斜めのパネル3枚の写真が時間差で切り替わり、下に小さな写真が横へ流れる
      C 街と道：スクロールすると、街→並木道→玄関へ続く道→空へ「奥へ進む」ように切り替わり、言葉が変わる"""
    css, js = (SRC / 'recruit-fv.css').read_text(), (SRC / 'recruit-fv.js').read_text()
    v = hashlib.sha1((css + js).encode()).hexdigest()[:8]
    write('assets/recruit-fv.css', css)
    write('assets/recruit-fv.js', js)
    base = layout('採用情報', page_recruitment(), 'recruitment')
    i = base.index('<section class="rc-fv">')
    j = base.index('</section>', i) + len('</section>')
    old = base[i:j]
    k = old.index('<div class="wrap rc-fv-copy">')
    copy = old[k:old.rindex('</div>') + len('</div>')]
    img = lambda f, cls='': '<img class="%s" src="/images/%s" alt="" %s onerror="this.remove()">' % (cls, f, 'fetchpriority="high"' if cls == 'is-on' else 'data-eager')
    tag = '<span class="rc-photo-todo">写真は仮（生成AIの素材に差し替え）</span>'
    # 案A の写真は生成AIで作った「同じ相談スペースの朝・昼・夕方・夜」（2026-10-06 松本さん作成。recruit-1000〜1800.jpg）
    times = [('10:00', 'START', '一日のはじまり', 'recruit-1000.jpg'), ('13:00', 'MEETING', 'お客様とのご相談', 'recruit-1300.jpg'),
             ('16:00', 'PROPOSAL', 'ご提案の準備', 'recruit-1600.jpg'), ('19:00', 'FINISH', '一日のおわり', 'recruit-1800.jpg')]
    fv = {
        'a': f'''<section class="rf rf-a" data-fx="a">
    <div class="rf-media">{''.join(img(f, 'is-on' if n == 0 else '') for n, (_, _, _, f) in enumerate(times))}</div>
    {copy}
    <div class="wrap rf-clock" aria-hidden="true">{''.join(f'<p class="rf-time{" is-on" if n == 0 else ""}"><b>{t}</b><span>{en}</span><small>{ja}</small></p>' for n, (t, en, ja, _) in enumerate(times))}
      <ol class="rf-bar">{'<li></li>' * len(times)}</ol></div>
  </section>''',
        'b': f'''<section class="rf rf-b" data-fx="b">
    <div class="rf-panels">{''.join(f'<div class="rf-panel">{"".join(img(f, "is-on" if m == 0 else "") for m, f in enumerate(fs))}</div>' for fs in (
            ('about-hero.jpg', 'scene-dining.jpg', 'mission-2.jpg'), ('scene-dining.jpg', 'mission-2.jpg', 'about-hero.jpg'), ('mission-2.jpg', 'scene-shop.jpg', 'scene-dining.jpg')))}</div>
    {copy}
    <div class="rf-strip" aria-hidden="true"><div class="rf-track">{''.join(img(f) for f in ('about-hero.jpg', 'scene-dining.jpg', 'mission-2.jpg', 'scene-shop.jpg', 'cta-final.jpg', 'scene-home.jpg') * 2)}</div></div>
    {tag}
  </section>''',
        'c': f'''<section class="rf rf-c" data-fx="c">
    <div class="rf-sticky">
      <div class="rf-media">{''.join(img(f, 'is-on' if n == 0 else '') for n, f in enumerate(('cta-final.jpg', 'scene-shop.jpg', 'scene-home.jpg', 'cta.jpg')))}</div>
      {copy}
      <div class="wrap rf-words" aria-hidden="true">{''.join(f'<p class="rf-word{" is-on" if n == 0 else ""}"><small>0{n + 1}</small>{w}</p>' for n, w in enumerate(('名古屋・東区から', '一歩ずつ', '自分の未来へ', 'ここから、はじまる')))}</div>
      {tag}
    </div>
  </section>''',
    }
    # 案A2（2026-10-07「もっとベンチャー企業感・イケイケの中小企業感を」）：案A の写真と仕組みのまま、
    # 極太のゴシック＋大きな英字、濃い背景に明るいゴールド、募集要項の数字のカウントアップ、2.5秒の切り替え、
    # 「WE ARE HIRING」の流れる帯、画面右下の ENTRY ボタン。コピーは募集要項にある内容（成果報酬・年収1,000万円も可能）から
    # コピーは今の採用情報ページのまま（2026-10-07 松本さん「コピーは今まで通りで、動きをいけいけに」）。
    # 見出しを1文字ずつ出すために rv-title を付け、ほかの要素は .fade を外して recruit-fv.js で順にすべり込ませる
    # 案A2のコピーは、採用情報ページのまま（2026-10-07 松本さん「コピーはそのまま。フォントだけ本番のトップと同じに」）。
    # 見出しを1文字ずつ出すために rv-title を付け、他の要素の .fade は外して recruit-fv.js で順にすべり込ませる
    # 見出し（2026-10-08 構成案のおすすめ）：「自分らしく働く／可能性を広げる」。英字は WORK／YOUR WAY.／GROW BEYOND.（それまでは「お客様のこれからに寄り添い…」・SUPPORT…）
    # 指定の文は読点「、」・ピリオド「.」を含むが、指定どおりそのまま入れる
    copy_v = (copy.replace('<h1 class="rc-fv-title fade"><span>人の人生に向き合いながら</span><span>自分の未来も変えていく</span></h1>',
                           '<h1 class="rc-fv-title rv-title"><span>自分らしく働く</span><span>可能性を広げる</span></h1>')
                  .replace(' fade"', '"').replace('class="fade"', ''))
    assert 'rv-title' in copy_v
    hiring = ''.join('<span>WE ARE HIRING<i>―</i>JOIN LF GROUP<i>―</i></span>' for _ in range(6))
    # A2：採用向けの仕事風景4枚（生成AIのイメージ素材。実在の社員・職場の写真ではない）。
    recruitment_photos = ('prepare', 'consult', 'team', 'learn')
    recruitment_fv = fv['a']
    for (_, _, _, original), scene in zip(times, recruitment_photos):
        recruitment_fv = recruitment_fv.replace('/images/' + original, '/images/recruit-work-' + scene + '.jpg')
    scene_labels = (('PREPARE', '仕事の準備'), ('CONSULT', 'お客様とのご相談'),
                    ('TEAM', 'チームでの打ち合わせ'), ('LEARN', '学びと成長'))
    for number, ((time, english, japanese, _), (label, caption)) in enumerate(zip(times, scene_labels), 1):
        recruitment_fv = recruitment_fv.replace(f'<b>{time}</b><span>{english}</span><small>{japanese}</small>',
                                                f'<b>0{number}</b><span>{label}</span><small>{caption}</small>')
    fv['a2'] = (recruitment_fv
                       .replace('<section class="rf rf-a" data-fx="a">',
                                '<section class="rf rf-a rf-v rf-top rf-wipe rf-serif rf-sub rf-recruit" data-fx="a" data-stay="4500">')
                       .replace(copy, '<p class="rv-big" aria-hidden="true"><span>WORK</span><span>YOUR WAY.</span><span>GROW BEYOND.</span></p>\n    ' + GOLD_WIPE + '\n    ' + copy_v)
                       .replace('  </section>', '''    <small class="rf-photo-note">写真はイメージです</small>
  </section>''', 1))
    # 01〜04の表示（右下の時刻・進み具合の線）は、案A2では外す（2026-10-07 松本さん）
    i2 = fv['a2'].index('<div class="wrap rf-clock"')
    j2 = fv['a2'].index('</ol></div>', i2) + len('</ol></div>')
    fv['a2'] = fv['a2'][:i2] + fv['a2'][j2:]
    out = {}
    for key, sec in fv.items():
        html_ = (base[:i] + sec + base[j:])
        html_ = (html_.replace('</head>', f'<link rel="stylesheet" href="/assets/recruit-fv.css?v={v}">\n</head>', 1)
                      .replace('</body>', f'<script src="/assets/recruit-fv.js?v={v}"></script>\n</body>', 1))
        if key == 'a2':  # 本番のトップと同じ明朝体系の英字（Cormorant Garamond）にするため、フォントを読み込む
            html_ = html_.replace('family=Montserrat:wght@500;600', 'family=Cormorant+Garamond:wght@300;400;500&family=Montserrat:wght@500;600', 1)
        out[key] = html_
        if not RELEASE:
            write(f'recruitment-{key}/index.html', html_.replace('リニューアルの試作です', f'リニューアルの試作です・採用情報のFV 案{key.upper()}', 1))
    return out['a2']  # 2026-10-07 本番の採用情報ページに採用（松本さん）：案A2のヒーロー（写真4枚が切り替わる）


def write_top_a2(top):
    """トップのヒーローに、採用情報のFV案A2（名古屋の街の朝〜夜・金の光・1文字ずつ跳ねる見出し・奥行き）を
    そのまま当てた試作（/top-a2/。2026-10-07）。コピーは今のトップのまま。本番には出さない。
    右下の時刻・ヒーロー下の流れる帯・ENTRY ボタンは外した（2026-10-07 松本さん）"""
    # 写真は名古屋の街の四季（2026-10-07 松本さん作成。春＝桜とビル、夏＝入道雲と交差点、秋＝イチョウ並木と夕日、冬＝雪とイルミネーション）
    times = [(None, None, None, f) for f in ('city-spring.jpg', 'city-summer.jpg', 'city-autumn.jpg', 'city-winter.jpg')]
    imgs = ''.join('<img class="%s" src="/images/%s" alt="" %s onerror="this.remove()">' % ('is-on' if n == 0 else '', f, 'fetchpriority="high"' if n == 0 else 'data-eager') for n, (_, _, _, f) in enumerate(times))
    sec = f'''<section class="rf rf-a rf-v rf-top" data-fx="a" data-stay="4000" id="top">
    <div class="rf-media">{imgs}</div>
    <p class="rv-big" aria-hidden="true"><span>BEYOND</span><span>THE</span><span>POSSIBILITIES.</span></p>
    {GOLD_WIPE}
    <div class="wrap rc-fv-copy">
      <p class="eyebrow">LF Group — Corporate Philosophy</p>
      <h1 class="rc-fv-title rv-title"><span>人と企業の可能性を</span><span>その<em>先</em>へ</span></h1>
      <p class="rc-fv-lead">一人ひとりの暮らしに安心を<br>企業の挑戦に　新たな価値を</p>
      <p class="rc-links"><a class="btn btn-primary" href="/contact/">保険・お金について相談する{ARROW}</a></p>
    </div>
  </section>'''
    css, js = (SRC / 'recruit-fv.css').read_text(), (SRC / 'recruit-fv.js').read_text()
    v = hashlib.sha1((css + js).encode()).hexdigest()[:8]
    i = top.index('<section class="fv" id="top">')
    j = top.index('</section>', i) + len('</section>')
    # /top-a2/ ＝ ヒーローだけの見比べ用（ロゴの演出なし）。
    # /top-a2-full/ ＝ 本番に反映した場合の見え方（2026-10-07）。ロゴの演出を残し、キャッチコピーがこのヒーローの見出しへ
    #   吸い込まれてつながる。演出（main.js）が .fv h1 を探すので、section に fv も付ける（.rf-top の指定で .fv の見た目は上書き）
    plain = top.replace(LOADER_HEAD, '', 1).replace(LOADER, '', 1)
    pi = plain.index('<section class="fv" id="top">')
    pj = plain.index('</section>', pi) + len('</section>')
    pages = (
        ('top-a2/index.html', plain[:pi] + sec + plain[pj:], 'トップのヒーローに採用FV案A2を当てた版'),
        ('top-a2-full/index.html', top[:i] + sec.replace('<section class="rf rf-a', '<section class="fv rf rf-a', 1) + top[j:],
         '本番のトップに反映した場合の見え方（ロゴの演出つき）'),
        # /top-a2-wipe/（2026-10-07）＝ 採用ページ（/recruitment-a2/）と同じ切り替え方（4.5秒ごとに斜めのマスク＋金の光）を当てた見比べ用
        ('top-a2-wipe/index.html', top[:i] + sec.replace('<section class="rf rf-a rf-v rf-top" data-fx="a" data-stay="4000"',
                                                         '<section class="fv rf rf-a rf-v rf-top rf-wipe" data-fx="a" data-stay="4500"', 1) + top[j:],
         '採用ページと同じ切り替え方（斜めのマスク＋金の光）を当てた版'),
        # /top-a2-serif/（2026-10-07）＝ 大きな英字を、見出しと同じ系統の明朝体系（Cormorant Garamond）にした見比べ用
        ('top-a2-serif/index.html', (top[:i] + sec.replace('<section class="rf rf-a rf-v rf-top" data-fx="a" data-stay="4000"',
                                                          '<section class="fv rf rf-a rf-v rf-top rf-wipe rf-serif" data-fx="a" data-stay="4500"', 1) + top[j:])
         .replace('family=Montserrat:wght@500;600', 'family=Cormorant+Garamond:wght@300;400;500&family=Montserrat:wght@500;600', 1),
         '大きな英字を明朝体系のフォントにした版'),
        # /top-flashy/（2026-10-08）＝ 今のトップ（/top-a2-serif/）に、派手な演出（src/flashy.css・flashy.js）を足した見比べ用。本番には出さない
        ('top-flashy/index.html', (top[:i] + sec.replace('<section class="rf rf-a rf-v rf-top" data-fx="a" data-stay="4000"',
                                                        '<section class="fv rf rf-a rf-v rf-top rf-wipe rf-serif rf-flashy" data-fx="a" data-stay="4500"', 1) + top[j:])
         .replace('family=Montserrat:wght@500;600', 'family=Cormorant+Garamond:wght@300;400;500&family=Montserrat:wght@500;600', 1)
         .replace('</head>', '<link rel="stylesheet" href="/assets/flashy.css?v=%s">\n</head>' % hashlib.sha1((SRC / 'flashy.css').read_bytes()).hexdigest()[:8], 1)
         .replace('</body>', '<script src="/assets/flashy.js?v=%s"></script>\n</body>' % hashlib.sha1((SRC / 'flashy.js').read_bytes()).hexdigest()[:8], 1),
         '今のトップに派手な演出（フラッシュ・金の粒・光の筋・きらめき）を足した版'),
    )
    if not RELEASE:
        write('assets/flashy.css', (SRC / 'flashy.css').read_text())
        write('assets/flashy.js', (SRC / 'flashy.js').read_text())
    out = {}
    for path, html_, label in pages:
        html_ = (html_.replace('</head>', f'<link rel="stylesheet" href="/assets/recruit-fv.css?v={v}">\n</head>', 1)
                      .replace('</body>', f'<script src="/assets/recruit-fv.js?v={v}"></script>\n</body>', 1))
        out[path] = html_
        if not RELEASE:
            write(path, html_.replace('リニューアルの試作です', 'リニューアルの試作です・' + label, 1))
    write('assets/recruit-fv.css', css)  # 本番（--release）のトップでも使うので、ここでも書き出す
    write('assets/recruit-fv.js', js)
    # 2026-10-07 本番のトップに採用（松本さん）：/top-a2-wipe/ の形に、大きな英字を明朝体系のフォントにした /top-a2-serif/ を反映
    return out['top-a2-serif/index.html']


def stylish_top(top):
    """トップページに動き（src/stylish.css・stylish.js ＋なめらかなスクロールの lenis.min.js）を足す。
    2026-10-06「もっとスタイリッシュで動きのあるホームページ」から /stylish/ で試作し、同日、本流のトップに反映した。
    見出しを「1行ずつせり上がる」用（s-lines）にする。下層ページには足さない（動きはトップだけ）。
    流れる英字の帯・スクロールで縮む全面写真＋切り替わる見出しは試して外した（2026-10-06 松本さん）。"""
    css, js, lenis = (SRC / 'stylish.css').read_text(), (SRC / 'stylish.js').read_text(), (SRC / 'lenis.min.js').read_text()
    v = hashlib.sha1((css + js).encode()).hexdigest()[:8]
    write('assets/stylish.css', css)
    write('assets/stylish.js', js)
    write('assets/lenis.min.js', lenis)
    html_ = (top.replace('</head>', f'<link rel="stylesheet" href="/assets/stylish.css?v={v}">\n</head>', 1)
                .replace('</body>', f'<script src="/assets/lenis.min.js?v={v}"></script>\n'
                                    f'<script src="/assets/stylish.js?v={v}"></script>\n</body>', 1)
                # 四季の切り替えを今のトップより早く（1枚 6秒→3.8秒、最初の切り替えまで 3.5秒→2.6秒。2026-10-06）
                .replace('<div class="fv-photo">', '<div class="fv-photo" data-stay="3800" data-first="2600">', 1)
                # 入口のタイルの文字は stylish.js が帯のあとに出すので、もとのふわっと表示（.fade）から外す
                .replace('<span class="entry-body fade">', '<span class="entry-body">'))
    for a in ('<h2 class="fade"><span>目的に合わせて', '<h2 class="fade"><span>LFグループについて',
              '<h2 class="fade">数字で見るLFグループ', '<h2 class="fade"><span>保険やお金について'):
        assert a in html_, a
        html_ = html_.replace(a, a.replace('class="fade"', 'class="s-lines"'), 1)
    return html_


# トップの季節の写真「人生の四季」（2026-10-05 採用。春→夏→秋→冬→三世代の春の順）：
# 春＝新婚の二人、夏＝子育て（公園で肩車）、秋＝40歳前後の夫婦と男の子、冬＝60代前半の二人、
# そして三世代の春＝祖父母になった二人と孫の女の子（冬のあとにもう一度春が来て、最初の新婚の春へ戻る）。
# 「同じ家族の1年」（春＝hero.jpg・夏＝hero-summer.jpg・秋冬＝hero-autumn/winter.jpg）と見比べて、こちらに決めた。
# 夏に hero.jpg を使うと、それまでのトップの写真と同じに見えるので、夏は hero-summer.jpg を使う
SEASON_PHOTOS = ('life-spring.jpg', 'hero-summer.jpg', 'life-autumn.jpg', 'life-winter.jpg', 'life-spring2.jpg')


# 人物なしの案（/scene/ で見比べ用。2026-10-06）：事業ごとに「人の気配が感じられる暮らしの風景」。
# 保険＝家族の靴が並ぶ玄関先、ライフライン＝朝のキッチン、暮らし＝コーヒーカップ2つのダイニング、法人＝開店前の小さなお店
SCENE_PHOTOS = ('scene-home.jpg', 'scene-kitchen.jpg', 'scene-dining.jpg', 'scene-shop.jpg')


def season_photos(top, photos=SEASON_PHOTOS, white_wrap=True):
    """トップのファーストビューの写真を、春→夏→秋→冬と切り替える（動きは src/season.css・season.js）。
    1枚目は最初から見せ、2枚目以降は最初の画面が出てから読み込むので data-src に置く
    （data-src="/images/…" も relative()・image_version() で相対パスとバージョン番号が付く）"""
    hero = '<img src="/images/hero.jpg" alt="" fetchpriority="high" onerror="this.remove()">'
    assert hero in top, 'ファーストビューの写真の書き方が変わった'
    first = hero.replace('<img ', '<img class="is-show" ').replace('/images/hero.jpg', f'/images/{photos[0]}')
    rest = ''.join(f'\n      <img data-src="/images/{name}" alt="">' for name in photos[1:])
    top = top.replace(hero, first + rest, 1)
    if not white_wrap:  # 最後から最初へ戻るときの白フェード（人生の四季の一区切り）を使わない
        top = top.replace('<div class="fv-photo">', '<div class="fv-photo" data-wrap="none">', 1)
    return top


def redirect(to):
    """前のURLから新しいページへ移すだけのページ。to は移る先（そのページから見た相対パス）"""
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={to}"><title>LFグループ株式会社</title></head>
<body><p><a href="{to}">ページを移動しました</a></p></body></html>
"""


# /season/・/life/ は試作のときのURL。お客さまに伝えている場合があるので、トップへ移す
SEASON_REDIRECT = redirect('../')


def main():
    global ASSET_V, SITE, RELEASE, SITE_URL
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', action='store_true', help='本番用を dist/ に書き出す')
    ap.add_argument('--site-url', default='', help='本番の公開URL（例：https://example.co.jp）')
    args = ap.parse_args()
    SITE_URL = args.site_url.rstrip('/')
    if args.release:
        RELEASE, SITE = True, BASE / 'dist'
        shutil.rmtree(SITE, ignore_errors=True)
        release_files()

    css = (SRC / 'style.css').read_text() + (SRC / 'pages.css').read_text() + (SRC / 'brand.css').read_text() + (SRC / 'refine.css').read_text() + (SRC / 'season.css').read_text()
    if RELEASE:
        css = re.sub(r'/\*[\s\S]*?\*/', '', css)
    else:
        css += """
  /* 試作の帯（--release では入れない） */
  .design-preview-note { position: relative; z-index: 60; padding: 6px var(--gutter); line-height: 18px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; background: #22303C; color: #fff; font-size: 12px; text-align: center; letter-spacing: .04em; }
  .design-preview-note ~ .header:not(.is-scrolled) { top: 30px; }
  .design-preview-note ~ .drawer { padding-top: calc(var(--header-h) + 54px); }
"""
    js = (SRC / 'main.js').read_text() + (SRC / 'season.js').read_text()
    # CSS・JS の中身が変わったら URL も変える。GitHub Pages は10分間ブラウザに覚えさせるため、
    # 変えないと「新しいページ＋古いデザイン」が組み合わさって表示が崩れる（MISSION の写真が消えた）
    ASSET_V = hashlib.sha1((css + js).encode()).hexdigest()[:8]
    write('assets/style.css', css)
    write('assets/main.js', js)

    top_base = layout('', TOP.replace('{{final_cta}}', final_cta()), loader=True)
    top = stylish_top(season_photos(top_base))  # 2026-10-06 スタイリッシュ版を本流に反映
    # 2026-10-07：本番のトップを /top-a2-wipe/ の形（名古屋の街の四季・斜めのマスク＋金の光・白文字のヒーロー）にした
    write('index.html', write_top_a2(top))
    if not RELEASE:
        # 動きの試作（/motion/）は /stylish/ にまとめ、本流のトップに反映した（2026-10-06）。前のURLはトップへ移す
        write('motion/index.html', redirect('../'))
        # スタイリッシュ版の試作（/stylish/）は本流のトップに反映した（2026-10-06）。前のURLはトップへ移す
        write('stylish/index.html', redirect('../'))
        write('season/index.html', SEASON_REDIRECT)
        write('life/index.html', SEASON_REDIRECT)
        write('scene/index.html', season_photos(top_base, SCENE_PHOTOS, white_wrap=False)
              .replace('リニューアルの試作です', 'リニューアルの試作です・人物なしの写真の試作版', 1))
    write('about/index.html', with_rf(layout('私たちについて', page_about(), 'about')))
    write('personal/index.html', with_rf(layout('個人のお客様', page_personal(), 'personal')))
    write('corporate/index.html', with_rf(layout('法人のお客様', page_corporate(), 'corporate')))
    write('partner/index.html', with_rf(layout('アライアンス事業', page_partner(), 'partner')))
    # 事業内容・取り扱いサービス・保険は、中身を上の3ページに分けた（2026-10-06）。前のURLは近いページへ移す
    write('business/index.html', redirect('../about/'))
    write('service/index.html', redirect('../personal/'))
    write('insurance/index.html', redirect('../personal/'))
    write('company/index.html', with_rf(layout('会社概要', page_company(), 'company')))
    write('contact/index.html', layout('お問い合わせ', page_contact(), 'contact'))
    write('recruitment/index.html', write_recruit_trials())  # 案A2のヒーロー（2026-10-07）。試作 /recruitment-a・a2・b・c は --release では書かない
    renders = {'operation': policy_operation, 'solicitation': policy_solicitation,
               'privacyprotection': policy_privacy, 'informationsecurity': policy_security}
    for key, label, _ in POLICIES:
        write(f'{key}/index.html', layout(label, page_policy(key, label, renders[key])))
    if RELEASE:
        write('404.html', layout('ページが見つかりません', page_404()).replace('<meta name="description"', '<meta name="robots" content="noindex">\n<meta name="description"', 1))


if __name__ == '__main__':
    main()
