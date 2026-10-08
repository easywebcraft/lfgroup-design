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
#   052-846-2135：お問い合わせ用。ヘッダー・CTA・フッター・会社概要に使う
#   052-846-8224：採用の応募先（採用情報ページとお問い合わせページ）
#   052-990-6159：今は使っていない番号（2026-10-04 クライアント確認）。サイトには載せない
TEL = '052-846-2135'
TEL_HREF = 'tel:0528462135'
RECRUIT_TEL = '052-846-8224'
RECRUIT_TEL_HREF = 'tel:0528468224'
ADDRESS = '愛知県名古屋市東区葵3丁目14-5 リッチコーポ2階'
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


def final_cta(title=None, text=None, button='お問い合わせ', eyebrow='Contact'):
    """ページ最下部のお問い合わせ欄（全ページ共通）。ボタンは1つ、電話は小さく添える。
    title・text を渡すと、そのページ向けの文にできる（アライアンス事業：2026-10-07 お客様の要望）。"""
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
      <p class="contact-cta-tel fade">お電話でのお問い合わせ<a href="{TEL_HREF}">{TEL}</a></p>
    </div>
  </section>
'''


def company_brief():
    """会社名・所在地・事業内容だけの短い会社案内（トップと同じ形）。"""
    return f'''  <section class="section company-brief">
    <div class="wrap company-brief-inner">
      <div>
        <p class="eyebrow fade">Company</p>
        <h2 class="fade">会社情報</h2>
      </div>
      <dl class="brief-list fade">
        <div><dt>会社名</dt><dd>{COMPANY}</dd></div>
        <div><dt>所在地</dt><dd>〒{POSTAL} {ADDRESS}</dd></div>
        <div><dt>事業内容</dt><dd>金融コンサル・保険代理店業務</dd></div>
      </dl>
      <p class="fade"><a class="link-arrow" href="/company/">会社概要を見る{ARROW}</a></p>
    </div>
  </section>
'''


# ───────────────────────── 各ページ ─────────────────────────

def page_about():
    """トップが「写真＋親しみ」なので、こちらは文字・余白・線・濃紺で企業の姿勢を見せる。
    主役は「お客様本位の業務運営方針」。MISSION はトップと別の、文字だけの見せ方にする。"""
    fd = [
        ('保険・固定費削減のプロフェッショナルとして、', 'お客様の立場になって、誠実・公正に業務を行います。'),
        ('お客様のニーズを把握し、', 'お客様にふさわしい商品とサービスを提供し続けます。'),
        ('お客様が納得してご契約できるよう、', '商品とサービスの説明を丁寧かつわかりやすく行います。'),
        ('事故に遭われたお客様に対して、', '迅速に保険金の支払いができるようアドバイスし、', '事故処理完了まで適切な対応を行います。'),
        ('お客様の立場で行動するために、', '継続的に教育を行うとともに、適切な管理体制を整備します。'),
    ]
    # 冒頭は「何の会社か」を一言で。下の言葉は本文（ライフライン・保険・固定費の見直し）から取る（FP事業はいまは行っていない）
    hero = page_hero(
        'About', '私たちについて', [('私たちについて', '/about/')],
        photo='about-hero.jpg', pos='50% 72%',
        extra='        <p class="about-message fade"><span>暮らしにかかるお金を、</span><br><span>一緒に見直す会社です。</span></p>',
        chips=('保険', '家計', 'ライフライン', 'ライフプラン'))
    return hero + f'''
  <section class="section about-intro">
    <div class="wrap">
      <div class="about-intro-body fade">
        <p class="eyebrow">Introduction</p>
        <h2 class="about-intro-title no-punct"><span>顧客満足度を最優先に</span><span>人々の生活を向上させます</span></h2>
        <p class="about-intro-text">お客様の暮らしにゆとりが生まれるよう、保険の見直しや、電気・ガスなどのライフラインをご案内しています。</p>
      </div>
    </div>
  </section>

  <section class="section about-mission" id="mission">
    <div class="wrap">
      <p class="eyebrow fade">Mission</p>
      <h2 class="about-mission-msg fade"><span>暮らしにゆとりを</span><br><span>お客様とともに</span></h2>
      <div class="about-mission-text fade">
        <p>毎月の暮らしにかかるお金だからこそ、<br>一度の見直しが、これからの家計につながります。</p>
        <p>LFグループ株式会社は、<br>ゆとりある生活の実現をお手伝いします。</p>
      </div>
      <p class="about-mission-quote fade"><span>家計にゆとりが生まれることで、</span><br><span>暮らしの選択肢も広がっていく。</span></p>
    </div>
  </section>

  <section class="section about-policy">
    <div class="wrap">
      <div class="about-policy-grid">
        <div class="about-policy-head">
          <p class="eyebrow fade">Policy</p>
          <h2 class="fade">お客様本位の<br>業務運営方針</h2>
          <p class="fade" style="margin-top:32px"><a class="link-arrow" href="/operation/">主な取組内容を見る{ARROW}</a></p>
        </div>
        {policy_lines_html(fd)}
      </div>
    </div>
  </section>

