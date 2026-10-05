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
NAV = [
    ('about', '私たちについて', '/about/'),
    ('business', '事業内容', '/business/'),
    ('service', 'サービス', '/service/'),        # メニューでは短く。ページの見出しは「取り扱いサービス」
    ('company', '会社情報', '/company/'),        # 同上「会社概要」
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
    <p class="ll-catch"><span class="l1">保険とお金を整えて、</span><br><span class="l2">安心できる未来へ。</span></p>
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
    band = ''
    if photo:
        style = f'object-position:{pos}' + (f';transform:scale({zoom});transform-origin:{pos}' if zoom != 1 else '')
        band = (f'\n    <div class="wrap"><figure class="hero-band fade">'
                f'<img src="/images/{photo}" alt="" data-eager style="{style}" onerror="this.remove()">'
                + (f'<figcaption>{caption}</figcaption>' if caption else '') + '</figure></div>')
    cls = 'page-hero sub-hero' + (' has-photo' if photo else '') + (' compact' if compact else '')
    return f'''  <section class="{cls}">
    <div class="wrap sub-hero-copy">
      <ol class="crumb fade" aria-label="パンくずリスト">{''.join(items)}</ol>
      <p class="eyebrow fade">{label}</p>
      {title_html}{lead_html}{chips_html}{extra_html}
    </div>{band}
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


def final_cta():
    """ページ最下部のお問い合わせ欄（全ページ共通）。ボタンは1つ、電話は小さく添える。"""
    return f'''  <section class="contact-cta" id="final-cta">
    <div class="wrap contact-cta-inner">
      <p class="eyebrow fade">Contact</p>
      <h2 class="fade"><span>保険やお金について、</span><br><span>気になることから</span><span>ご相談ください。</span></h2>
      <p class="text fade">保険の見直しや家計、これからのお金について、まずはお気軽にお問い合わせください。</p>
      <p class="contact-cta-actions fade">
        <a class="btn btn-primary" href="/contact/">お問い合わせ{ARROW}</a>
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
        <div><dt>事業内容</dt><dd>ファイナンシャルプランニング・金融コンサル・保険代理店業務</dd></div>
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
    # 冒頭は「何の会社か」を一言で。下の4つは本文（ライフライン・保険・FP・ライフプランの見直し）から取る
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
        <h2 class="about-intro-title"><span>顧客満足度を最優先に、</span><span>人々の生活を向上させます。</span></h2>
        <p class="about-intro-text">弊社はお客様の固定費を削減することを目的に、電気やガスなどのライフラインの代行業務、保険の見直しに加え、FP資格取得者が多数在籍しており、NISAやふるさと納税をはじめとした投資や節税などを通して、お客様のライフプランの見直しを行っています。</p>
      </div>
    </div>
  </section>

  <section class="section about-mission" id="mission">
    <div class="wrap">
      <p class="eyebrow fade">Mission</p>
      <h2 class="about-mission-msg fade"><span>固定費削減で、</span><br><span>家計を見直す。</span></h2>
      <div class="about-mission-text fade">
        <p>毎月かかる固定費だからこそ、<br>一度の見直しが、これからの家計につながります。</p>
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


BUSINESS = [
    ('insuranceagency', '保険代理店事業', 'Insurance Agency', [
        'LFグループ株式会社では、大手保険会社の代理店として、個人のお客様・法人のお客様の各種保険を取り扱っています。',
        '自動車・バイク・病気・ケガ・旅行・趣味・こども・生命保険等、お客様のライフプランに合わせた最適な保険を提案するとともに、生涯を安心して過ごせるように長期的なサポートを行います。',
    ], ''),
    ('financialplanning', 'ファイナンシャルプランニング事業', 'Financial Planning', [
        'LFグループ株式会社では、ファイナンシャルプランニング技能士（国家資格）を保有するスタッフが多数在籍しています。',
        'お金の専門家であるFPがライフプラン・家計・保険・年金・住宅資金・教育資金・税金・資産運用・介護・医療費・相続・贈与などのお悩みに対して、適切なアドバイスを行い、お客様の人生がより良くなるようサポートさせて頂きます。',
    ], ''),
    ('alliance', 'アライアンス事業', 'Alliance', [
        '私たちLFグループ株式会社は、マンションやアパートのご入居者様へガスや電気などのライフライン、インターネット回線、ウォーターサーバーなどのお手続きやご案内を行います。',
        '経験豊富なオペレーターによる丁寧なご案内に加え、選りすぐりの商材を取り揃えており、提携いただく企業様とエンドユーザー様に安心確実なサポートをご提供いたします。',
    ], ''),
    ('partner', 'パートナー事業', 'Partner', [
        'LFグループ株式会社では、当社が取り扱っている商材やサービスを提携企業様、パートナー様と協力してお客様にご提供しています。',
        'アライアンス事業で培ったノウハウを活かして、お客様に本当に必要なものを丁寧にご提案するとともに、厳格なチェック体制と管理の下でミスなくきめ細やかな対応を行うことができます。',
        '提携企業様・パートナー様の事業繁栄をお手伝いし、相互の長期的な利益追求・価値創造を目指します。',
    ], '提携企業様・パートナー様募集中'),
]
# 「これは自分向けか」をすぐ判断できるよう、4事業を2つに分けて見せる
BIZ_GROUPS = [
    ('customers', '個人・法人のお客様へ', 'For Customers', ('insuranceagency', 'financialplanning')),
    ('partners', '提携企業様へ', 'For Partners', ('alliance', 'partner')),
]


def page_business():
    num = {k: i + 1 for i, (k, *_) in enumerate(BUSINESS)}
    name = {k: n for k, n, *_ in BUSINESS}
    # 冒頭の一覧：個人向け・法人向けの見出しの下に、番号付きのリンクカード。主力の保険代理店事業だけ軽く強調する
    index = ''
    for gid, glabel, _, keys in BIZ_GROUPS:
        links = ''.join(
            f'<a class="hero-biz" href="#{k}"><b>{num[k]:02d}</b><span class="hb-name">{name[k]}</span>'
            f'{"<small>Main</small>" if k == "insuranceagency" else ""}{ARROW}</a>'
            for k in keys)
        index += f'<div class="hero-biz-group"><p class="hbg-label">{glabel}</p><div class="hero-bizs">{links}</div></div>'
    groups = []
    for gid, glabel, gen, keys in BIZ_GROUPS:
        blocks = []
        for key, bname, en, paras, note in BUSINESS:
            if key not in keys:
                continue
            texts = ''.join(f'<p class="text">{p}</p>' for p in paras)
            note_html = f'<p class="biz-note">{note}</p>' if note else ''
            if key == 'insuranceagency':
                note_html = f'<p style="margin-top:24px"><a class="link-arrow" href="/insurance/">取り扱い保険・事故対応について見る{ARROW}</a></p>'
            blocks.append(f'''      <article class="biz-block fade" id="{key}">
        <div class="biz-visual"><span class="num">{num[key]:02d}</span>{ICONS[key]}</div>
        <div>
          <h2>{bname.replace('ファイナンシャルプランニング', '<span>ファイナンシャル</span><span>プランニング</span>')}</h2>
          <span class="card-en">{en}</span>
          {'<p class="badge"><span>国家資格</span>FP技能士在籍</p>' if key == 'financialplanning' else ''}
          <div style="margin-top:28px">{texts}</div>
          {note_html}
        </div>
      </article>''')
        groups.append(f'''  <section class="section biz-section{" bg-blue" if gid == "corporate" else ""}" id="{gid}">
    <div class="wrap">
      <div class="biz-group-head fade"><p class="eyebrow">{gen}</p><p class="biz-group-title">{glabel}</p></div>
{chr(10).join(blocks)}
    </div>
  </section>''')
    hero = page_hero('Business', '事業内容', [('事業内容', '/business/')], photo='hero.jpg', pos='70% 42%', zoom=1.12,
                     lead='保険、ファイナンシャルプランニング、固定費の見直しを通じて、<br class="pc">ゆとりある生活の実現をお手伝いします。',
                     extra=f'        <nav class="hero-biz-groups fade" aria-label="事業の一覧">{index}</nav>')
    return hero + '\n' + '\n\n'.join(groups) + '\n\n' + final_cta()


def tags(items):
    return '<ul class="svc-items">' + ''.join(f'<li>{t}</li>' for t in items) + '</ul>'


LIFE_INS = ['医療保険', 'がん保険', '終身保険', '変額保険', '収入保障保険', '定期保険', 'こども保険', '学資保険']
NONLIFE_INS = ['自動車保険', '火災保険', '損害保険', '賠償責任保険', '労災保険']


def page_insurance():
    """保険の詳細ページ。今のサイトの「保険代理店事業」「取り扱いサービス」「お客様本位の業務運営方針」
    「勧誘方針」「ファイナンシャルプランニング事業」の文言だけで組む。"""
    tiles = lambda items: ''.join(f'<li>{t}</li>' for t in items) + '<li class="etc">ほか</li>'
    sol = [
        '金融商品の販売等に際して、各種法令等を遵守し、適正な販売等に努めます。',
        'お客さまの金融商品に関するお客さまの知識・経験、契約目的、財産の状況等を総合的に勘案し、お客さまの意向と実情に応じた金融商品の販売等に努めます。',
        'お客さまへの商品説明等については、販売・勧誘形態に応じて、お客さま本位の方法等の創意工夫に努めます。',
        'お客さまのご意見等の収集に努め現状を把握し、また、お客さまの満足度を高めるよう努めます。',
    ]
    return page_hero('Insurance', '保険', [('取り扱いサービス', '/service/'), ('保険', '/insurance/')],
                     '大手保険会社の代理店として、個人のお客様・法人のお客様の各種保険を取り扱っています。',
                     photo='service-insurance.jpg', pos='45% 50%', chips=('個人保険', '法人保険', '生命保険', '損害保険')) + f'''
  <section class="section">
    <div class="wrap ins-intro">
      <div>
        <p class="eyebrow fade">Insurance Agency</p>
        <h2 class="fade">保険代理店事業</h2>
        <p class="text fade" style="margin-top:28px">LFグループ株式会社では、大手保険会社の代理店として、個人のお客様・法人のお客様の各種保険を取り扱っています。</p>
        <p class="text fade">自動車・バイク・病気・ケガ・旅行・趣味・こども・生命保険等、お客様のライフプランに合わせた最適な保険を提案するとともに、生涯を安心して過ごせるように長期的なサポートを行います。</p>
      </div>
      <aside class="ins-partners fade" aria-label="主力会社">
        <p class="ins-partners-head">主力会社</p>
        <ul>
          <li><span class="kind">生命保険</span>SOMPOひまわり生命</li>
          <li><span class="kind">損害保険</span>日新火災海上保険</li>
        </ul>
      </aside>
    </div>
  </section>

  <!-- 個人保険・法人保険は別の事業として扱う（2026-10-04 クライアント確認）。トップの「目的から探す」からここへ来る -->
  <section class="section ins-for">
    <div class="wrap ins-for-grid">
      <article class="ins-for-item fade" id="personal">
        <p class="eyebrow">Personal</p>
        <h2>個人保険のお客様</h2>
        <p class="text">生命保険・損害保険を、お客様のライフプランに合わせてご提案します。家計やライフプランのご相談は、ファイナンシャルプランニング技能士（国家資格）がお受けします。</p>
        <p><a class="link-arrow" href="/contact/">保険について相談する{ARROW}</a></p>
      </article>
      <article class="ins-for-item fade" id="corporate">
        <p class="eyebrow">Corporate</p>
        <h2>法人保険のお客様</h2>
        <p class="text">法人のお客様の保険も取り扱っています。保険の見直しなど、お気軽にご相談ください。</p>
        <p><a class="link-arrow" href="/contact/">保険について相談する{ARROW}</a></p>
      </article>
    </div>
  </section>

  <section class="section bg-blue">
    <div class="wrap">
      <p class="eyebrow fade">Lineup</p>
      <h2 class="fade">取り扱い保険</h2>
      <div class="ins-lineup">
        <article class="ins-cat fade">
          <h3>生命保険<span>Life Insurance</span></h3>
          <ul class="ins-tiles">{tiles(LIFE_INS)}</ul>
        </article>
        <article class="ins-cat fade">
          <h3>損害保険<span>Non-Life Insurance</span></h3>
          <ul class="ins-tiles">{tiles(NONLIFE_INS)}</ul>
        </article>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap ins-support">
      <div>
        <p class="eyebrow fade">Support</p>
        <h2 class="fade">事故対応</h2>
      </div>
      <div class="fade">
        <p class="ins-lead">事故に遭われたお客様に対して、迅速に保険金のお支払いができるようアドバイスし、事故処理完了まで適切な対応を行います。</p>
        <ul class="ins-checks">
          <li>事故に遭われたお客様への連絡頻度を高めています。</li>
          <li>休日・夜間の事故対応。</li>
        </ul>
        <p style="margin-top:24px"><a class="link-arrow" href="/operation/">お客様本位の業務運営方針を見る{ARROW}</a></p>
      </div>
    </div>
  </section>

  <section class="section about-policy">
    <div class="wrap">
      <div class="about-policy-grid">
        <div class="about-policy-head">
          <p class="eyebrow fade">Policy</p>
          <h2 class="fade">勧誘方針</h2>
          <p class="fade" style="margin-top:32px"><a class="link-arrow" href="/solicitation/">勧誘方針の全文を見る{ARROW}</a></p>
        </div>
        {policy_lines_html(sol)}
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <a class="ins-related fade" href="/business/#financialplanning">
        <div>
          <p class="eyebrow">Related</p>
          <p class="ins-related-title"><span>ファイナンシャル</span><span>プランニング事業</span></p>
          <p class="badge"><span>国家資格</span>FP技能士在籍</p>
          <p class="text" style="margin-top:16px">お金の専門家であるFPがライフプラン・家計・保険・年金・住宅資金・教育資金・税金・資産運用・介護・医療費・相続・贈与などのお悩みに対して、適切なアドバイスを行い、お客様の人生がより良くなるようサポートさせて頂きます。</p>
        </div>
        <span class="link-arrow">詳しく見る{ARROW}</span>
      </a>
    </div>
  </section>

''' + final_cta()


LIFE_SERVICES = [
    ('ライフライン', 'Lifeline', 'service-lifeline.jpg', 'IMAGE：暮らしのあかり', ['電気', 'ガス', '水道']),
    ('インターネット', 'Internet', 'service-internet.jpg', 'IMAGE：住まいとネット', ['フレッツ光', '光コラボレーション', 'ダークファイバー系光回線', '電力系光回線']),
    ('ウォーターサーバー', 'Water Server', 'service-water.jpg', 'IMAGE：水・キッチン', ['浄水器型ウォーターサーバー']),
]


def page_service():
    rows = [
        ('保険', 'Insurance', 'service-insurance.jpg', 'IMAGE：家族の安心', f'''
          <div class="svc-group"><h3>主力会社</h3><p>SOMPOひまわり生命・日新火災海上保険</p></div>
          <div class="svc-group"><h3>生命保険</h3>{tags(['医療保険', 'がん保険', '終身保険', '変額保険', '収入保障保険', '定期保険', 'こども保険', '学資保険', 'ほか'])}</div>
          <div class="svc-group"><h3>損害保険</h3>{tags(['自動車保険', '火災保険', '損害保険', '賠償責任保険', '労災保険', 'ほか'])}</div>
          <p class="svc-group"><a class="link-arrow" href="/insurance/">保険について詳しく見る{ARROW}</a></p>'''),
    ]
    ids = ['insurance', 'lifeline', 'internet', 'water']
    # 主力の保険は写真つきの大きな1段。その下に「暮らしのサービス」として3つをカードで並べる
    (name, en, img, ph, inner) = rows[0]
    main = f'''      <article class="svc-row svc-row-main fade" id="svc-insurance">
        <div class="photo"><span class="ph">{ph}</span><img src="/images/{img}" alt="" onerror="this.remove()"></div>
        <div>
          <p class="svc-main-tag">Main Service</p>
          <h2>{name}</h2>
          <p class="eyebrow">{en}</p>
          <p class="text" style="margin-top:20px">大手保険会社の代理店として、お客様のライフプランに合わせた最適な保険を提案します。</p>{inner}
        </div>
      </article>'''
    cards = ''.join(f'''
        <article class="svc fade" id="svc-{sid}">
          <div class="photo"><span class="ph">{ph}</span><img src="/images/{img}" alt="" onerror="this.remove()"></div>
          <div class="svc-body">
            <h3>{name}<small>{en}</small></h3>
            {tags(items)}
          </div>
        </article>''' for (name, en, img, ph, items), sid in zip(LIFE_SERVICES, ids[1:]))
    # 4サービスは番号＋名称＋矢印のナビ（各サービスの説明へ移動）。主力の保険だけ軽く強調する
    nav = ''.join(
        f'<a class="svc-nav-item{" main" if sid == "insurance" else ""}" href="#svc-{sid}">'
        f'<b>{i + 1:02d}</b><span class="sn-name">{name}<small>{en}</small></span>'
        f'{"<em>Main Service</em>" if sid == "insurance" else ""}{ARROW}</a>'
        for i, ((name, en, *_), sid) in enumerate(zip(rows[:1] + LIFE_SERVICES, ids)))
    return page_hero('Service', '取り扱いサービス', [('取り扱いサービス', '/service/')],
                     # 説明は今のサイトの「大手保険会社の代理店として」と取り扱い商材の名前を組み合わせたもの
                     lead='大手保険会社の代理店としての保険をはじめ、<br class="pc">電気・ガス・水道などのライフライン、インターネット回線、<br class="pc">ウォーターサーバーを取り扱っています。',
                     photo='service-lifeline.jpg', pos='55% 50%',
                     extra=f'        <nav class="svc-nav fade" aria-label="取り扱いサービスの一覧">{nav}</nav>') + f'''
  <section class="section">
    <div class="wrap">
{main}
    </div>
  </section>

  <section class="section bg-blue svc-life">
    <div class="wrap">
      <p class="eyebrow fade">Life Service</p>
      <h2 class="fade">暮らしのサービス</h2>
      <p class="text fade" style="margin-top:16px">毎月かかる固定費の見直しにつながる、暮らしのサービスのお手続きやご案内を行います。</p>
      <div class="svc-grid svc-sub-grid">{cards}
      </div>
    </div>
  </section>

''' + final_cta()


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
                            f'          <p class="co-biz">ファイナンシャルプランニング・金融コンサル・<br class="pc">保険代理店業務を行っています。</p>\n'
                            f'        </div>')) + f'''
  <section class="section co-first">
    <div class="wrap">
      <dl class="company-list full">
        <div><dt>会社名</dt><dd>{COMPANY}</dd></div>
        <div><dt>代表者</dt><dd>遠藤 昇平</dd></div>
        <div><dt>所在地</dt><dd>〒{POSTAL}<br>愛知県名古屋市東区葵3丁目14-5<br>リッチコーポ2階</dd></div>
        <!-- ★要確認：2つの番号の用途（代表／お問い合わせ）が今のサイトに書かれていない。確認できたら「代表」などを添える -->
        <div><dt>電話番号</dt><dd><a href="{TEL_HREF}">{TEL}</a></dd></div>
        <div><dt>事業内容</dt><dd>ファイナンシャルプランニング・金融コンサル・保険代理店業務</dd></div>
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
    # お問い合わせはお電話のみ（フォームは置かない、2026-10-05 決定）
    # ★公開前に確認：受付時間は勤務時間（10時～18時）に合わせた仮の値（個人情報の窓口と同じ）
    return page_hero('Contact', 'お問い合わせ', [('お問い合わせ', '/contact/')],
                     lead='お金や保険について、気になることからご相談ください。<br class="pc">ご相談・お問い合わせは、お電話で承っております。',
                     photo='about-hero.jpg', pos='50% 72%') + f'''
  <section class="section">
    <div class="wrap contact-tel">
      <div class="tel-box tel-main">
        <p>保険・お金のご相談、お問い合わせ</p>
        <a href="{TEL_HREF}">{TEL}</a>
        <p class="tel-hours">受付時間 10:00～18:00</p>
      </div>
      <div class="tel-box">
        <p>採用に関するお問い合わせ</p>
        <a href="{RECRUIT_TEL_HREF}">{RECRUIT_TEL}</a>
        <p class="tel-hours"><a class="link-arrow" href="/recruitment/">採用情報を見る{ARROW}</a></p>
      </div>
    </div>
  </section>
