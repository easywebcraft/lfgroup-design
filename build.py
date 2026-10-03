#!/usr/bin/env python3
"""LFグループ株式会社 サイト試作のページを書き出す。

  python3 build.py  →  リポジトリの直下に各ページの index.html と assets/ を作る（GitHub Pages でそのまま配信）

共通部分（head・ヘッダー・メニュー・フッター）はここで一度だけ定義し、各ページの中身と組み合わせる。
文言は今のサイト（text/ に保存した本文）にあるものだけを使う。足していない。
"""
import hashlib
import html
import re
from pathlib import Path

BASE = Path(__file__).parent
SRC = BASE / 'src'
SITE = BASE  # GitHub Pages はリポジトリ直下を配信する（かみのてと同じ）
TEXT = BASE / 'text'

TEL = '052-990-6159'
TEL_HREF = 'tel:0529906159'
ADDRESS = '愛知県名古屋市東区葵3丁目14-5 リッチコーポ2階'
COMPANY = 'LFグループ株式会社'

# メインメニュー（ヘッダー・ドロワー・フッターで共通）
NAV = [
    ('about', '私たちについて', '/about/'),
    ('business', '事業内容', '/business/'),
    ('service', '取り扱いサービス', '/service/'),
    ('company', '会社概要', '/company/'),
    ('news', 'お知らせ', '/news/'),
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
TOP = (SRC / 'top.html').read_text()
ICONS = re.findall(r'(<svg class="card-icon".*?</svg>)', TOP, re.S)  # 事業4つのアイコン（トップのカードと同じもの）


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


def layout(page_title, body, current='', description='顧客満足度を最優先に人々の生活を向上させます。'):
    title = COMPANY if not page_title else f'{page_title}｜{COMPANY}'
    return f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{html.escape(description)}">
<meta name="robots" content="noindex,nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600&family=Noto+Sans+JP:wght@400;500;700&family=Noto+Serif+JP:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css?v={ASSET_V}">
</head>
<body>
{SPRITE}
<!-- ★公開前に必ず外す：試作であることを示す帯 -->
<div class="draft-bar">LFグループ株式会社さま ホームページ リニューアルの試作です（EasyWebCraft）</div>

<header class="header" id="header">
  <div class="wrap header-inner">
    <a class="logo" href="/" aria-label="{COMPANY} トップ">
      <span class="logo-mark" aria-hidden="true">LF</span>{COMPANY}
    </a>
    <nav class="gnav" aria-label="メインメニュー">
      <ul>
        {nav_items(current)}
      </ul>
    </nav>
    <a class="btn btn-primary" href="/contact/">お問い合わせ{ARROW}</a>
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
  <a class="btn btn-primary" href="/contact/">お問い合わせ{ARROW}</a>
  <a class="tel" href="{TEL_HREF}"><small>お電話でのお問い合わせ</small>{TEL}</a>
</div>

<main>
{body}
</main>

<footer class="footer">
  <div class="wrap">
    <div class="footer-top">
      <div class="footer-info">
        <a class="logo" href="/"><span class="logo-mark" aria-hidden="true">LF</span>{COMPANY}</a>
        <p>〒（要確認）{ADDRESS}</p>
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
  <a class="c" href="/contact/">お問い合わせ</a>
  <a class="t" href="{TEL_HREF}"><svg><use href="#i-tel"/></svg>電話する</a>
</div>

<script src="/assets/main.js?v={ASSET_V}"></script>
</body>
</html>
'''


SPRITE = (SRC / 'sprite.svg').read_text()


def page_hero(label, title, crumbs, lead=''):
    """下層ページの見出し。crumbs は (名前, URL) の並び。最後が今のページ。"""
    items = ['<li><a href="/">トップ</a></li>']
    for name, href in crumbs[:-1]:
        items.append(f'<li><a href="{href}">{name}</a></li>')
    items.append(f'<li aria-current="page">{crumbs[-1][0]}</li>')
    lead_html = f'\n      <p class="lead fade">{lead}</p>' if lead else ''
    return f'''  <section class="page-hero">
    <div class="wrap">
      <ol class="crumb fade" aria-label="パンくずリスト">{''.join(items)}</ol>
      <p class="label fade">{label}</p>
      <h1 class="fade">{title}</h1>{lead_html}
    </div>
  </section>
'''


def final_cta():
    return f'''  <section class="cta" id="final-cta">
    <div class="photo"><img src="/images/cta-final.jpg" alt="" onerror="this.remove()"></div>
    <div class="wrap">
      <h2 class="cta-title fade"><span>サービスに関するお問い合わせ、</span><br><span>資料のご請求はこちら</span></h2>
      <div class="btns fade">
        <a class="btn btn-primary" href="/contact/">お問い合わせ{ARROW}</a>
        <a class="btn btn-white" href="/contact/?type=document">資料請求{ARROW}</a>
      </div>
      <p class="cta-tel fade">お電話でのお問い合わせ<a href="{TEL_HREF}">{TEL}</a></p>
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
    items = ''.join(
        f'<li class="fade"><p class="pl-num">{i + 1:02d}</p><p class="pl-text">{"".join(f"<span>{x}</span>" for x in parts)}</p></li>'
        for i, parts in enumerate(fd))
    hero = page_hero('About', '私たちについて', [('私たちについて', '/about/')])
    hero = hero.replace('<section class="page-hero">', '<section class="page-hero about-hero">')
    # 左に見出しとメッセージ、右に縦長の写真を1枚（相談スペース。人物なし）
    hero = hero.replace('    <div class="wrap">\n', '    <div class="wrap about-hero-grid">\n      <div>\n', 1)
    hero = hero.replace('      <h1 class="fade">私たちについて</h1>\n',
                        '      <h1 class="fade">私たちについて</h1>\n'
                        # 説明文と3つの価値観は、お客様本位の業務運営方針と保険代理店事業の文言から取る（新しい言葉は足さない）
                        '      <p class="about-lead fade">「保険・固定費削減のプロフェッショナルとして、<br class="pc">お客様の立場になって、誠実・公正に業務を行います。」</p>\n'
                        '      <p class="about-message fade"><span>顧客満足度を最優先に、</span><br><span>人々の生活を向上させます。</span></p>\n'
                        '      <ul class="about-values fade"><li><b>01</b>誠実・公正</li><li><b>02</b>わかりやすい説明</li><li><b>03</b>長期的なサポート</li></ul>\n'
                        '      </div>\n'
                        '      <div class="about-hero-visual fade"><div class="about-hero-photo photo"><span class="ph">IMAGE：相談スペース</span>'
                        '<img src="/images/about-hero.jpg" alt="" onerror="this.remove()"></div></div>\n')
    hero = hero.replace('<section class="page-hero about-hero">', '<section class="page-hero about-hero">\n    <p class="about-bg-word" aria-hidden="true">About Us</p>')
    return hero + f'''
  <section class="section about-intro">
    <div class="wrap">
      <div class="about-intro-body fade">
        <p class="label">Introduction</p>
        <p class="about-intro-text">弊社はお客様の固定費を削減することを目的に、電気やガスなどのライフラインの代行業務、保険の見直しに加え、FP資格取得者が多数在籍しており、NISAやふるさと納税をはじめとした投資や節税などを通して、お客様のライフプランの見直しを行っています。</p>
      </div>
    </div>
  </section>

  <section class="section about-mission" id="mission">
    <div class="wrap">
      <p class="label fade">Mission</p>
      <h2 class="about-mission-msg fade"><span>固定費削減で、</span><br><span>家計を見直す。</span></h2>
      <div class="about-mission-text fade">
        <p>固定費は、見直し削減することで<br>半永久的な節約につながります。</p>
        <p>LFグループ株式会社では、<br>ゆとりある生活の実現のために<br>お役立ちをさせていただきます。</p>
      </div>
      <p class="about-mission-quote fade"><span>金銭的な余裕は、</span><br><span>人生の幸福度を高めます。</span></p>
    </div>
  </section>

  <section class="section about-policy">
    <div class="wrap">
      <div class="about-policy-grid">
        <div class="about-policy-head">
          <p class="label fade">Policy</p>
          <h2 class="heading fade">お客様本位の<br>業務運営方針</h2>
          <p class="fade" style="margin-top:32px"><a class="more" href="/operation/">主な取組内容を見る{ARROW}</a></p>
        </div>
        <ol class="policy-lines">{items}</ol>
      </div>
    </div>
  </section>

''' + final_cta()


BUSINESS = [
    ('financialplanning', 'ファイナンシャルプランニング事業', 'Financial Planning', [
        'LFグループ株式会社では、ファイナンシャルプランニング技能士（国家資格）を保有するスタッフが多数在籍しています。',
        'お金の専門家であるFPがライフプラン・家計・保険・年金・住宅資金・教育資金・税金・資産運用・介護・医療費・相続・贈与などのお悩みに対して、適切なアドバイスを行い、お客様の人生がより良くなるようサポートさせて頂きます。',
    ], ''),
    ('alliance', 'アライアンス事業', 'Alliance', [
        '私たちLFグループ株式会社は、マンションやアパートのご入居者様へガスや電気などのライフライン、インターネット回線、ウォーターサーバーなどのお手続きやご案内を行います。',
        '経験豊富なオペレーターによる丁寧なご案内に加え、選りすぐりの商材を取り揃えており、提携いただく企業様とエンドユーザー様に安心確実なサポートをご提供いたします。',
    ], ''),
    ('insuranceagency', '保険代理店事業', 'Insurance Agency', [
        'LFグループ株式会社では、大手保険会社の代理店として各種保険を取り扱っています。',
        '自動車・バイク・病気・ケガ・旅行・趣味・こども・生命保険等、お客様のライフプランに合わせた最適な保険を提案するとともに、生涯を安心して過ごせるように長期的なサポートを行います。',
    ], ''),
    ('partner', 'パートナー事業', 'Partner', [
        'LFグループ株式会社では、当社が取り扱っている商材やサービスを提携企業様、パートナー様と協力してお客様にご提供しています。',
        'アライアンス事業で培ったノウハウを活かして、お客様に本当に必要なものを丁寧にご提案するとともに、厳格なチェック体制と管理の下でミスなくきめ細やかな対応を行うことができます。',
        '提携企業様・パートナー様の事業繁栄をお手伝いし、相互の長期的な利益追求・価値創造を目指します。',
    ], '提携企業様・パートナー様募集中'),
]


def page_business():
    index = ''.join(f'<a href="#{k}">{n}</a>' for k, n, *_ in BUSINESS)
    blocks = []
    for i, (key, name, en, paras, note) in enumerate(BUSINESS):
        texts = ''.join(f'<p class="text">{p}</p>' for p in paras)
        note_html = f'<p class="biz-note">{note}</p>' if note else ''
        if key == 'insuranceagency':
            note_html = f'<p style="margin-top:24px"><a class="more" href="/insurance/">取り扱い保険・事故対応について見る{ARROW}</a></p>'
        blocks.append(f'''      <article class="biz-block fade" id="{key}">
        <div class="biz-visual"><span class="num">{i + 1:02d}</span>{ICONS[i]}</div>
        <div>
          <h2>{name.replace('ファイナンシャルプランニング', '<span>ファイナンシャル</span><span>プランニング</span>')}</h2>
          <span class="card-en">{en}</span>
          {'<p class="badge"><span>国家資格</span>FP技能士在籍</p>' if key == 'financialplanning' else ''}
          <div style="margin-top:28px">{texts}</div>
          {note_html}
        </div>
      </article>''')
    hero = page_hero('Business', '事業内容', [('事業内容', '/business/')])
    hero = hero.replace('    </div>\n  </section>', f'      <nav class="biz-index fade" aria-label="事業の一覧">{index}</nav>\n    </div>\n  </section>', 1)
    return hero + f'''
  <section class="section">
    <div class="wrap">
{chr(10).join(blocks)}
    </div>
  </section>

''' + final_cta()


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
                     '大手保険会社の代理店として、各種保険を取り扱っています。') + f'''
  <section class="section">
    <div class="wrap ins-intro">
      <div>
        <p class="label fade">Insurance Agency</p>
        <h2 class="heading fade">保険代理店事業</h2>
        <p class="text fade" style="margin-top:28px">LFグループ株式会社では、大手保険会社の代理店として各種保険を取り扱っています。</p>
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

  <section class="section bg-blue">
    <div class="wrap">
      <p class="label fade">Lineup</p>
      <h2 class="heading fade">取り扱い保険</h2>
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
        <p class="label fade">Support</p>
        <h2 class="heading fade">事故対応</h2>
      </div>
      <div class="fade">
        <p class="ins-lead">事故に遭われたお客様に対して、迅速に保険金のお支払いができるようアドバイスし、事故処理完了まで適切な対応を行います。</p>
        <ul class="ins-checks">
          <li>事故に遭われたお客様への連絡頻度を高めています。</li>
          <li>休日・夜間の事故対応。</li>
        </ul>
        <p style="margin-top:24px"><a class="more" href="/operation/">お客様本位の業務運営方針を見る{ARROW}</a></p>
      </div>
    </div>
  </section>

  <section class="section bg-blue">
    <div class="wrap narrow">
      <p class="label fade">Policy</p>
      <h2 class="heading fade">勧誘方針</h2>
      <ol class="fd-list" style="margin-top:40px">
        {''.join(f'<li class="fade">{t}</li>' for t in sol)}
      </ol>
      <p style="margin-top:32px" class="fade"><a class="more" href="/solicitation/">勧誘方針の全文を見る{ARROW}</a></p>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <a class="ins-related fade" href="/business/#financialplanning">
        <div>
          <p class="label">Related</p>
          <p class="ins-related-title"><span>ファイナンシャル</span><span>プランニング事業</span></p>
          <p class="badge"><span>国家資格</span>FP技能士在籍</p>
          <p class="text" style="margin-top:16px">お金の専門家であるFPがライフプラン・家計・保険・年金・住宅資金・教育資金・税金・資産運用・介護・医療費・相続・贈与などのお悩みに対して、適切なアドバイスを行い、お客様の人生がより良くなるようサポートさせて頂きます。</p>
        </div>
        <span class="more">詳しく見る{ARROW}</span>
      </a>
    </div>
  </section>

''' + simple_cta()


