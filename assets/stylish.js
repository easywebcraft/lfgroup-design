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
  // ① 入口のタイル：同じ段の左右で少しずらす
  Array.prototype.forEach.call(document.querySelectorAll('.entry'), function (el, i) {
    el.setAttribute('data-delay', (i % 2) * 220);
    io.observe(el);
  });
  // ③ 小見出しの金の線（最初の写真の中のものは除く）
  var lio = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      lio.unobserve(e.target);
      whenReady(function () { e.target.classList.add('s-line'); });
    });
  }, { rootMargin: '0px 0px -12% 0px' });
  Array.prototype.forEach.call(document.querySelectorAll('main .eyebrow'), function (el) { if (!el.closest('.fv')) lio.observe(el); });

  // ② 最初の写真が開き始めたら、少し遅れてメニューと相談ボタンを降ろす
  var fv = document.querySelector('.fv');
  var dropHeader = function () {
    if (fv && !fv.classList.contains('is-loaded')) return setTimeout(dropHeader, 100);
    setTimeout(function () { root.classList.add('s-head'); }, fv ? 900 : 0);
    setTimeout(function () { root.classList.add('s-ul'); }, fv ? 1500 : 0);  // ⑨ 見出しの金の下線は、メニューが降りたあとに
  };
  whenReady(dropHeader);

  // ①・④ 奥行き：画面の中での位置に合わせて、写真を上下に少しだけずらす
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
    // ⑧ ヒーローの奥行き：スクロールした量（画面の高さまで）を渡す。写真はゆっくり、文字は速く流れる
    if (fv) fv.style.setProperty('--fy', Math.min(window.scrollY, vh).toFixed(0));
    // ④ 数字の段：上端が画面の下端に来たとき 0、画面の 25% の高さまで上がったとき 1
    if (nums) {
      var s = nums.getBoundingClientRect();
      nums.style.setProperty('--p', Math.min(1, Math.max(0, (vh - s.top) / (vh * .75))).toFixed(3));
    }
  };
  var nums = document.querySelector('.numbers');
  window.addEventListener('resize', function () { vh = window.innerHeight; parallax(); });

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