''' + company_brief() + final_cta()


def tags(items):
    return '<ul class="svc-items">' + ''.join(f'<li>{t}</li>' for t in items) + '</ul>'




LIFE_SERVICES = [
    ('ライフライン', 'Lifeline', 'service-lifeline.jpg', 'IMAGE：暮らしのあかり', ['電気', 'ガス', '水道']),
    ('インターネット', 'Internet', 'service-internet.jpg', 'IMAGE：住まいとネット', ['フレッツ光', '光コラボレーション', 'ダークファイバー系光回線', '電力系光回線']),
    ('ウォーターサーバー', 'Water Server', 'service-water.jpg', 'IMAGE：水・キッチン', ['浄水器型ウォーターサーバー']),
]


# ───── 見る人ごとのページ（2026-10-06）：個人のお客様・法人のお客様・提携企業様 ─────
# 文言は今のサイト（保険代理店事業・アライアンス事業・パートナー事業・
# 取り扱いサービス・お客様本位の業務運営方針・勧誘方針）にあるものだけで組む

def strengths(items, cols=3):
    """強みのカード。items は (英字, 見出し, 本文)。見出しは <br> で改行位置を決められる"""
    cards = ''.join(f'''
        <article class="str-item fade">
          <p class="str-num">{i + 1:02d}<span>{en}</span></p>
          <h3>{title}</h3>
          <p class="text">{text}</p>
        </article>''' for i, (en, title, text) in enumerate(items))
    return f'''  <section class="section bg-blue" id="strengths">
    <div class="wrap">
      <p class="eyebrow fade">Strengths</p>
      <h2 class="fade">強み</h2>
      <div class="str-list" style="--cols:{cols}">{cards}
      </div>
    </div>
  </section>
'''


def life_cards():
    """ライフライン・インターネット・ウォーターサーバーのカード（取り扱いサービスのページと同じ形）"""
    return ''.join(f'''
        <article class="svc fade">
          <div class="photo"><span class="ph">{ph}</span><img src="/images/{img}" alt="" onerror="this.remove()"></div>
          <div class="svc-body">
            <h3>{name}<small>{en}</small></h3>
            {tags(items)}
          </div>
        </article>''' for (name, en, img, ph, items) in LIFE_SERVICES)


def page_nav(items):
    """冒頭に置くページ内の目次（強み・サービスなどへ移動）"""
    links = ''.join(f'<a class="svc-nav-item" href="#{k}"><b>{i + 1:02d}</b><span class="sn-name">{n}</span>{ARROW}</a>'
                    for i, (k, n) in enumerate(items))
    return f'        <nav class="svc-nav fade" aria-label="このページの内容">{links}</nav>'


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


def rf_hero(crumb, eyebrow, title, lead, button, photos, big):
    """個人・法人のお客様の冒頭（2026-10-08 松本さん「TOPページのFVの見せ方を取り入れて」）。
    トップと同じ部品（src/recruit-fv.css・recruit-fv.js）：写真が4.5秒ごとに斜めのマスクで切り替わり金の光が走る、
    大きな英字（明朝体系）、1文字ずつ出る白い明朝の見出し、マウスとスクロールで奥行き。
    トップ専用の指定（ページ全体を紺にする等）は .rf-sub で外す。title・lead は2行（(1行目, 2行目)）"""
    imgs = ''.join('<img class="%s" src="/images/%s" alt="" style="object-position:%s" %s onerror="this.remove()">'
                   % ('is-on' if n == 0 else '', f, pos, 'fetchpriority="high"' if n == 0 else 'data-eager') for n, (f, pos) in enumerate(photos))
    words = ''.join(f'<span>{w}</span>' for w in big)
    return f'''  <section class="rf rf-a rf-v rf-top rf-wipe rf-serif rf-sub" data-fx="a" data-stay="4500">
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