def page_service():
    rows = [
        ('保険', 'Insurance', 'service-insurance.jpg', 'IMAGE：家族の安心', f'''
          <div class="svc-group"><h3>主力会社</h3><p>SOMPOひまわり生命・日新火災海上保険</p></div>
          <div class="svc-group"><h3>生命保険</h3>{tags(['医療保険', 'がん保険', '終身保険', '変額保険', '収入保障保険', '定期保険', 'こども保険', '学資保険', 'ほか'])}</div>
          <div class="svc-group"><h3>損害保険</h3>{tags(['自動車保険', '火災保険', '損害保険', '賠償責任保険', '労災保険', 'ほか'])}</div>
          <p class="svc-group"><a class="more" href="/insurance/">保険について詳しく見る{ARROW}</a></p>'''),
        ('ライフライン', 'Lifeline', 'service-lifeline.jpg', 'IMAGE：暮らしのあかり',
         f'<div class="svc-group">{tags(["電気", "ガス", "水道"])}</div>'),
        ('インターネット', 'Internet', 'service-internet.jpg', 'IMAGE：住まいとネット',
         f'<div class="svc-group">{tags(["フレッツ光", "光コラボレーション", "ダークファイバー系光回線", "電力系光回線"])}</div>'),
        ('ウォーターサーバー', 'Water Server', 'service-water.jpg', 'IMAGE：水・キッチン',
         f'<div class="svc-group">{tags(["浄水器型ウォーターサーバー"])}</div>'),
    ]
    out = []
    for name, en, img, ph, inner in rows:
        out.append(f'''      <article class="svc-row fade">
        <div class="photo"><span class="ph">{ph}</span><img src="/images/{img}" alt="" onerror="this.remove()"></div>
        <div>
          <h2>{name}</h2>
          <p class="label">{en}</p>{inner}
        </div>
      </article>''')
    return page_hero('Service', '取り扱いサービス', [('取り扱いサービス', '/service/')]) + f'''
  <section class="section">
    <div class="wrap">
{chr(10).join(out)}
    </div>
  </section>

''' + final_cta()


