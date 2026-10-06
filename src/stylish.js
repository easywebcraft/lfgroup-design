/* スタイリッシュ版の試作（/stylish/・2026-10-06）。中身は stylish.css の先頭のとおり。
   lenis.min.js（なめらかなスクロール。MIT License, darkroom.engineering）を先に読み込んでおく */
(function () {
  var root = document.documentElement;
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  root.classList.add('s-ready');

  // A 見出しの行（中の span、なければ見出し全体）を「枠」と「中身」に分ける
  var lines = document.querySelectorAll('.s-lines');
  Array.prototype.forEach.call(lines, function (h) {
    var rows = Array.prototype.filter.call(h.children, function (c) { return c.tagName === 'SPAN'; });
    if (!rows.length) { h.innerHTML = '<span>' + h.innerHTML + '</span>'; rows = [h.firstChild]; }
    rows.forEach(function (r, i) {
      r.classList.add('s-row');
      r.innerHTML = '<span class="s-in" style="transition-delay:' + (i * 0.12) + 's">' + r.innerHTML + '</span>';
    });
  });

  // 画面に入ったら1回だけ動かす（ページを開いたときのロゴの演出中は待つ）
  var whenReady = function (fn) {
    if (root.classList.contains('is-loading')) return setTimeout(function () { whenReady(fn); }, 150);
    fn();
  };
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      io.unobserve(e.target);
      var el = e.target, delay = +(el.getAttribute('data-delay') || 0);
      whenReady(function () { setTimeout(function () { el.classList.add(el.classList.contains('entry') ? 'is-open' : 'is-shown'); }, delay); });
    });
  }, { rootMargin: '0px 0px -12% 0px' });
  Array.prototype.forEach.call(lines, function (h) { io.observe(h); });
  // B 入口のタイル：同じ段の左右で少しずらす
  Array.prototype.forEach.call(document.querySelectorAll('.entry'), function (el, i) {
    el.setAttribute('data-delay', (i % 2) * 160);
    io.observe(el);
  });

  // B 奥行き：画面の中での位置に合わせて、写真を上下に少しだけずらす
  var par = [];
  Array.prototype.forEach.call(document.querySelectorAll('.entry img'), function (img) { par.push([img, img.parentNode, 28]); });
  var nb = document.querySelector('.numbers-bg');
  if (nb) par.push([nb, nb.parentNode, 60]);
  var vh = window.innerHeight;
  var parallax = function () {
    par.forEach(function (p) {
      var r = p[1].getBoundingClientRect();
      if (r.bottom < -100 || r.top > vh + 100) return;
      var t = (r.top + r.height / 2 - vh / 2) / (vh / 2 + r.height / 2);  // 画面の中央で 0、上下の端で ±1
      p[0].style.setProperty('--py', (-t * p[2]).toFixed(1) + 'px');
    });
  };
  window.addEventListener('resize', function () { vh = window.innerHeight; parallax(); });

  // FV：見出しの頭の言葉を「保険→家計→暮らし」と切り替える（2.8秒ごと）。枠の幅も今の言葉に合わせる
  var rot = document.querySelector('.sf-rot');
  if (rot) {
    var words = rot.children, k = 0;
    var fit = function () { rot.style.width = words[k].offsetWidth + 'px'; };
    fit();
    setInterval(function () {
      var old = words[k];
      k = (k + 1) % words.length;
      old.classList.remove('is-on');
      old.classList.add('is-out');
      words[k].classList.add('is-on');
      fit();
      setTimeout(function () { old.classList.remove('is-out'); }, 850);
    }, 2800);
    window.addEventListener('resize', fit);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);  // 書体が読み込まれると幅が変わるので測り直す
  }

  // FV：スクロールに合わせて、画面いっぱいの写真を角の丸いカードへ縮める（--p：0＝全面、1＝縮みきり）
  var sf = document.querySelector('.fv.sf');
  var shrink = function () {
    if (!sf) return;
    var r = sf.getBoundingClientRect(), run = r.height - window.innerHeight;
    var p = run > 0 ? Math.min(Math.max(-r.top / run, 0), 1) : 0;
    sf.style.setProperty('--p', p.toFixed(4));
    sf.classList.toggle('is-scrolling', p > 0);
  };
  var parallaxOnly = parallax;
  parallax = function () { parallaxOnly(); shrink(); };

  // D なめらかなスクロール。ロゴの演出中は止めておく。ページ内リンクは固定ヘッダーの分だけずらす
  if (window.Lenis) {
    var header = document.querySelector('.header');
    var lenis = new Lenis({ lerp: 0.09, anchors: { offset: -(header ? header.offsetHeight : 0) } });
    lenis.on('scroll', parallax);
    var raf = function (t) { lenis.raf(t); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
    if (root.classList.contains('is-loading')) {
      lenis.stop();
      whenReady(function () { lenis.start(); });
    }
  } else {
    window.addEventListener('scroll', parallax, { passive: true });
  }
  parallax();
})();