def ps_worries(title, items, answer, bg='bg-blue', band=False):
    """お悩みの段（個人・法人で共通）。items は (アイコン, 一文)。
    band=True：段の頭を、トップの「FIND YOUR PAGE」のような狭い見出しの帯にする（2026-10-08 松本さん「TOPのような狭めに」「色はそのままでOK」。個人・法人のお客様）。
    問いかけの見出しは帯の中に残す"""
    lis = ''.join(f'''
          <li class="fade">{ps_icon(k)}<p>{t}</p></li>''' for k, t in items)
    if band:
        head = f'''  <div class="ps-band" id="worries">
    <div class="wrap">
      <p class="eyebrow">Worries</p>
      <h2>{title}</h2>
    </div>
  </div>
  <section class="section {bg} ps-worries ps-worries-banded">
    <div class="wrap">'''
    else:
        head = f'''  <section class="section {bg} ps-worries" id="worries">
    <div class="wrap">
      <p class="eyebrow fade">Worries</p>
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


def ps_flow(items, bg=''):
    steps = ''.join(f'''
        <li class="fade"><p class="ps-step">STEP<b>{i + 1:02d}</b></p><h3>{t}</h3><p>{x}</p></li>''' for i, (t, x) in enumerate(items))
    return f'''
  <section class="section {bg}" id="flow">
    <div class="wrap">
      <p class="eyebrow fade">Flow</p>
      <h2 class="fade">ご相談の流れ</h2>
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
                        button='無料相談を予約する'))


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
      <p class="text fade" style="margin-top:16px">生命保険と損害保険の両面から、経営者・従業員・事業活動の3つの視点で、企業のリスクへの備えを考えます。</p>{''.join(groups)}
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
      <p class="text fade" style="margin-top:16px">企業の成長とともに、備えるべきリスクや必要な資金は変わります。<br class="pc">今の経営ステージに合わせて、優先したい備えをご提案します。</p>
      <div class="co-stage-list">{stages}
      </div>
    </div>
  </section>
