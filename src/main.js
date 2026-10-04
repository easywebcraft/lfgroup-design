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

      // 演出の文字を、本物の要素の位置と大きさへ動かしながら消す
      var fly = function (from, to) {
        if (!from || !to) return;
        var a = from.getBoundingClientRect(), b = to.getBoundingClientRect();
        var dx = (b.left + b.width / 2) - (a.left + a.width / 2);
        var dy = (b.top + b.height / 2) - (a.top + a.height / 2);
        from.style.transform = 'translate(' + dx + 'px,' + dy + 'px) scale(' + (b.height / a.height) + ')';
        from.style.opacity = '0';
      };
      // 本物の見出しは、ぼかした状態から浮かび上がらせる（演出のコピーがぼけながら消えるのと重ねて、
      // 入れ替わりの境目を見せない）。ふつうのフェードの「下からせり上がる」動きは位置がずれるので使わない
      var h1 = document.querySelector('.fv h1');
      var showH1 = function () { if (h1) h1.classList.add('is-on'); };
      var absorb = function () {
        if (ended) return;
        if (h1) { h1.classList.remove('fade', 'is-in'); h1.classList.add('ll-in'); }
        fly(L.querySelector('.ll-logo'), document.querySelector('.header .logo'));
        fly(L.querySelector('.ll-catch'), h1);
        L.classList.add('is-absorb');           // 白い幕を透かして、奥のトップページを見せる
        setTimeout(showH1, 420);
        setTimeout(go, 500);
        setTimeout(end, 1350);
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

    // スマホ下部の固定CTA：ページ最上部を過ぎたら出し、最後のCTAかフォームが見えたら隠す
    var bar = document.getElementById('spBar');
    var end = document.querySelector('#final-cta, .form');
    var topGone = false, endSeen = false;
    var update = function () { bar.classList.toggle('is-shown', topGone && !endSeen); };
    if ('IntersectionObserver' in window && first) {
      new IntersectionObserver(function (e) { topGone = !e[0].isIntersecting; update(); }).observe(first);
      if (end) new IntersectionObserver(function (e) { endSeen = e[0].isIntersecting; update(); }).observe(end);
    }

    // お問い合わせフォーム（試作：送信はしない）
    var form = document.getElementById('contactForm');
    if (form) {
      var types = { document: '資料請求', consult: '保険・お金のご相談' };
      var t = types[new URLSearchParams(location.search).get('type')];
      if (t) form.querySelector('input[name="type"][value="' + t + '"]').checked = true;
      var showErr = function (input, msg) {
        var box = input.closest('.field');
        var err = box.querySelector('.err');
        if (msg) {
          if (!err) { err = document.createElement('p'); err.className = 'err'; err.id = input.name + '-err'; box.appendChild(err); }
          err.textContent = msg;
          input.setAttribute('aria-invalid', 'true');
          input.setAttribute('aria-describedby', err.id);
        } else {
          if (err) err.remove();
          input.removeAttribute('aria-invalid');
          input.removeAttribute('aria-describedby');
        }
      };
      var check = function (input) {
        var v = input.value.trim();
        if (input.type === 'checkbox') return showErr(input, input.checked ? '' : 'プライバシーポリシーへの同意が必要です');
        if (!v) return showErr(input, '入力してください');
        if (input.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return showErr(input, 'メールアドレスの形式で入力してください');
        if (input.type === 'tel' && !/^[0-9０-９\-－+() ]{10,}$/.test(v)) return showErr(input, '電話番号を入力してください');
        showErr(input, '');
      };
      var required = form.querySelectorAll('[required]');
      required.forEach(function (input) {
        input.addEventListener('blur', function () { check(input); });
        input.addEventListener('change', function () { if (input.hasAttribute('aria-invalid')) check(input); });
      });
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        required.forEach(check);
        var bad = form.querySelector('[aria-invalid="true"]');
        if (bad) { bad.focus(); return; }
        var done = document.getElementById('formDone');
        form.hidden = true;
        done.hidden = false;
        done.focus();
      });
    }
  })();