'''


def page_recruitment():
    rows = [
        ('職務内容', '生命保険、損害保険などの金融商品の販売とアフターサービス'),
        ('雇用形態', '契約社員<br>※試用期間3カ月　正社員登用制度あり（成績基準あり）'),
        ('応募資格', '学歴・性別・国籍不問'),
        ('勤務地', '愛知県名古屋市東区'),
        ('勤務時間', '10時～18時'),
        ('給与', '成果連動型報酬（営業成績に応じて支給）<br>給与：固定給20万円＋成果報酬<br>年収1,000万円も可能'),
        ('選考方法', '書類面接・面接試験（1～2回）'),
        ('応募方法', 'お電話下さい'),
        ('郵送先・応募先', f'〒{POSTAL} {ADDRESS}'),
    ]
    dl = ''.join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in rows)
    # 「エントリー受付中！」はステータス表示にして、募集要項と電話（応募方法は電話）へつなぐ
    return page_hero('Recruitment', '採用情報', [('採用情報', '/recruitment/')],
                     photo='cta.jpg', pos='30% 50%',
                     extra=(f'        <div class="rc-hero fade">\n'
                            f'          <p class="rc-status"><span class="dot"></span>Entry Open<b>エントリー受付中</b></p>\n'
                            f'          <p class="rc-lead">現在、採用エントリーを受け付けています。<br>ご応募はお電話で承ります。</p>\n'
                            f'          <p class="rc-links"><a class="btn btn-primary" href="#requirements">募集要項を見る{ARROW}</a>'
                            f'<a class="simple-cta-tel" href="tel:0528468224"><svg class="ico"><use href="#i-tel"/></svg>052-846-8224</a></p>\n'
                            f'        </div>')) + f'''
  <section class="section rc-first" id="points">
    <div class="wrap">
      <p class="eyebrow fade">Points</p>
      <h2 class="fade">LFグループで働くポイント</h2>
      <ul class="rc-points">
        <li class="fade"><span class="rc-pt-num">01</span><p class="rc-pt-title">固定給＋成果報酬</p><p>固定給20万円に、営業成績に応じた成果報酬を加えてお支払いします。</p></li>
        <li class="fade"><span class="rc-pt-num">02</span><p class="rc-pt-title">正社員登用制度あり</p><p>契約社員としてスタートし、正社員登用制度があります（成績基準あり）。</p></li>
        <li class="fade"><span class="rc-pt-num">03</span><p class="rc-pt-title">学歴・性別・国籍不問</p><p>応募資格に、学歴・性別・国籍の条件はありません。</p></li>
        <li class="fade"><span class="rc-pt-num">04</span><p class="rc-pt-title">10時～18時勤務</p><p>勤務時間は10時～18時。勤務地は愛知県名古屋市東区です。</p></li>
      </ul>
    </div>
  </section>

  <section class="section bg-blue" id="work">
    <div class="wrap rc-work">
      <div>
        <p class="eyebrow fade">Work</p>
        <h2 class="fade">仕事内容</h2>
      </div>
      <div class="fade">
        <p class="rc-work-lead">生命保険、損害保険などの金融商品の販売とアフターサービス</p>
        <p class="text">LFグループ株式会社は、大手保険会社の代理店として各種保険を取り扱っています。お客様のライフプランに合わせた最適な保険を提案するとともに、生涯を安心して過ごせるように長期的なサポートを行います。</p>
        <p style="margin-top:24px"><a class="link-arrow" href="/business/#insuranceagency">保険代理店事業について見る{ARROW}</a></p>
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
      <h2 class="fade">ご応募はお電話で</h2>
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
TYPO = [('提供し続きます', '提供し続けます'), ('幣社', '弊社')]


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


