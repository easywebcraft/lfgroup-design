  // トップページの動きの試作（/motion/ だけで読み込む。中身は motion.css の先頭を参照）
  (function () {
    if (!window.matchMedia('(prefers-reduced-motion: no-preference)').matches) return;
    var root = document.documentElement;
    root.classList.add('m-go');

    // A・B・D：画面に入ったら一度だけクラスを付ける（main.js の .fade とは別。あちらは終わると is-in を外すため）
    var once = function (els, cls, margin) {
      if (!('IntersectionObserver' in window)) { els.forEach(function (el) { el.classList.add(cls); }); return; }
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          e.target.classList.add(cls);
          io.unobserve(e.target);
        });
      }, { rootMargin: margin });
      els.forEach(function (el) { io.observe(el); });
    };
    var all = function (sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); };

    // A. 写真が帯の後ろから現れる。写真が右側にある行は右から
    var photos = all('.m-reveal');
    photos.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.left + r.width / 2 > window.innerWidth / 2 + 1 && r.width < window.innerWidth * .8) el.classList.add('is-right');
    });
    once(photos, 'is-on', '0px 0px -18% 0px');

    // B. 小見出しの線
    once(all('.eyebrow'), 'm-line', '0px 0px -12% 0px');

    // D. 強みの番号：数字だけを包んで、下からせり上げる
    all('.feature-num').forEach(function (el) {
      var t = el.firstChild;
      if (t && t.nodeType === 3) {
        var s = document.createElement('span');
        s.className = 'm-num';
        s.textContent = t.textContent;
        el.replaceChild(s, t);
      }
    });
    once(all('.feature'), 'm-on', '0px 0px -20% 0px');

    // D・E：スクロールに合わせて動かす（PC だけ。スマホは画面が狭く重く感じやすいので、A のような出方だけにする）
    var wide = window.matchMedia('(min-width: 768px)');
    var drift = all('.feature-photo img, .split-photo img');
    var show = document.querySelector('.showcase-photo');
    var ticking = false;
    var update = function () {
      ticking = false;
      if (!wide.matches) return;
      var vh = window.innerHeight;
      drift.forEach(function (img) {
        var r = img.parentNode.getBoundingClientRect();
        if (r.bottom < 0 || r.top > vh) return;
        // 画面の真ん中に来たとき 0。上下に最大 6%（写真の高さに対して）ずらす
        var d = ((r.top + r.height / 2) - vh / 2) / (vh / 2 + r.height / 2);
        img.style.setProperty('--py', (d * 6).toFixed(2) + '%');
      });
      if (show) {
        var s = show.getBoundingClientRect();
        // 写真の上端が画面の下端に来たとき 0、画面の 25% の高さまで上がったとき 1
        var p = Math.min(1, Math.max(0, (vh - s.top) / (vh * .75)));
        show.style.setProperty('--p', p.toFixed(3));
      }
    };
    var onScroll = function () { if (!ticking) { ticking = true; requestAnimationFrame(update); } };
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    update();
  })();
