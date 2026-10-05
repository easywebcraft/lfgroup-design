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

    // 切り替え方は1周ごとに変える（見比べる用の試作）。中身は season.css の data-fx
    var FX = [['diag', '斜めのワイプ（今の方式）'], ['fade', 'A ゆっくりクロスフェード'], ['soft', 'B やわらかいワイプ'],
              ['white', 'C 白く溶けて変わる'], ['slit', 'D 縦のスリット']];
    var fx = 0;
    var fxLabel = document.createElement('p');
    fxLabel.className = 'fv-fx';
    fxLabel.setAttribute('aria-live', 'polite');
    var setFx = function (n) {
      fx = n % FX.length;
      box.dataset.fx = FX[fx][0];
      fxLabel.textContent = '切り替え：' + FX[fx][1];
    };
    // ?fx=fade のように URL で始める切り替え方を選べる（見たい方式からすぐ確かめる用）
    var want = new URLSearchParams(location.search).get('fx');
    setFx(Math.max(0, FX.findIndex(function (f) { return f[0] === want; })));
    fv.appendChild(fxLabel);

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
      // 次の写真を、今の切り替え方の「待機中」の状態にすぐ合わせる（切り替え方が変わった直後は、
      // 前の方式の待機中の状態のまま残っていて、そこから始めると動かずにパッと出てしまう）
      next.style.transition = 'none';
      void next.offsetWidth;
      next.style.transition = '';
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
      if (!paused && !document.hidden) timer = setInterval(function () {
        var next = (cur + 1) % imgs.length;
        if (next === 0) setFx(fx + 1);  // 冬→春に戻るところから、次の切り替え方にする
        show(next);
      }, STAY);
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
