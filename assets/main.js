  (function () {
    var root = document.documentElement;
    root.classList.add('js');
    window.LF_READY = true;
    document.getElementById('year').textContent = new Date().getFullYear();

    // ヘッダー：スクロールで白背景に
    var header = document.getElementById('header');
    var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 24); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    // ハンバーガーメニュー
    var btn = document.getElementById('menuBtn');
    var drawer = document.getElementById('drawer');
    var setMenu = function (open) {
      document.body.classList.toggle('is-menu-open', open);
      btn.setAttribute('aria-expanded', open);
      btn.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
      drawer.setAttribute('aria-hidden', !open);
      document.body.style.overflow = open ? 'hidden' : '';
    };
    btn.addEventListener('click', function () { setMenu(!document.body.classList.contains('is-menu-open')); });
    drawer.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });

    // ページ最上部（トップはファーストビュー、下層はページ見出し）：順番にフェードイン
    var first = document.querySelector('.fv, .page-hero');
    var startFirst = function () {
      if (first && first.classList.contains('fv')) {
        requestAnimationFrame(function () { first.classList.add('is-loaded'); });  // 写真のズームも文字と同時に始める
      }
      if (first) {
        first.querySelectorAll('.fade').forEach(function (el, i) {
          setTimeout(function () { el.classList.add('is-in'); }, 60 + i * 80);
        });
      }
    };

    // トップの最初の演出（build.py の LOADER）。演出のあいだはファーストビューの動きを待たせ、
    // キャッチコピーが見出しの位置へ吸い込まれる瞬間に始める（本物の見出しと入れ替わって見える）
    var runLoader = function (done) {
      window.LF_LOADER_RUN = true;
      try { sessionStorage.setItem('lf_loader', '1'); } catch (e) {}
      window.scrollTo(0, 0);
      var L = document.getElementById('lfLoader');
      var called = false, ended = false;
      var go = function () { if (!called) { called = true; done(); } };
      var end = function () {
        if (ended) return;
        ended = true;
        go();
        showH1();
        L.classList.add('is-out');
        setTimeout(function () { root.classList.remove('is-loading'); L.remove(); }, 500);
      };
      if (!L) { root.classList.remove('is-loading'); go(); return; }
      L.addEventListener('click', end);  // 押せばすぐ終わる

      var fill = L.querySelector('.ll-ring .f'), pct = L.querySelector('.ll-pct');
      var C = 2 * Math.PI * 54, D = 1800, t0 = null;
      fill.style.strokeDasharray = C;
      fill.style.strokeDashoffset = C;

      // 演出の文字を、本物の要素とぴったり重なる位置・大きさへ動かす。
      // 文字組み（書体・太さ・行間・字間）は本物と同じにしてあるので、着いたところで
      // 本物とゆっくり入れ替える（CSS の .ll-catch / .fv h1.ll-in）と、境目なく溶けて見える
      var fly = function (from, to) {
        if (!from || !to) return;
        var a = from.getBoundingClientRect(), b = to.getBoundingClientRect();
        from.style.transformOrigin = '0 0';
        from.style.transform = 'translate(' + (b.left - a.left) + 'px,' + (b.top - a.top) + 'px) scale(' + (b.height / a.height) + ')';
        from.classList.add('is-fly');
      };
      // 本物の見出しは、ぼかした状態から浮かび上がらせる（演出のコピーがぼけながら消えるのと重ねて、
      // 入れ替わりの境目を見せない）。ふつうのフェードの「下からせり上がる」動きは位置がずれるので使わない
      var h1 = document.querySelector('.fv h1');
      var hlogo = document.querySelector('.header .logo');
      var showH1 = function () { [h1, hlogo].forEach(function (el) { if (el) el.classList.add('is-on'); }); };
      var absorb = function () {
        if (ended) return;
        if (h1) { h1.classList.remove('fade', 'is-in'); h1.classList.add('ll-in'); }
        if (hlogo) hlogo.classList.add('ll-in');  // ヘッダーのロゴも、演出のロゴが重なるまで隠しておく
        fly(L.querySelector('.ll-logo'), hlogo);
        fly(L.querySelector('.ll-catch'), h1);
        L.classList.add('is-absorb');           // 白い幕をゆっくり透かして、奥のトップページを見せる
        setTimeout(showH1, 950);                // 文字が着く少し前から、本物の見出しを重ねて浮かべる
        setTimeout(go, 700);
        setTimeout(end, 2100);
      };
      var tick = function (ts) {
        if (ended) return;
        if (t0 === null) t0 = ts;
        var p = Math.min((ts - t0) / D, 1), e = 1 - Math.pow(1 - p, 3);
        pct.textContent = Math.round(e * 100) + '%';
        fill.style.strokeDashoffset = C * (1 - e);
        if (p < 1) { requestAnimationFrame(tick); return; }
        setTimeout(function () {
          if (ended) return;
          L.classList.add('is-p2');
          setTimeout(absorb, 1300);
        }, 250);
      };
      requestAnimationFrame(tick);
    };

    if (root.classList.contains('is-loading')) runLoader(startFirst); else startFirst();

    document.addEventListener('transitionend', function (e) {
      var el = e.target;
      if (e.propertyName === 'opacity' && el.classList && el.classList.contains('fade') && el.classList.contains('is-in')) {
        el.classList.remove('fade', 'is-in');
        el.style.transitionDelay = '';
      }
    });

    // スクロールでフェードイン（1回だけ）。同じ親の中では少しずつずらす
    var targets = Array.prototype.filter.call(document.querySelectorAll('main .fade'), function (el) { return !first || !first.contains(el); });
    if (!('IntersectionObserver' in window)) {
      targets.forEach(function (el) { el.classList.add('is-in'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          var sibs = Array.prototype.filter.call(el.parentNode.children, function (c) { return c.classList.contains('fade'); });
          el.style.transitionDelay = Math.min(sibs.indexOf(el), 3) * 0.08 + 's';
          el.classList.add('is-in');
          io.unobserve(el);
        });
      }, { rootMargin: '0px 0px -8% 0px' });
      targets.forEach(function (el) { io.observe(el); });
    }

    // スマホ下部の固定CTA：ページ最上部を過ぎたら出し、最後のCTAかお問い合わせページの電話番号が見えたら隠す
    var bar = document.getElementById('spBar');
    var end = document.querySelector('#final-cta, .contact-tel');
    var topGone = false, endSeen = false;
    var update = function () { bar.classList.toggle('is-shown', topGone && !endSeen); };
    if ('IntersectionObserver' in window && first) {
      new IntersectionObserver(function (e) { topGone = !e[0].isIntersecting; update(); }).observe(first);
      if (end) new IntersectionObserver(function (e) { endSeen = e[0].isIntersecting; update(); }).observe(end);
    }
  })();
  // トップのファーストビューの写真を、春→夏→秋→冬→春…と切り替える（見た目は season.css。トップ以外では何もしない）
  (function () {
    var fv = document.querySelector('.fv');
    var box = fv && fv.querySelector('.fv-photo');
    if (!box) return;
    var imgs = Array.prototype.slice.call(box.querySelectorAll('img'));
    var STAY = 6000;  // 1枚を見せる時間
    var FIRST = 3500; // 最初の演出が終わってから、最初に切り替えるまで（春は演出の間も見えているので、ほかより短くする）
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var cur = 0, timer = null, paused = reduce;

    // 一時停止ボタン（自動で切り替わり続けるので、止められるようにする。動きを減らす設定の端末では、最初から止めておく）。
    // 季節の名前のボタンは、2026-10-05 お客さまの希望で外した
    var pause = document.createElement('button');
    pause.type = 'button';
    pause.className = 'fv-season';
    var setPause = function (p, first) {
      paused = p;
      pause.setAttribute('aria-label', p ? '写真の切り替えを再生する' : '写真の切り替えを一時停止する');
      pause.innerHTML = p ? '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 0.5 9.5 5 1.5 9.5z"/></svg>'
                          : '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 0.5h2.5v9H1.5zM6 0.5h2.5v9H6z"/></svg>';
      restart(first);
    };
    pause.addEventListener('click', function () { setPause(!paused); });
    fv.appendChild(pause);

    var show = function (i) {
      if (i === cur) return;
      var next = imgs[i];
      // まだ読み込めていない写真は飛ばさず、読み込めてから切り替える
      if (!next.complete || !next.naturalWidth) { next.addEventListener('load', function () { show(i); }, { once: true }); return; }
      imgs.forEach(function (img) { img.classList.remove('is-prev'); });
      imgs[cur].classList.add('is-prev');
      imgs[cur].classList.remove('is-show');
      next.classList.add('is-show');
      var prev = imgs[cur];
      setTimeout(function () { if (!prev.classList.contains('is-show')) prev.classList.remove('is-prev'); }, 2700);
      cur = i;
    };
    // first：次に切り替えるまでの時間（省略すると STAY）。そのあとは STAY ごと
    var restart = function (first) {
      clearTimeout(timer);
      clearInterval(timer);
      if (paused || document.hidden) return;
      var next = function () { show((cur + 1) % imgs.length); };
      timer = setTimeout(function () { next(); timer = setInterval(next, STAY); }, typeof first === 'number' ? first : STAY);
    };
    // タブを見ていない間は止める（戻ったときに何枚も飛ばないように）
    document.addEventListener('visibilitychange', function () { restart(); });

    // 夏・秋・冬の写真は、最初の画面が出てから読み込む（最初の表示を遅くしないため）
    var loadRest = function () {
      imgs.forEach(function (img, i) {
        if (i && img.dataset.src) { img.src = img.dataset.src; img.removeAttribute('data-src'); }
        if (i) img.classList.add('is-ready');
      });
    };
    // 最初の演出とズーム（main.js）が終わるのを待ってから（1.8秒）切り替えを始める
    var start = function () {
      loadRest();
      setTimeout(function () {
        imgs[0].classList.add('is-ready');
          setPause(paused, FIRST - 1800);
      }, 1800);
    };
    setPause(true);  // 始まるまでは止めておく
    paused = reduce;
    var wait = setInterval(function () {
      if (fv.classList.contains('is-loaded')) { clearInterval(wait); start(); }
    }, 200);
  })();
