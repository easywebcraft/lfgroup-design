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

  // 季節の粒子：春＝花びら、夏＝立ちのぼる光の粒、秋＝イチョウの葉、冬＝雪。季節が変わると、前の粒は薄れて消え、新しい粒が浮かぶ。
  // ヒーローが画面の外にあるときと、タブを見ていないときは描かない（重くしないため）
  var makeParticles = function (cv, box) {
    var ctx = cv.getContext('2d'), dpr = Math.min(window.devicePixelRatio || 1, 2), W = 0, H = 0, P = [], kind = 0;
    var size = function () { W = cv.clientWidth; H = cv.clientHeight; cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); };
    size();
    window.addEventListener('resize', size);
    var MAX = function () { return W < 768 ? 16 : 34; };
    var make = function (k, anywhere) {
      var rise = k === 1;
      return { k: k, life: 0, x: Math.random() * W,
        y: anywhere ? Math.random() * H : (rise ? H + 20 : -20),
        r: k === 0 ? 5 + Math.random() * 4 : k === 1 ? 1.5 + Math.random() * 2.5 : k === 2 ? 6 + Math.random() * 5 : 1.5 + Math.random() * 2.5,
        vy: rise ? -(0.25 + Math.random() * 0.45) : k === 3 ? 0.5 + Math.random() * 0.9 : 0.6 + Math.random() * 0.8,
        vx: -0.4 + Math.random() * 0.5, a: Math.random() * 6.28, va: -0.03 + Math.random() * 0.06, ph: Math.random() * 6.28 };
    };
    var season = function (k) {
      kind = k;
      for (var n = 0; n < MAX(); n++) P.push(make(k, true));  // 新しい季節の粒を、画面のあちこちに薄く浮かべる
    };
    var draw = function (p) {
      var al = Math.max(0, Math.min(1, p.life));
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.a);
      if (p.k === 0) { ctx.fillStyle = 'rgba(255, 218, 230,' + (.85 * al) + ')'; ctx.beginPath(); ctx.ellipse(0, 0, p.r, p.r * .58, 0, 0, 6.28); ctx.fill(); }
      else if (p.k === 1) {
        var tw = .55 + .45 * Math.sin(p.ph * 3), g = ctx.createRadialGradient(0, 0, 0, 0, 0, p.r * 4);
        g.addColorStop(0, 'rgba(255, 246, 214,' + (.9 * al * tw) + ')'); g.addColorStop(1, 'rgba(255, 246, 214, 0)');
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, p.r * 4, 0, 6.28); ctx.fill();
      } else if (p.k === 2) {
        ctx.fillStyle = 'rgba(232, 176, 48,' + (.9 * al) + ')';
        ctx.beginPath(); ctx.moveTo(0, p.r * .5); ctx.quadraticCurveTo(-p.r, -p.r * .2, -p.r * .55, -p.r * .8);
        ctx.quadraticCurveTo(0, -p.r * .45, p.r * .55, -p.r * .8); ctx.quadraticCurveTo(p.r, -p.r * .2, 0, p.r * .5); ctx.fill();
      } else { ctx.fillStyle = 'rgba(255, 255, 255,' + (.85 * al) + ')'; ctx.beginPath(); ctx.arc(0, 0, p.r, 0, 6.28); ctx.fill(); }
      ctx.restore();
    };
    var tick = function () {
      requestAnimationFrame(tick);
      if (document.hidden || box.getBoundingClientRect().bottom < 0) return;
      ctx.clearRect(0, 0, W, H);
      var live = 0;
      P = P.filter(function (p) {
        p.ph += .02; p.a += p.va;
        p.x += p.vx + Math.sin(p.ph) * (p.k === 3 ? .25 : .5);
        p.y += p.vy;
        p.life += p.k === kind ? .02 : -.02;  // 今の季節の粒は浮かび、前の季節の粒は薄れる
        if (p.life > 1) p.life = 1;
        var out = p.y > H + 30 || p.y < -30 || p.x < -30 || p.x > W + 30;
        if (p.k !== kind && p.life <= 0) return false;
        if (out) { if (p.k !== kind) return false; Object.assign(p, make(p.k, false), { life: 1 }); }
        if (p.k === kind) live++;
        draw(p);
        return true;
      });
      if (live < MAX() && Math.random() < .3) P.push(Object.assign(make(kind, false), { life: 1 }));
    };
    requestAnimationFrame(tick);
    return { season: season };
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
    // /top-a2/：季節の名前（パタパタ入れ替わる英字）と、季節の粒子（花びら・光・イチョウ・雪）
    var label = sec.querySelector('.rv-season'), NAMES = ['SPRING', 'SUMMER', 'AUTUMN', 'WINTER'];
    var particles = sec.querySelector('.rv-particles') ? makeParticles(sec.querySelector('.rv-particles'), sec) : null;
    var mark = function (i) {
      sec.setAttribute('data-season', i);  // 今の季節（0春 1夏 2秋 3冬）
      if (particles) particles.season(i);
      if (label) {
        label.innerHTML = '<small>0' + (i + 1) + '</small>' + NAMES[i].split('').map(function (ch, k) {
          return '<span style="animation-delay:' + (k * 0.05) + 's">' + ch + '</span>';
        }).join('');
      }
      if (!bars.length) return;
      bars.forEach(function (b, k) { b.classList.toggle('is-done', k < i); b.classList.remove('is-on'); });
      void bars[i].offsetWidth;
      bars[i].classList.add('is-on');
    };
    var show = function (i) {
      mark(i);
      step(imgs, i);
      if (sweep && !sec.classList.contains('rf-top')) { sweep.classList.remove('is-run'); void sweep.offsetWidth; sweep.classList.add('is-run'); }  // A2：金の光の帯（切り替えのたびに。/top-a2/ では外した 2026-10-07）
      times.forEach(function (t, k) { t.classList.toggle('is-on', k === i); });
    };
    // 4枚とも先に読み込み・描画の準備（decode）を済ませてから動かす（初めて出す写真で引っかからないように）
    Promise.all(imgs.map(function (im) { return im.decode ? im.decode().catch(function () {}) : null; })).then(function () {
      // ロゴの演出のあとは、最初の写真がもう見えているので現れ直させない（春がぼやけ直して見えるため）
      if (!window.LF_LOADER_RUN) { imgs[0].classList.remove('is-on'); show(0); } else mark(0);
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
