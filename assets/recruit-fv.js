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
    // 写真のマスクと金の光を、同じフレーム・同じ進行値で描く。
    // CSSのマスクを後追いして速度を予測すると、加速中や季節の変わり目に光だけが先に進む。
    var edgeSvg = sweep && sweep.querySelector('.rv-edge');
    var sharedWipe = edgeSvg && sec.classList.contains('rf-wipe');
    var wipeFrame = 0;
    var easeWipe = function (x) {
      // 既存の cubic-bezier(.77, 0, .18, 1) を維持する。
      var lo = 0, hi = 1, t = x;
      for (var k = 0; k < 20; k++) {
        t = (lo + hi) / 2;
        var u = 1 - t;
        var bx = 3 * u * u * t * .77 + 3 * u * t * t * .18 + t * t * t;
        if (bx < x) lo = t; else hi = t;
      }
      return 3 * (1 - t) * t * t + t * t * t;
    };
    var animateWipe = function (on) {
      var start = performance.now(), duration = 1400;
      var draw = function (now) {
        var time = Math.max(0, Math.min(1, (now - start) / duration));
        var x = 130 * easeWipe(time);
        on.style.clipPath = 'polygon(0 0, ' + x + '% 0, ' + (x - 30) + '% 100%, -30% 100%)';
        var r = on.getBoundingClientRect(), sr = sweep.getBoundingClientRect();
        // 拡大・移動後の写真の境目を、光の層の上端・下端まで延長して座標を変換する。
        // 写真の上端と光の上端は一致しないため、縦方向の移動と高さの違いも含める。
        var topX = r.left + r.width * x / 100;
        var slope = .3 * r.width / (r.height || 1);
        var tx = (topX - slope * (sr.top - r.top) - sr.left) * 100 / (sr.width || 1);
        var bx = (topX - slope * (sr.bottom - r.top) - sr.left) * 100 / (sr.width || 1);
        edgeSvg.querySelectorAll('polygon').forEach(function (poly, i) {
          var w = i === 0 ? 6 : .5;
          poly.setAttribute('points', tx + ',0 ' + (tx + w) + ',0 ' + (bx + w) + ',100 ' + bx + ',100');
        });
        var g = edgeSvg.querySelector('#rvEdgeG');
        if (g) {
          g.setAttribute('x1', tx + 6); g.setAttribute('x2', tx);
          g.setAttribute('y1', 0); g.setAttribute('y2', 0);
        }
        edgeSvg.style.opacity = time < .8 ? '1' : String((1 - time) / .2);
        if (time < 1) wipeFrame = requestAnimationFrame(draw);
        else { wipeFrame = 0; sweep.classList.remove('is-run'); }
      };
      draw(start);
    };
    var show = function (i, initial) {
      sec.setAttribute('data-season', i);  // /top-a2/：今の季節（0春 1夏 2秋 3冬）。秋→冬の雪の演出に使う
      if (sharedWipe && !initial) {
        cancelAnimationFrame(wipeFrame);
        imgs.forEach(function (im) { im.style.removeProperty('clip-path'); });
      }
      // 初回はHTMLで表示済みの1枚目を残す。金の光は2枚目から使う。
      if (!initial) {
        step(imgs, i);
        if (sweep && (!sec.classList.contains('rf-top') || sec.classList.contains('rf-wipe'))) { sweep.classList.remove('is-run'); void sweep.offsetWidth; sweep.classList.add('is-run'); }
        if (sharedWipe) animateWipe(imgs[i]);
      }
      times.forEach(function (t, k) { t.classList.toggle('is-on', k === i); });
      if (!bars.length) return;  // 時刻を出さない版（/top-a2/）
      bars.forEach(function (b, k) { b.classList.toggle('is-done', k < i); b.classList.remove('is-on'); });
      void bars[i].offsetWidth;
      bars[i].classList.add('is-on');
    };
    // 最初の写真だけ準備できれば開始する。次の写真が未準備なら、今の写真を残して待つ。
    var ready = imgs.map(function (im) { return im.decode ? im.decode().catch(function () {}) : Promise.resolve(); });
    ready[0].then(function () {
      if (sharedWipe) show(0, true);
      else if (!window.LF_LOADER_RUN) { imgs[0].classList.remove('is-on'); show(0); }
      // 季節ごとに見せる時間を変えられる（data-stays="春,夏,秋,冬" ミリ秒。冬は雪の演出のあとに現れるので長め）
      var stays = (sec.getAttribute('data-stays') || '').split(',').map(Number);
      var next = function () {
        setTimeout(function () {
          var upcoming = (n + 1) % imgs.length;
          ready[upcoming].then(function () { n = upcoming; show(n); next(); });
        }, stays[n] || STAY);
      };
      next();
    });
  }

  // 案A2：見出しを1文字ずつ勢いよく出し、数字を 0 から増やす
  var vt = sec.querySelector('.rv-title');
  if (vt) {
    var k = 0;
    // 見出しを1文字ずつに分ける。still=true のときは、動かさずそのまま見せる（見た目は変えない）
    var split = function (still) {
      all('span', vt).forEach(function (row) {
        Array.prototype.slice.call(row.childNodes).forEach(function (node) {
          var text = node.textContent, wrap = document.createDocumentFragment();
          text.split('').forEach(function (ch) {
            var c = document.createElement('span');
            c.className = still ? 'rv-ch is-still' : 'rv-ch';
            c.textContent = ch;
            if (!still) c.style.transitionDelay = (0.2 + k++ * 0.05) + 's';
            wrap.appendChild(c);
          });
          if (node.nodeType === 3) row.replaceChild(wrap, node); else { node.textContent = ''; node.appendChild(wrap); }
        });
      });
    };
    // ロゴの演出でキャッチコピーが見出しへ吸い込まれた場合は、見出しはそのまま見せる（1文字ずつの入場の動きは2回目以降）。
    // ただし金の光が走る演出（1文字ずつ）のため、吸い込みが終わった後に、動かさずに1文字ずつへ分ける（初回も同じ演出になるように）
    if (!window.LF_LOADER_RUN) split(false);
    else setTimeout(function () { split(true); }, 3200);
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

  // /top-a2/：ヒーローより下の動き（相談ボタンがマウスに引き寄せられる）
  if (sec.classList.contains('rf-top')) {
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