'''
            + ps_flow(CO_FLOW) + ps_faq(CO_FAQ) + '\n'
            + final_cta(title='<span>企業の未来に</span><br><span>確かな備えを</span>',
                        text='経営者の保障、従業員の福利厚生、<br>事業活動に伴うさまざまなリスクまで。<br>企業の状況に合わせた対策を一緒に考えます。',
                        button='法人保険の相談を申し込む', eyebrow='Your Business, Our Commitment.'))


def page_partner():
    """アライアンス事業。2段落：個人のお客様（アライアンスサービス）／提携事業者様（強み・サービス）。2026-10-07 お客様の要望"""
    hero = page_hero('Alliance', 'アライアンス事業', [('アライアンス事業', '/partner/')],
                     lead='マンション・アパートのご入居者様へのご案内を通じて、<br class="pc">ご入居者様の固定費の見直しと、<br class="pc">提携企業様・パートナー様の事業の発展をお手伝いします。',
                     photo='scene-home.jpg', pos='70% 55%',
                     extra=page_nav([('for-personal', '個人のお客様'), ('for-partner', '提携事業者様')]))
    return hero + f'''
  <section class="section" id="for-personal">
    <div class="wrap">
      <p class="eyebrow fade">For Personal</p>
      <h2 class="fade">個人のお客様</h2>
      <p class="text fade" style="margin-top:16px">マンションやアパートのご入居者様へ、ガスや電気などのライフライン、インターネット回線、ウォーターサーバーなどのお手続きやご案内を行います。<br class="pc">経験豊富なオペレーターが、丁寧にご案内します。</p>
      <p class="eyebrow fade" style="margin-top:56px">Alliance Service</p>
      <h3 class="sub-title fade" style="margin-top:12px">アライアンスサービス</h3>
      <div class="svc-grid svc-sub-grid">{life_cards()}
      </div>
    </div>
  </section>

  <section class="section bg-blue" id="for-partner">
    <div class="wrap">
      <p class="eyebrow fade">For Partner</p>
      <h2 class="fade">提携事業者様</h2>
      <p class="text fade" style="margin-top:16px">不動産管理会社など、提携企業様・パートナー様の事業の発展をお手伝いします。</p>
      <div class="partner-flow" aria-label="提携サービスの役割">
        <article><p class="eyebrow">Partner</p><h3>提携企業様・パートナー様</h3><p>当社と協力し、ご入居者様へのサービス案内につなげます。</p></article>
        <span class="flow-arrow" aria-hidden="true">→</span>
        <article><p class="eyebrow">LF Group</p><h3>LFグループ</h3><p>オペレーターが、お手続きやサービスを丁寧にご案内します。</p></article>
        <span class="flow-arrow" aria-hidden="true">→</span>
        <article><p class="eyebrow">Resident</p><h3>ご入居者様</h3><p>ライフライン・インターネットなどのご案内を受けられます。</p></article>
      </div>
    </div>
  </section>
''' + strengths([
        ('Operator', '経験豊富な<br>オペレーター', '経験豊富なオペレーターが、ご入居者様へ丁寧にご案内します。'),
        ('Lineup', '厳選した<br>商品・サービス', 'ライフライン・インターネット回線・ウォーターサーバーなど、厳選した商品・サービスを取り揃えています。'),
        ('Check', '厳格なチェック体制と<br>管理', 'アライアンス事業で培ったノウハウを活かし、厳格なチェック体制のもと、ミスなく、きめ細やかに対応します。'),
        ('Partnership', '長期的な<br>パートナーとして', '提携企業様・パートナー様の事業の発展を支え、双方にとっての利益と価値を、長期的に生み出すことを目指します。'),
    ], cols=2) + f'''
  <section class="section" id="service">
    <div class="wrap">
      <p class="eyebrow fade">Service</p>
      <h2 class="fade">サービス</h2>
      <div class="ins-for-grid" style="margin-top:48px">
        <article class="ins-for-item fade" id="alliance">
          <p class="eyebrow">Alliance</p>
          <h2>アライアンス事業</h2>
          <p class="text">マンションやアパートのご入居者様に、ライフライン・インターネット回線・ウォーターサーバーなどのお手続きやサービスをご案内します。</p>
          <p class="text">経験豊富なオペレーターが、厳選した商品・サービスを丁寧にご案内します。提携企業様とサービスをご利用のお客様に、安心・確実なサポートをご提供します。</p>
        </article>
        <article class="ins-for-item fade" id="partner">
          <p class="eyebrow">Partner</p>
          <h2>パートナー事業</h2>
          <p class="text">提携企業様・パートナー様と協力し、当社が取り扱う商品・サービスをお客様にご提供しています。</p>
          <p class="text">アライアンス事業で培ったノウハウを活かし、お客様に本当に必要なものを丁寧にご提案します。厳格なチェック体制のもと、ミスなく、きめ細やかに対応します。</p>
          <p class="biz-note">提携企業様・パートナー様募集中</p>
        </article>
      </div>
    </div>
  </section>

