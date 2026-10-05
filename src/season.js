  // トップのファーストビューの写真を、春→夏→秋→冬→春…と切り替える（見た目は season.css。トップ以外では何もしない）
  (function () {
    var fv = document.querySelector('.fv');
    var box = fv && fv.querySelector('.fv-photo');
    if (!box) return;
    var imgs = Array.prototype.slice.call(box.querySelectorAll('img'));
    var STAY = 6000;  // 1枚を見せる時間
    var FIRST = 3500; // 最初の演出が終わってから、最初に切り替えるまで（春は演出の間も見えているので、ほかより短くする）
    // 最後の写真から最初の写真へ戻るときは、白をはさんでゆっくり切り替える（一区切りが分かるように。見た目は season.css の .is-wrap）。
    // その分（白へ消える1.6秒＋白0.3秒）だけ、最初の写真を見せる時間をのばす
    var WRAP = 1900, WRAP_END = 3800;
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var cur = 0, timer = null, started = false;

    // 季節の名前のボタン・一時停止ボタンは、2026-10-05 お客さまの希望で外した（動きを減らす設定の端末では切り替えない）

    var show = function (i) {
      if (i === cur) return;
      var next = imgs[i];
      // まだ読み込めていない写真は飛ばさず、読み込めてから切り替える
      if (!next.complete || !next.naturalWidth) { next.addEventListener('load', function () { show(i); }, { once: true }); return; }
      var wrap = i === 0;
      box.classList.toggle('is-wrap', wrap);
      imgs.forEach(function (img) { img.classList.remove('is-prev'); });
      imgs[cur].classList.add('is-prev');
      imgs[cur].classList.remove('is-show');
      next.classList.add('is-show');
      var prev = imgs[cur];
      setTimeout(function () {
        if (!prev.classList.contains('is-show')) prev.classList.remove('is-prev');
        if (wrap) box.classList.remove('is-wrap');
      }, wrap ? WRAP_END : 2700);
      cur = i;
    };
    // first：次に切り替えるまでの時間（省略すると STAY）。そのあとは STAY ごと（最初の写真へ戻ったときだけ WRAP 長く）
    var restart = function (first) {
      clearTimeout(timer);
      if (!started || reduce || document.hidden) return;  // 最初の演出が終わるまでは動かさない
      var tick = function (ms) {
        timer = setTimeout(function () {
          var i = (cur + 1) % imgs.length;
          show(i);
          tick(STAY + (i === 0 ? WRAP : 0));
        }, ms);
      };
      tick(typeof first === 'number' ? first : STAY);
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
        started = true;
        restart(FIRST - 1800);
      }, 1800);
    };
    var wait = setInterval(function () {
      if (fv.classList.contains('is-loaded')) { clearInterval(wait); start(); }
    }, 200);
  })();
