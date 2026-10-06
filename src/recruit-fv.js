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
  var begin = function () {
  if (root.classList.contains('is-loading')) { setTimeout(begin, 100); return; }
  var fx = sec.getAttribute('data-fx');

  // 案A：4秒ごとに 朝→昼→夕方→夜。時刻と進み具合の線も合わせる
  if (fx === 'a') {
    var STAY = +(sec.getAttribute('data-stay') || 4000);  // A2 は 2.5秒
    var imgs = all('.rf-media img', sec), times = all('.rf-time', sec), bars = all('.rf-bar li', sec);
    sec.style.setProperty('--stay', STAY / 1000 + 's');
    var n = 0;
    var sweep = sec.querySelector('.rv-sweep');
    var show = function (i) {
      sec.setAttribute('data-season', i);  // /top-a2/：今の季節（0春 1夏 2秋 3冬）。秋→冬の雪の演出に使う
      step(imgs, i);
      if (sweep && (i === 0 || !sec.classList.contains('rf-top'))) { sweep.classList.remove('is-run'); void sweep.offsetWidth; sweep.classList.add('is-run'); }  // A2：金の光の帯（/top-a2/ は冬→春の一年が巡るときだけ）
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
  };
  begin();
})();