def write(path, content):
    if path.endswith('.html'):
        page = path.removesuffix('index.html')
        content = image_version(image_attrs(content)).replace('__URL_META__\n', url_meta(page))
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


PAGES = ['', 'about/', 'business/', 'service/', 'insurance/', 'company/', 'contact/', 'recruitment/',
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


def write_motion(top):
    """トップページの動きの試作（/motion/）。お客さまに今のトップと見比べてもらう用で、本番（--release）には出さない。
    中身は今のトップと同じで、src/motion.css・motion.js を足し、写真の枠を「帯の後ろから現れる」用（m-reveal）にする。"""
    css, js = (SRC / 'motion.css').read_text(), (SRC / 'motion.js').read_text()
    v = hashlib.sha1((css + js).encode()).hexdigest()[:8]
    write('assets/motion.css', css)
    write('assets/motion.js', js)
    html_ = (top.replace('</head>', f'<link rel="stylesheet" href="/assets/motion.css?v={v}">\n</head>', 1)
                .replace('</body>', f'<script src="/assets/motion.js?v={v}"></script>\n</body>', 1)
                .replace('リニューアルの試作です', 'リニューアルの試作です・動きの試作版', 1)
                .replace('class="panel-photo"', 'class="panel-photo m-reveal"'))
    html_ = re.sub(r'class="(split-photo|feature-photo|showcase-photo) fade"', r'class="\1 m-reveal"', html_)
    write('motion/index.html', html_)


def season_photos(top, photos=('hero.jpg', 'hero-summer.jpg', 'hero-autumn.jpg', 'hero-winter.jpg')):
    """トップのファーストビューの写真を、春→夏→秋→冬と切り替える（2026-10-05 採用。動きは src/season.css・season.js）。
    photos は春・夏・秋・冬の順。トップは「同じ家族の1年」（春が今の hero.jpg）。
    1枚目は最初から見せ、2枚目以降は最初の画面が出てから読み込むので data-src に置く
    （data-src="/images/…" も relative()・image_version() で相対パスとバージョン番号が付く）"""
    hero = '<img src="/images/hero.jpg" alt="" fetchpriority="high" onerror="this.remove()">'
    assert hero in top, 'ファーストビューの写真の書き方が変わった'
    first = hero.replace('<img ', '<img class="is-show" ').replace('/images/hero.jpg', f'/images/{photos[0]}')
    rest = ''.join(f'\n      <img data-src="/images/{name}" alt="">' for name in photos[1:])
    return top.replace(hero, first + rest, 1)


# 「人生の四季」の試作（/life/）：春＝新婚の二人、夏＝今の hero.jpg（子育て）、秋＝40代の家族、冬＝70代の二人。
# 2026-10-05、季節の写真の別案として作った。お客さまに今のトップ（同じ家族の1年）と見比べてもらう用で、本番には出さない
LIFE_PHOTOS = ('life-spring.jpg', 'hero.jpg', 'life-autumn.jpg', 'life-winter.jpg')


# /season/ は試作のときのURL。お客さまに伝えている場合があるので、トップへ移す
SEASON_REDIRECT = """<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url=../"><title>LFグループ株式会社</title></head>
<body><p><a href="/">トップページへ</a></p></body></html>
"""


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
    top = season_photos(top_base)
    write('index.html', top)
    if not RELEASE:
        write_motion(top)
        write('season/index.html', SEASON_REDIRECT)
        write('life/index.html', season_photos(top_base, LIFE_PHOTOS)
              .replace('リニューアルの試作です', 'リニューアルの試作です・人生の四季の写真の試作版', 1))
    write('about/index.html', layout('私たちについて', page_about(), 'about'))
    write('business/index.html', layout('事業内容', page_business(), 'business'))
    write('service/index.html', layout('取り扱いサービス', page_service(), 'service'))
    write('insurance/index.html', layout('保険', page_insurance(), 'service'))
    write('company/index.html', layout('会社概要', page_company(), 'company'))
    write('contact/index.html', layout('お問い合わせ', page_contact(), 'contact'))
    write('recruitment/index.html', layout('採用情報', page_recruitment(), 'recruitment'))
    renders = {'operation': policy_operation, 'solicitation': policy_solicitation,
               'privacyprotection': policy_privacy, 'informationsecurity': policy_security}
    for key, label, _ in POLICIES:
        write(f'{key}/index.html', layout(label, page_policy(key, label, renders[key])))
    if RELEASE:
        write('404.html', layout('ページが見つかりません', page_404()).replace('<meta name="description"', '<meta name="robots" content="noindex">\n<meta name="description"', 1))


if __name__ == '__main__':
    main()
