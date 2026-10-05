  // ファーストビューの写真を、春→夏→秋→冬→春…と切り替える試作（/season/ だけで読み込む。見た目は season.css）
  (function () {
    var fv = document.querySelector('.fv');
    var box = fv && fv.querySelector('.fv-photo');
    if (!box) return;
    var imgs = Array.prototype.slice.call(box.querySelectorAll('img'));
    var names = ['Spring', 'Summer', 'Autumn', 'Winter'];
    var labels = ['春', '夏', '秋', '冬'];
    var STAY = 6000;  // 1枚を見せる時間
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var cur = 0, timer = null, paused = reduce;

    // ボタン：季節を選ぶと、その写真に切り替える。一時停止（動きを減らす設定の端末では、最初から止めておく）
    var bar = document.createElement('div');
    bar.className = 'fv-season';
    bar.setAttribute('role', 'group');
    bar.setAttribute('aria-label', '季節の写真');
    var dots = imgs.map(function (img, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = names[i];
      b.setAttribute('aria-label', labels[i] + 'の写真を見る');
      b.addEventListener('click', function () { show(i); restart(); });
      bar.appendChild(b);
      return b;
    });
    var pause = document.createElement('button');
    pause.type = 'button';
    pause.className = 'fs-pause';
    bar.appendChild(pause);
    var setPause = function (p) {
      paused = p;
      pause.setAttribute('aria-label', p ? '写真の切り替えを再生する' : '写真の切り替えを一時停止する');
      pause.innerHTML = p ? '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 0.5 9.5 5 1.5 9.5z"/></svg>'
                          : '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 0.5h2.5v9H1.5zM6 0.5h2.5v9H6z"/></svg>';
      restart();
    };
    pause.addEventListener('click', function () { setPause(!paused); });
    fv.appendChild(bar);

    var mark = function () { dots.forEach(function (b, i) { b.setAttribute('aria-current', i === cur ? 'true' : 'false'); }); };
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
      mark();
    };
    var restart = function () {
      clearInterval(timer);
      if (!paused && !document.hidden) timer = setInterval(function () { show((cur + 1) % imgs.length); }, STAY);
    };
    // タブを見ていない間は止める（戻ったときに何枚も飛ばないように）
    document.addEventListener('visibilitychange', restart);

    // 夏・秋・冬の写真は、最初の画面が出てから読み込む（最初の表示を遅くしないため）
    var loadRest = function () {
      imgs.forEach(function (img, i) {
        if (i && img.dataset.src) { img.src = img.dataset.src; img.removeAttribute('data-src'); }
        if (i) img.classList.add('is-ready');
      });
    };
    // 最初の演出とズーム（main.js）が終わってから切り替えを始める
    var start = function () {
      loadRest();
      setTimeout(function () {
        imgs[0].classList.add('is-ready');
        mark();
        setPause(paused);
      }, 1800);
    };
    mark();
    setPause(true);  // 始まるまでは止めておく
    paused = reduce;
    var wait = setInterval(function () {
      if (fv.classList.contains('is-loaded')) { clearInterval(wait); start(); }
    }, 200);
  })();