''' + final_cta(
        '<span class="cta-nowrap">アライアンス事業について</span><br><span>お気軽に</span><span>ご相談ください</span>',
        '提携をご検討の企業様・パートナー様、ご入居者様へのライフライン・インターネットなどのご案内について、まずはお気軽にお問い合わせください。')


def page_company():
    # 「愛知県名古屋市東区葵3丁目14-5」を Google マップの埋め込み形式にしたもの
    q = 'https://www.google.com/maps/embed?origin=mfe&amp;pb=!1m3!2m1!1z5oSb55-l55yM5ZCN5Y-k5bGL5biC5p2x5Yy66JG1M-S4geebrjE0LTU!6i16'
    links = ''.join(f'<a href="{h}">{l}{ARROW}</a>' for _, l, h in POLICIES)
    # 冒頭は会社名・所在地・事業内容（どれも今の会社概要にある情報）。写真は所在地の名古屋の街並みとして見せる
    return page_hero('Company', '会社概要', [('会社概要', '/company/')],
                     photo='cta-final.jpg', pos='50% 62%', caption='Nagoya, Aichi',
                     extra=(f'        <div class="co-hero fade">\n'
                            f'          <p class="co-name">{COMPANY}</p>\n'
                            f'          <p class="co-addr">〒{POSTAL}<br>愛知県名古屋市東区葵3丁目14-5<br>リッチコーポ2階</p>\n'
                            f'          <p class="co-biz">金融コンサル・保険代理店業務を行っています。</p>\n'
                            f'        </div>')) + f'''
  <section class="section co-philosophy" id="philosophy">
    <div class="wrap">
      <p class="eyebrow fade">Philosophy</p>
      <h2 class="fade">企業理念</h2>
      <p class="co-philosophy-main no-punct fade"><span>顧客満足度を最優先に</span><span>人々の生活を向上させます</span></p>
      <div class="co-philosophy-sub fade">
        <p class="co-philosophy-head">お客様の暮らしにゆとりを</p>
        <p class="text">LFグループ株式会社は、お客様に寄り添い、ゆとりある生活の実現をお手伝いします。</p>
        <p class="text">お金のゆとりは、暮らしの安心や人生の豊かさにつながります。</p>
      </div>
    </div>
  </section>

  <section class="section bg-blue" id="message">
    <div class="wrap co-message">
      <div>
        <p class="eyebrow fade">Message</p>
        <h2 class="fade">代表挨拶</h2>
      </div>
      <div class="fade">
        <!-- ★公開前に必要：代表挨拶は、今のサイトにある言葉（顧客満足度を最優先に・お客様本位の運営方針・迅速な事故対応）
             だけで作った「下書き」（2026-10-07）。ご本人の言葉ではないので、代表の確認・修正をいただいたら、.note-draft の印を外す。お写真もいただいたら差し替える -->
        <p class="note-draft">下書き（代表の確認前）</p>
        <p class="co-message-lead">お客様の毎日の暮らしを<br>保険とお金の面から支えます</p>
        <div class="co-message-body">
          <p>LFグループ株式会社は、「顧客満足度を最優先に、人々の生活を向上させます」という理念のもと、保険を中心に、お客様の暮らしに関わるさまざまなご案内をしています。</p>
          <p>ゆとりある生活の実現のために、お客様一人ひとりの立場になって、誠実・公正にご提案いたします。</p>
          <p>ご契約のあとも、お客様が安心して過ごせるよう、長く寄り添います。万が一の事故のときは、休日・夜間も、保険金のお支払いまで迅速に対応いたします。</p>
          <p>これからも、お客様に信頼していただけるよう、社員一同、学び続けてまいります。保険やお金のことで気になることがあれば、どうぞお気軽にご相談ください。</p>
        </div>
        <p class="co-message-name">代表 遠藤 昇平</p>
      </div>
    </div>
  </section>

  <section class="section co-first">
    <div class="wrap">
      <dl class="company-list full">
        <div><dt>会社名</dt><dd>{COMPANY}</dd></div>
        <div><dt>代表者</dt><dd>遠藤 昇平</dd></div>
        <div><dt>所在地</dt><dd>〒{POSTAL}<br>愛知県名古屋市東区葵3丁目14-5<br>リッチコーポ2階</dd></div>
        <!-- ★要確認：2つの番号の用途（代表／お問い合わせ）が今のサイトに書かれていない。確認できたら「代表」などを添える -->
        <div><dt>電話番号</dt><dd><a href="{TEL_HREF}">{TEL}</a></dd></div>
        <div><dt>事業内容</dt><dd>金融コンサル・保険代理店業務</dd></div>
        <div><dt>適格請求書発行<br>事業者登録番号</dt><dd>T4180001157727</dd></div>
      </dl>
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