def page_company():
    # 「愛知県名古屋市東区葵3丁目14-5」を Google マップの埋め込み形式にしたもの
    q = 'https://www.google.com/maps/embed?origin=mfe&amp;pb=!1m3!2m1!1z5oSb55-l55yM5ZCN5Y-k5bGL5biC5p2x5Yy66JG1M-S4geebrjE0LTU!6i16'
    links = ''.join(f'<a href="{h}">{l}{ARROW}</a>' for _, l, h in POLICIES)
    return page_hero('Company', '会社概要', [('会社概要', '/company/')]) + f'''
  <section class="section">
    <div class="wrap">
      <dl class="company-list full fade">
        <div><dt>会社名</dt><dd>{COMPANY}</dd></div>
        <div><dt>代表者</dt><dd>遠藤 昇平</dd></div>
        <div><dt>所在地</dt><dd>愛知県名古屋市東区葵3丁目14-5<br>リッチコーポ2階</dd></div>
        <div><dt>電話番号</dt><dd><a href="tel:0528462135">052-846-2135</a> / <a href="{TEL_HREF}">{TEL}</a></dd></div>
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
      <p class="label fade">Policy</p>
      <h2 class="heading fade">各種方針</h2>
      <div class="link-list fade" style="margin-top:40px">{links}</div>
    </div>
  </section>

''' + final_cta()


