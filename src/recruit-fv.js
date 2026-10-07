/* 採用情報のFVの試作（/recruitment-a/・-b/・-c/。2026-10-06）。見た目は recruit-fv.css */
(function () {
  var root = document.documentElement;
  var sec = document.querySelector('.rf');
  if (!sec) return;
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  root.classList.add('rf-go');
  var all = function (sel, el) { return Array.prototype.slice.call((el || document).querySelectorAll(sel)); };

  // 複数の写真（または文字）を順に切り替える。前のものは .is-prev にして、上に次のものを重ねる
  var step = function (items, i) {
    items.forEach(function (el) { el.classList.remove('is-prev'); });
    var cur = items.filter(function (el) { return el.classList.contains('is-on'); })[0];
    if (cur) { cur.classList.remove('is-on'); cur.classList.add('is-prev'); }
    void items[i].offsetWidth;  // 閉じた状態を反映させてから開く
    items[i].classList.add('is-on');
  };

  // トップ（/top-a2-full/）では、ページを開いたときのロゴの演出（main.js）が終わるまで待ってから動かす
  // /top-a2/ 系は、演出の終わり（白い幕が消えきる）まで待たず、キャッチコピーが見出しへ着いた瞬間（幕が透け始めて約0.9秒）から始める。
  // メニュー（s-head）・小見出し・説明文・ボタン・英字を、そこから約1秒の間にテンポよく出す（2026-10-07）
  var absorbAt = 0;
  var begin = function () {
  if (root.classList.contains('is-loading')) {
    var L = document.getElementById('lfLoader');
    if (sec.classList.contains('rf-top') && L && L.classList.contains('is-absorb')) {
      if (!absorbAt) absorbAt = Date.now();
      if (Date.now() - absorbAt < 900) { setTimeout(begin, 30); return; }
    } else { setTimeout(begin, 50); return; }
  }
  if (sec.classList.contains('rf-top')) root.classList.add('s-head');
  var fx = sec.getAttribute('data-fx');

  // 案A：4秒ごとに 朝→昼→夕方→夜。時刻と進み具合の線も合わせる
  if (fx === 'a') {
    var STAY = +(sec.getAttribute('data-stay') || 4000);  // A2 は 2.5秒
    var imgs = all('.rf-media img', sec), times = all('.rf-time', sec), bars = all('.rf-bar li', sec);
    sec.style.setProperty('--stay', STAY / 1000 + 's');
    var n = 0;
    var sweep = sec.querySelector('.rv-sweep');
    // 金の光を、写真が開く斜めの境目に毎フレーム合わせて置く（2026-10-07。写真は季節ごとに拡大・移動するので、
    // 固定の位置で動かすと境目とずれる。境目の実際の画面上の位置（clip-path と画像の枠から計算）を読んで、光の線を同じ位置へ置く）
    var edgeSvg = sweep && sweep.querySelector('.rv-edge');
    var trackEdge = function () {
      requestAnimationFrame(trackEdge);
      if (!edgeSvg || !sweep.classList.contains('is-run')) return;
      var on = sec.querySelector('.rf-media img.is-on');
      if (!on) return;
      var m = getComputedStyle(on).clipPath.match(/polygon\(([^)]*)\)/);
      if (!m) return;
      var pts = m[1].split(',').map(function (q) { return q.trim().split(' '); });
      var r = on.getBoundingClientRect(), sr = sweep.getBoundingClientRect();
      var num = function (v, w) { return v.indexOf('%') > 0 ? parseFloat(v) / 100 * w : parseFloat(v); };
      // clip-path の % は、拡大前の画像の枠（offsetWidth）が基準。画像は中心を基準に scale 倍されて外接長方形 r になるので、
      // 拡大前の枠の左端は r.left + (r.width - offsetWidth * scale) / 2、1px あたりの長さは scale 倍
      var sc = r.width / (on.offsetWidth || r.width), ow = on.offsetWidth || r.width;
      var left0 = r.left + (r.width - ow * sc) / 2;
      var topX = left0 + num(pts[1][0], ow) * sc, botX = left0 + num(pts[2][0], ow) * sc;
      // 光の層（sweep）の座標（0〜100）に直す。光の線の polygon は「上 x=0・下 x=-30」の形なので、上端の位置と傾きを合わせる
      var W = sr.width || 1, k = 100 / W;
      var tx = (topX - sr.left) * k, bx = (botX - sr.left) * k;
      // 境目は毎フレーム動くので、読んだ値は次の描画では少し古い。前のフレームとの差（速度）で、1フレーム先へ進めて置く
      if (trackEdge.px !== undefined) { tx += (tx - trackEdge.px); bx += (bx - trackEdge.pb); }
      trackEdge.px = (topX - sr.left) * k; trackEdge.pb = (botX - sr.left) * k;
      edgeSvg.querySelectorAll('polygon').forEach(function (poly, i) {
        var w = i === 0 ? 6 : 0.5;   // 光の帯の幅（0〜100 の座標。にじみ6、細い白い線0.5）
        // 細い白い線(i=1)は境目の上に、にじみ(i=0)は境目から右へ。どちらも左の辺を境目に置く
        poly.setAttribute('points', tx + ',0 ' + (tx + w) + ',0 ' + (bx + w) + ',100 ' + bx + ',100');
      });
      // 光の線の向き（グラデーション）も、上端から下端へ（帯の左端→右端）
      var g = edgeSvg.querySelector('#rvEdgeG');
      if (g) { g.setAttribute('x1', tx + 6); g.setAttribute('x2', tx); g.setAttribute('y1', 0); g.setAttribute('y2', 0); }  // 境目に近いほど濃く、右へ薄くなる
    };
    if (edgeSvg) requestAnimationFrame(trackEdge);
    var show = function (i) {
      sec.setAttribute('data-season', i);  // /top-a2/：今の季節（0春 1夏 2秋 3冬）。秋→冬の雪の演出に使う
      step(imgs, i);
      if (sweep && (!sec.classList.contains('rf-top') || sec.classList.contains('rf-wipe'))) { sweep.classList.remove('is-run'); void sweep.offsetWidth; sweep.classList.add('is-run'); }  // A2：金の光の帯（切り替えのたびに。/top-a2/ では外した 2026-10-07）
      times.forEach(function (t, k) { t.classList.toggle('is-on', k === i); });
      if (!bars.length) return;  // 時刻を出さない版（/top-a2/）
      bars.forEach(function (b, k) { b.classList.toggle('is-done', k < i); b.classList.remove('is-on'); });
      void bars[i].offsetWidth;
      bars[i].classList.add('is-on');
    };
    // 4枚とも先に読み込み・描画の準備（decode）を済ませてから動かす（初めて出す写真で引っかからないように）
    Promise.all(imgs.map(function (im) { return im.decode ? im.decode().catch(function () {}) : null; })).then(function () {
      // ロゴの演出のあとは、最初の写真がもう見えているので現れ直させない（春がぼやけ直して見えるため）
      if (!window.LF_LOADER_RUN) { imgs[0].classList.remove('is-on'); show(0); }
      // 季節ごとに見せる時間を変えられる（data-stays="春,夏,秋,冬" ミリ秒。冬は雪の演出のあとに現れるので長め）
      var stays = (sec.getAttribute('data-stays') || '').split(',').map(Number);
      var next = function () {
        setTimeout(function () { n = (n + 1) % imgs.length; show(n); next(); }, stays[n] || STAY);
      };
      next();
    });
  }

  // 案A2：見出しを1文字ずつ勢いよく出し、数字を 0 から増やす
  var vt = sec.querySelector('.rv-title');
  if (vt) {
    var k = 0;
    // ロゴの演出でキャッチコピーが見出しへ吸い込まれた場合は、見出しはそのまま見せる（1文字ずつの動きは2回目以降）
    if (!window.LF_LOADER_RUN) all('span', vt).forEach(function (row) {
      Array.prototype.slice.call(row.childNodes).forEach(function (node) {
        var text = node.textContent, wrap = document.createDocumentFragment();
        text.split('').forEach(function (ch) {
          var c = document.createElement('span');
          c.className = 'rv-ch';
          c.textContent = ch;
          c.style.transitionDelay = (0.2 + k++ * 0.05) + 's';
          wrap.appendChild(c);
        });
        if (node.nodeType === 3) row.replaceChild(wrap, node); else { node.textContent = ''; node.appendChild(wrap); }
      });
    });
    requestAnimationFrame(function () { requestAnimationFrame(function () { vt.classList.add('is-go'); sec.classList.add('is-go'); }); });
    // マウスの位置（PCだけ）とスクロールの量を渡す。写真・大きな英字・コピーが別々の量でずれて、奥行きが出る
    if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
      window.addEventListener('mousemove', function (e) {
        sec.style.setProperty('--mx', (e.clientX / window.innerWidth * 2 - 1).toFixed(3));
        sec.style.setProperty('--my', (e.clientY / window.innerHeight * 2 - 1).toFixed(3));
      }, { passive: true });
    }
    var onScroll = function () { sec.style.setProperty('--sy', Math.min(window.scrollY, window.innerHeight).toFixed(0)); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    all('.rv-count', sec).forEach(function (el) {
      var to = +el.getAttribute('data-count'), t0 = null;
      el.textContent = '0';
      var tick = function (t) {
        if (t0 === null) t0 = t + 700;  // 見出しが出てから
        var p = Math.max(0, Math.min((t - t0) / 1600, 1));
        el.textContent = Math.round(to * (1 - Math.pow(1 - p, 3))).toLocaleString('ja-JP');
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }

  // 案B：3枚のパネルが、少しずつ時間をずらして下から切り替わる
  if (fx === 'b') {
    all('.rf-panel', sec).forEach(function (p, k) {
      var imgs = all('img', p), n = 0;
      setTimeout(function () {
        setInterval(function () { n = (n + 1) % imgs.length; step(imgs, n); }, 3600);
      }, 600 + k * 500);
    });
  }

  // 案C：スクロールの進み具合で、写真と言葉を切り替える。今の写真はスクロールに合わせて少しずつ寄る（奥へ進む感じ）
  if (fx === 'c') {
    var cimgs = all('.rf-media img', sec), words = all('.rf-word', sec), cur = 0;
    var update = function () {
      var r = sec.getBoundingClientRect(), run = r.height - window.innerHeight;
      var p = run > 0 ? Math.min(Math.max(-r.top / run, 0), .9999) : 0;
      var i = Math.floor(p * cimgs.length), local = p * cimgs.length - i;
      if (i !== cur) {
        cimgs[cur].classList.remove('is-on'); words[cur].classList.remove('is-on');
        cimgs[i].classList.add('is-on'); words[i].classList.add('is-on');
        cur = i;
      }
      cimgs[i].style.setProperty('--z', (1 + local * .18).toFixed(3));
    };
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  // /top-a2/：ヒーローより下の動き（④ 数字のカードに光が走る、⑤ 相談ボタンがマウスに引き寄せられる）
  if (sec.classList.contains('rf-top')) {
    var cards = all('.num-card');
    if (cards.length && 'IntersectionObserver' in window) {
      var cio = new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (!e.isIntersecting) return;
          cio.disconnect();
          // 数字が増え終わるころ（main.js のカウントアップは約1.8秒）に、左から順に光らせる
          cards.forEach(function (c, i) { setTimeout(function () { c.classList.add('is-shine'); }, 2000 + i * 250); });
        });
      }, { threshold: .6 });
      cio.observe(cards[0]);
    }
    var cta = document.querySelector('#final-cta .btn-primary');
    if (cta && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
      var area = document.getElementById('final-cta');  // 段全体でマウスの位置を見て、ボタンから 160px 以内なら引き寄せる
      area.addEventListener('mousemove', function (e) {
        var r = cta.getBoundingClientRect(), dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
        var d = Math.hypot(dx, dy), pull = d < 160 ? (1 - d / 160) : 0;
        cta.style.setProperty('--bx', (dx * .35 * pull).toFixed(1) + 'px');
        cta.style.setProperty('--by', (dy * .35 * pull).toFixed(1) + 'px');
      });
      area.addEventListener('mouseleave', function () { cta.style.setProperty('--bx', '0px'); cta.style.setProperty('--by', '0px'); });
    }
  }
  };
  begin();
})();