''' + final_cta()


def page_contact():
    # 電話のみの受付。受付時間は既存の表示を維持（公開前に要確認）。
    contacts = f'''      <div class="contact-tel contact-first">
        <div class="tel-box tel-main">
          <h2>保険・固定費のご相談</h2>
          <a class="tel-number" href="{TEL_HREF}">{TEL}</a>
          <p class="tel-hours">受付時間 10:00～18:00</p>
          <a class="btn btn-primary" href="{TEL_HREF}">電話で相談する{ARROW}</a>
        </div>
        <div class="tel-box">
          <h2>採用に関するお問い合わせ</h2>
          <a class="tel-number" href="{RECRUIT_TEL_HREF}">{RECRUIT_TEL}</a>
          <p class="tel-hours"><a class="link-arrow" href="/recruitment/">採用情報を見る{ARROW}</a></p>
        </div>
      </div>'''
    return page_hero('Contact', 'お問い合わせ', [('お問い合わせ', '/contact/')],
                     lead='保険や固定費の見直しについて、お電話でご相談を承っています。',
                     compact=True, extra=contacts).replace('sub-hero compact', 'sub-hero compact contact-intro', 1)


def page_recruitment():
    rows = [
        ('職務内容', '生命保険・損害保険などの金融商品のご提案・販売と、ご契約後のアフターサービス'),
        ('雇用形態', '契約社員<br>※試用期間3カ月　正社員登用制度あり（成績基準あり）'),
        ('応募資格', '学歴・性別・国籍不問'),
        ('勤務地', '愛知県名古屋市東区'),
        ('勤務時間', '10時～18時'),
        ('給与', '成果連動型報酬（営業成績に応じて支給）<br>給与：固定給20万円＋成果報酬<br>年収1,000万円も可能'),
        ('選考方法', '書類面接・面接試験（1～2回）'),
        ('応募方法', 'お電話にてご応募ください'),
        ('郵送先・応募先', f'〒{POSTAL} {ADDRESS}'),
    ]
    dl = ''.join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in rows)
    # FV：求職者に「どんな仕事か」を最初に伝える。コピーは募集要項・職務内容の範囲で書く（2026-10-06）
    # ★TODO：写真は仮。実際の社員・オフィス・相談風景の写真をいただいたら差し替え、.rc-photo-todo を消す
    # FV のすぐ下に募集要項にある4項目の小さなカード（同じ4項目だった「働くポイント」の段はこれにまとめた）
    facts = [
        ('応募資格', '学歴・性別・国籍不問', ''),
        ('勤務時間', '10:00〜18:00', ''),
        ('給与', '固定給＋成果報酬', '固定給20万円＋成果報酬'),
        ('雇用形態', '契約社員', '正社員登用制度あり（成績基準あり）'),
    ]
    cards = ''.join(f'<li class="fade"><p class="rc-fact-label">{k}</p><p class="rc-fact-value">{v}</p>'
                    + (f'<p class="rc-fact-note">{n}</p>' if n else '') + '</li>' for k, v, n in facts)
    return f'''  <section class="rc-fv">
    <div class="rc-fv-photo fade"><img src="/images/about-hero.jpg" alt="" data-eager onerror="this.remove()"><span class="rc-photo-todo">写真は仮</span></div>
    <div class="wrap rc-fv-copy">
      <ol class="crumb fade" aria-label="パンくずリスト"><li><a href="/">トップ</a></li><li aria-current="page">採用情報</li></ol>
      <p class="eyebrow fade">Recruitment<span class="rc-fv-ja">採用情報</span></p>
      <h1 class="rc-fv-title fade"><span>人の人生に向き合いながら</span><span>自分の未来も変えていく</span></h1>
      <p class="rc-fv-lead fade">生命保険・損害保険のご提案とアフターサービスを通じて、<br class="pc">お客様のこれからの暮らしを支える仕事です。</p>
      <p class="rc-status fade"><span class="dot"></span>Entry Open<b>エントリー受付中</b></p>
      <p class="rc-links fade"><a class="btn btn-primary" href="tel:0528468224">電話で応募・相談する{ARROW}</a><a class="link-arrow" href="#requirements">募集要項を見る{ARROW}</a></p>
    </div>
  </section>
  <section class="rc-facts" aria-label="募集のポイント">
    <div class="wrap"><ul class="rc-fact-list">{cards}</ul></div>
  </section>

  <section class="section bg-blue" id="work">
    <div class="wrap rc-work">
      <div>
        <p class="eyebrow fade">Work</p>
        <h2 class="fade">仕事内容</h2>
      </div>
      <div class="fade">
        <p class="rc-work-lead">生命保険・損害保険などの金融商品のご提案・販売と、ご契約後のアフターサービス</p>
        <p class="text">LFグループ株式会社は、大手保険会社の代理店として各種保険を取り扱っています。お客様のライフプランに合わせた最適な保険をご提案します。ご契約後も、生涯を安心して過ごせるよう、長期的にサポートします。</p>
        <p style="margin-top:24px"><a class="link-arrow" href="/personal/#service">保険について見る{ARROW}</a></p>
      </div>
    </div>
  </section>

  <section class="section" id="requirements">
    <div class="wrap">
      <p class="eyebrow fade">Requirements</p>
      <h2 class="fade" style="margin-bottom:40px">募集要項</h2>
      <dl class="company-list full">{dl}</dl>
    </div>
  </section>

  <section class="section bg-blue">
    <div class="wrap narrow">
      <p class="eyebrow fade">Entry</p>
      <h2 class="fade">ご応募・採用に関するお問い合わせ</h2>
      <div class="recruit-tel fade">
        <a href="tel:0528468224">052-846-8224</a>
      </div>
    </div>
  </section>