NEWS = [
    ('20230920', '2023-09-20', 'NEWS', 'ホームページを公開しました！！', [
        'こんにちは！',
        'ＬＦグループ株式会社です。弊社はお客様の固定費を削減することを目的に、電気やガスなどのライフラインの代行業務、保険の見直しに加え、ＦＰ資格取得者が多数在籍しており、ＮＩＳＡやふるさと納税をはじめとした投資や節税などを通して、お客様のライフプランの見直しを行っています。',
        '皆さんのお力になれるよう頑張りますので、これからよろしくお願い致します。',
    ]),
]


def news_row(slug, d, cat, t):
    return (f'<li><a href="/news/{slug}/"><time datetime="{d}">{d.replace("-", ".")}</time>'
            f'<span class="news-cat">{cat}</span><span class="news-title">{t.rstrip("！")}</span>{ARROW}</a></li>')


def simple_cta():
    """写真を使わない、下層ページ用のお問い合わせ欄。"""
    return f'''  <section class="section simple-cta-wrap">
    <div class="wrap">
      <div class="simple-cta fade">
        <p class="simple-cta-title"><span>サービスに関するお問い合わせ、</span><span>資料のご請求はこちら</span></p>
        <div class="btns">
          <a class="btn btn-primary" href="/contact/">お問い合わせ{ARROW}</a>
          <a class="btn btn-white" href="/contact/?type=document">資料請求{ARROW}</a>
          <a class="btn btn-white btn-tel" href="{TEL_HREF}"><svg class="ico"><use href="#i-tel"/></svg>{TEL}</a>
        </div>
      </div>
    </div>
  </section>
'''


