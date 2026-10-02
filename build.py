#!/usr/bin/env python3
"""LFグループ株式会社 サイト試作のページを書き出す。

  python3 build.py  →  site/ 以下に各ページの index.html と assets/ を作る

共通部分（head・ヘッダー・メニュー・フッター）はここで一度だけ定義し、各ページの中身と組み合わせる。
文言は今のサイト（text/ に保存した本文）にあるものだけを使う。足していない。
"""
import html
import re
from pathlib import Path

BASE = Path(__file__).parent
SRC = BASE / 'src'
SITE = BASE / 'site'
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
]
POLICIES = [
    ('operation', 'お客様本位の業務運営方針', '/operation/'),
    ('solicitation', '勧誘方針', '/solicitation/'),
    ('privacyprotection', '個人情報保護方針', '/privacyprotection/'),
    ('informationsecurity', '情報セキュリティ基本方針', '/informationsecurity/'),
]

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
    recruit_cur = ' aria-current="page"' if current == 'recruitment' else ''
    return f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600&family=Noto+Sans+JP:wght@400;500;700&family=Noto+Serif+JP:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css">
</head>
<body>
{SPRITE}

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
      <li><a href="/recruitment/"{recruit_cur}>採用情報{ARROW}</a></li>
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
          <li><a href="/recruitment/">採用情報</a></li>
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

<script src="/assets/main.js"></script>
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
    fd = [
        '保険・固定費削減のプロフェッショナルとして、お客様の立場になって、誠実・公正に業務を行います。',
        'お客様のニーズを把握し、お客様にふさわしい商品とサービスを提供し続けます。',
        'お客様が納得してご契約できるよう、商品とサービスの説明を丁寧かつわかりやすく行います。',
        '事故に遭われたお客様に対して、迅速に保険金の支払いができるようアドバイスし、事故処理完了まで適切な対応を行います。',
        'お客様の立場で行動するために、継続的に教育を行うとともに、適切な管理体制を整備します。',
    ]
    return page_hero('About', '私たちについて', [('私たちについて', '/about/')]) + f'''
  <section class="section">
    <div class="wrap narrow">
      <p class="about-message fade"><span>顧客満足度を最優先に</span><br><span>人々の生活を向上させます</span></p>
      <p class="text fade" style="margin-top:40px">弊社はお客様の固定費を削減することを目的に、電気やガスなどのライフラインの代行業務、保険の見直しに加え、FP資格取得者が多数在籍しており、NISAやふるさと納税をはじめとした投資や節税などを通して、お客様のライフプランの見直しを行っています。</p>
    </div>
  </section>

  <section class="section bg-blue" id="mission">
    <div class="wrap mission-grid">
      <div>
        <p class="label fade">Mission</p>
        <h2 class="mission-msg fade">固定費削減で、<br>家計を見直す。</h2>
        <p class="mission-text fade">固定費は、見直し削減することで半永久的に節約することができます。<br>LFグループ株式会社では、ゆとりある生活の実現のためにお役立ちをさせていただきます。</p>
      </div>
      <div class="mission-photos fade">
        <div class="photo p2"><span class="ph">IMAGE：明るいリビング</span><img src="/images/mission-2.jpg" alt="" onerror="this.remove()"></div>
        <div class="photo p1"><span class="ph">IMAGE：空・海</span><img src="/images/mission-1.jpg" alt="" onerror="this.remove()"></div>
      </div>
    </div>
  </section>

  <section class="section about-statement">
    <div class="wrap">
      <p class="fade"><span>金銭的な余裕は、</span><span>人生の幸福度を高めます。</span></p>
    </div>
  </section>

  <section class="section bg-blue">
    <div class="wrap narrow">
      <p class="label fade">Policy</p>
      <h2 class="heading fade">お客様本位の業務運営方針</h2>
      <ol class="fd-list" style="margin-top:40px">
        {''.join(f'<li class="fade">{t}</li>' for t in fd)}
      </ol>
      <p style="margin-top:32px" class="fade"><a class="more" href="/operation/">主な取組内容を見る{ARROW}</a></p>
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
        blocks.append(f'''      <article class="biz-block fade" id="{key}">
        <div class="biz-visual"><span class="num">{i + 1:02d}</span>{ICONS[i]}</div>
        <div>
          <h2>{name.replace('ファイナンシャルプランニング', '<span>ファイナンシャル</span><span>プランニング</span>')}</h2>
          <span class="card-en">{en}</span>
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