'''


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
    <div><dt>受付時間</dt><dd>10:00～18:00</dd></div>
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
             ('16:00', 'PROPOSAL', 'ご提案の準備', 'recruit-1600.jpg'), ('18:00', 'FINISH', '一日のおわり', 'recruit-1800.jpg')]
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
    # 見出し（2026-10-07 松本さん指定）：「お客様のこれからに寄り添い自分のこれからも描いていく」。英字は SUPPORT／THEIR FUTURE／SHAPE YOUR OWN
    # 指定の文は読点「、」・ピリオド「.」を含むが、指定どおりそのまま入れる
    copy_v = (copy.replace('<h1 class="rc-fv-title fade"><span>人の人生に向き合いながら</span><span>自分の未来も変えていく</span></h1>',
                           '<h1 class="rc-fv-title rv-title"><span>お客様のこれからに寄り添い</span><span>自分のこれからも描いていく</span></h1>')
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
                                '<section class="rf rf-a rf-v rf-wipe rf-serif" data-fx="a" data-stay="4500">')
                       .replace(copy, '<p class="rv-big" aria-hidden="true"><span>SUPPORT</span><span>THEIR FUTURE</span><span>SHAPE YOUR OWN</span></p>\n    ' + GOLD_WIPE + '\n    ' + copy_v)
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
    write('about/index.html', layout('私たちについて', page_about(), 'about'))
    write('personal/index.html', with_rf(layout('個人のお客様', page_personal(), 'personal')))
    write('corporate/index.html', with_rf(layout('法人のお客様', page_corporate(), 'corporate')))
    write('partner/index.html', layout('アライアンス事業', page_partner(), 'partner'))
    # 事業内容・取り扱いサービス・保険は、中身を上の3ページに分けた（2026-10-06）。前のURLは近いページへ移す
    write('business/index.html', redirect('../about/'))
    write('service/index.html', redirect('../personal/'))
    write('insurance/index.html', redirect('../personal/'))
    write('company/index.html', layout('会社概要', page_company(), 'company'))
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