def page_news_list():
    items = ''.join(news_row(slug, d, cat, t) for slug, d, cat, t, _ in NEWS)
    return page_hero('News', 'お知らせ', [('お知らせ', '/news/')]).replace('<section class="page-hero">', '<section class="page-hero compact">') + f'''
  <section class="section news-page">
    <div class="wrap narrow">
      <ul class="news-lines fade">{items}</ul>
    </div>
  </section>

''' + simple_cta()


def page_news_article(slug, date, cat, title, paras):
    body = ''.join(f'<p>{p}</p>' for p in paras)
    return page_hero('News', 'お知らせ', [('お知らせ', '/news/'), (title.rstrip('！'), f'/news/{slug}/')]).replace('<h1 class="fade">お知らせ</h1>', '<p class="heading fade">お知らせ</p>').replace('<section class="page-hero">', '<section class="page-hero compact">') + f'''
  <section class="section">
    <div class="wrap narrow">
      <article>
        <header class="article-head fade">
          <p class="article-meta"><time datetime="{date}">{date.replace("-", ".")}</time><span class="news-cat">{cat}</span></p>
          <h1>{title}</h1>
        </header>
        <div class="article-body fade">{body}</div>
      </article>
      <p class="back"><a class="more" href="/news/">お知らせ一覧へ戻る{ARROW}</a></p>
    </div>
  </section>

''' + simple_cta()