def page_service():
    rows = [
        ('保険', 'Insurance', 'service-insurance.jpg', 'IMAGE：家族の安心', f'''
          <div class="svc-group"><h3>主力会社</h3><p>SOMPOひまわり生命・日新火災海上保険</p></div>
          <div class="svc-group"><h3>生命保険</h3>{tags(['医療保険', 'がん保険', '終身保険', '変額保険', '収入保障保険', '定期保険', 'こども保険', '学資保険', 'ほか'])}</div>
          <div class="svc-group"><h3>損害保険</h3>{tags(['自動車保険', '火災保険', '損害保険', '賠償責任保険', '労災保険', 'ほか'])}</div>'''),
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
    ('20230920', '2023-09-20', 'ホームページを公開しました！！', [
        'こんにちは！',
        'ＬＦグループ株式会社です。弊社はお客様の固定費を削減することを目的に、電気やガスなどのライフラインの代行業務、保険の見直しに加え、ＦＰ資格取得者が多数在籍しており、ＮＩＳＡやふるさと納税をはじめとした投資や節税などを通して、お客様のライフプランの見直しを行っています。',
        '皆さんのお力になれるよう頑張りますので、これからよろしくお願い致します。',
    ]),
]


def page_news_list():
    items = ''.join(
        f'<li><a href="/news/{slug}/"><time datetime="{d}">{d.replace("-", ".")}</time>'
        f'<span>{t.rstrip("！")}</span>{ARROW}</a></li>' for slug, d, t, _ in NEWS)
    return page_hero('News', 'お知らせ', [('お知らせ', '/news/')]) + f'''
  <section class="section">
    <div class="wrap narrow">
      <ul class="news-list fade">{items}</ul>
    </div>
  </section>
'''


def page_news_article(slug, date, title, paras):
    body = ''.join(f'<p>{p}</p>' for p in paras)
    return page_hero('News', 'お知らせ', [('お知らせ', '/news/'), (title.rstrip('！'), f'/news/{slug}/')]).replace('<h1 class="fade">お知らせ</h1>', '<p class="heading fade">お知らせ</p>') + f'''
  <section class="section">
    <div class="wrap narrow">
      <article>
        <header class="article-head fade">
          <time datetime="{date}">{date.replace("-", ".")}</time>
          <h1>{title}</h1>
        </header>
        <div class="article-body fade">{body}</div>
      </article>
      <p class="back"><a class="more" href="/news/">お知らせ一覧へ戻る{ARROW}</a></p>
    </div>
  </section>
'''


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

def write(path, content):
    p = SITE / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    print('  ', path)


def main():
    css = (SRC / 'style.css').read_text() + (SRC / 'pages.css').read_text()
    write('assets/style.css', css)
    write('assets/main.js', (SRC / 'main.js').read_text())

    write('index.html', layout('', TOP))
    write('about/index.html', layout('私たちについて', page_about(), 'about'))
    write('business/index.html', layout('事業内容', page_business(), 'business'))
    write('service/index.html', layout('取り扱いサービス', page_service(), 'service'))
    write('company/index.html', layout('会社概要', page_company(), 'company'))
    write('news/index.html', layout('お知らせ', page_news_list(), 'news'))
    for slug, d, t, paras in NEWS:
        write(f'news/{slug}/index.html', layout(t.rstrip('！'), page_news_article(slug, d, t, paras), 'news'))
    write('contact/index.html', layout('お問い合わせ', page_contact(), 'contact'))
    write('recruitment/index.html', layout('採用情報', page_recruitment(), 'recruitment'))
    renders = {'operation': policy_operation, 'solicitation': policy_solicitation,
               'privacyprotection': policy_privacy, 'informationsecurity': policy_security}
    for key, label, _ in POLICIES:
        write(f'{key}/index.html', layout(label, page_policy(key, label, renders[key])))


if __name__ == '__main__':
    main()
