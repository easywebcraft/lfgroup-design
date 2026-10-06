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

  var fx = sec.getAttribute('data-fx');

  // 案A：4秒ごとに 朝→昼→夕方→夜。時刻と進み具合の線も合わせる
  if (fx === 'a') {
    var STAY = 4000;
    var imgs = all('.rf-media img', sec), times = all('.rf-time', sec), bars = all('.rf-bar li', sec);
    sec.style.setProperty('--stay', STAY / 1000 + 's');
    var n = 0;
    var show = function (i) {
      step(imgs, i);
      times.forEach(function (t, k) { t.classList.toggle('is-on', k === i); });
      bars.forEach(function (b, k) { b.classList.toggle('is-done', k < i); b.classList.remove('is-on'); });
      void bars[i].offsetWidth;
      bars[i].classList.add('is-on');
    };
    // 4枚とも先に読み込み・描画の準備（decode）を済ませてから動かす（初めて出す写真で引っかからないように）
    Promise.all(imgs.map(function (im) { return im.decode ? im.decode().catch(function () {}) : null; })).then(function () {
      imgs[0].classList.remove('is-on');
      show(0);
      setInterval(function () { n = (n + 1) % imgs.length; show(n); }, STAY);
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
})();