def page_contact():
    return page_hero('Contact', 'お問い合わせ', [('お問い合わせ', '/contact/')]) + f'''
  <section class="section">
    <div class="wrap contact-grid">
      <div class="fade">
        <p class="text">弊社へのお問い合わせは、こちらのフォームより承っております。</p>
        <p class="text">ご返信に3営業日ほどお時間をいただいております。3営業日を過ぎても返信がない場合は、お手数ですが再度お問い合わせをお願いいたします。</p>
        <div class="tel-box">
          <p>お電話でのお問い合わせ</p>
          <a href="{TEL_HREF}">{TEL}</a>
        </div>
      </div>

      <div class="fade">
        <!-- 試作：送信先（メール送信・フォームサービス）は公開前に設定する。今は入力チェックだけで送信しない -->
        <form class="form" id="contactForm" novalidate>
          <fieldset class="field">
            <legend>お問い合わせ種別</legend>
            <div class="radios">
              <label><input type="radio" name="type" value="お問い合わせ" checked>お問い合わせ</label>
              <label><input type="radio" name="type" value="資料請求">資料請求</label>
            </div>
          </fieldset>
          <div class="field">
            <label for="f-name">お名前<span class="req">必須</span></label>
            <input type="text" id="f-name" name="name" autocomplete="name" required>
          </div>
          <div class="field">
            <label for="f-tel">電話番号<span class="req">必須</span></label>
            <input type="tel" id="f-tel" name="tel" autocomplete="tel" inputmode="tel" required>
          </div>
          <div class="field">
            <label for="f-email">メールアドレス<span class="req">必須</span></label>
            <input type="email" id="f-email" name="email" autocomplete="email" required>
          </div>
          <div class="field">
            <label for="f-body">お問い合わせ内容<span class="req">必須</span></label>
            <textarea id="f-body" name="body" required></textarea>
          </div>
          <div class="field">
            <label class="agree"><input type="checkbox" name="agree" required><span><a href="/privacyprotection/" target="_blank" rel="noopener">プライバシーポリシー</a>に同意して送信する</span></label>
          </div>
          <button class="btn btn-primary" type="submit">この内容で送信する{ARROW}</button>
        </form>
        <div class="form-done" id="formDone" tabindex="-1" hidden>
          <h2>（試作）入力内容を確認しました</h2>
          <p>この試作ページでは送信されません。公開前に送信の仕組みを設定します。</p>
        </div>
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
        ('郵送先・応募先', f'{ADDRESS}'),
    ]
    dl = ''.join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in rows)
    return page_hero('Recruitment', '採用情報', [('採用情報', '/recruitment/')], 'エントリー受付中！') + f'''
  <section class="section">
    <div class="wrap">
      <dl class="company-list full fade">{dl}</dl>
    </div>
  </section>

  <section class="section bg-blue">
    <div class="wrap narrow">
      <p class="label fade">Entry</p>
      <h2 class="heading fade">ご応募はお電話で</h2>
      <div class="recruit-tel fade">
        <a href="tel:0528468224">052-846-8224</a>
        <a href="{TEL_HREF}">{TEL}</a>
      </div>
    </div>
  </section>
'''


# ───────────── 方針ページ：保存した本文を見出し・箇条書きに組み直す ─────────────

NAV_NOISE = {'HOME', 'COMPANY', 'SERVICE', 'NEWS', 'CONTACT', 'RECURUITMENT', 'RECRUITMENT', 'ＬＦグループ株式会社',
             TEL, 'お問い合わせはこちらから', 'エントリー受付中！', '採用情報はこちらから'}

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
    out.append('<ol class="num">' + ''.join(f'<li>{esc(l)}</li>' for l in nums) + '</ol>')
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
    return render_policy(lines, heading_rule=lambda l: not l.startswith('・'))


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
    # 本文が「下記のお問い合わせ窓口」と書いているが、今のサイトには窓口の記載がない
    body += '<p class="todo">【要確認】本文中の「下記のお問い合わせ窓口」が今のサイトに載っていません。窓口（部署・電話番号・受付時間など）をクライアントに確認して追記してください。</p>'
    return body


def policy_security():
    lines = policy_lines('informationsecurity', '情報セキュリティ基本方針')
    return render_policy(lines, heading_rule=lambda l: bool(re.match(r'^（[０-９]+）', l)))


def page_policy(key, label, render):
    return page_hero('Policy', label, [(label, f'/{key}/')]) + f'''
  <section class="section">
    <div class="wrap narrow policy fade">
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


def write(path, content):
    if path.endswith('.html'):
        content = relative(path, image_version(content))
    p = SITE / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    print('  ', path)


def main():
    global ASSET_V
    css = (SRC / 'style.css').read_text() + (SRC / 'pages.css').read_text() + (SRC / 'brand.css').read_text()
    css += """
  /* ★公開前に必ず外す：試作の帯 */
  .draft-bar { position: relative; z-index: 60; padding: 6px var(--gutter); line-height: 18px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; background: #22303C; color: #fff; font-size: 12px; text-align: center; letter-spacing: .04em; }
  .draft-bar ~ .header:not(.is-scrolled) { top: 30px; }
  .draft-bar ~ .drawer { padding-top: calc(var(--header-h) + 54px); }
"""
    js = (SRC / 'main.js').read_text()
    # CSS・JS の中身が変わったら URL も変える。GitHub Pages は10分間ブラウザに覚えさせるため、
    # 変えないと「新しいページ＋古いデザイン」が組み合わさって表示が崩れる（MISSION の写真が消えた）
    ASSET_V = hashlib.sha1((css + js).encode()).hexdigest()[:8]
    write('assets/style.css', css)
    write('assets/main.js', js)

    write('index.html', layout('', TOP))
    write('about/index.html', layout('私たちについて', page_about(), 'about'))
    write('business/index.html', layout('事業内容', page_business(), 'business'))
    write('service/index.html', layout('取り扱いサービス', page_service(), 'service'))
    write('insurance/index.html', layout('保険', page_insurance(), 'service'))
    write('company/index.html', layout('会社概要', page_company(), 'company'))
    write('news/index.html', layout('お知らせ', page_news_list(), 'news'))
    for slug, d, cat, t, paras in NEWS:
        write(f'news/{slug}/index.html', layout(t.rstrip('！'), page_news_article(slug, d, cat, t, paras), 'news'))
    write('contact/index.html', layout('お問い合わせ', page_contact(), 'contact'))
    write('recruitment/index.html', layout('採用情報', page_recruitment(), 'recruitment'))
    renders = {'operation': policy_operation, 'solicitation': policy_solicitation,
               'privacyprotection': policy_privacy, 'informationsecurity': policy_security}
    for key, label, _ in POLICIES:
        write(f'{key}/index.html', layout(label, page_policy(key, label, renders[key])))


if __name__ == '__main__':
    main()
