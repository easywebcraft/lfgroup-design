  // トップのファーストビューの写真を、春→夏→秋→冬→春…と切り替える（見た目は season.css。トップ以外では何もしない）
  (function () {
    var fv = document.querySelector('.fv');
    var box = fv && fv.querySelector('.fv-photo');
    if (!box) return;
    var imgs = Array.prototype.slice.call(box.querySelectorAll('img'));
    var STAY = 6000;  // 1枚を見せる時間
    var FIRST = 3500; // 最初の演出が終わってから、最初に切り替えるまで（春は演出の間も見えているので、ほかより短くする）
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var cur = 0, timer = null, paused = reduce;

    // 一時停止ボタン（自動で切り替わり続けるので、止められるようにする。動きを減らす設定の端末では、最初から止めておく）。
    // 季節の名前のボタンは、2026-10-05 お客さまの希望で外した
    var pause = document.createElement('button');
    pause.type = 'button';
    pause.className = 'fv-season';
    var setPause = function (p, first) {
      paused = p;
      pause.setAttribute('aria-label', p ? '写真の切り替えを再生する' : '写真の切り替えを一時停止する');
      pause.innerHTML = p ? '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 0.5 9.5 5 1.5 9.5z"/></svg>'
                          : '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 0.5h2.5v9H1.5zM6 0.5h2.5v9H6z"/></svg>';
      restart(first);
    };
    pause.addEventListener('click', function () { setPause(!paused); });
    fv.appendChild(pause);

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
    };
    // first：次に切り替えるまでの時間（省略すると STAY）。そのあとは STAY ごと
    var restart = function (first) {
      clearTimeout(timer);
      clearInterval(timer);
      if (paused || document.hidden) return;
      var next = function () { show((cur + 1) % imgs.length); };
      timer = setTimeout(function () { next(); timer = setInterval(next, STAY); }, typeof first === 'number' ? first : STAY);
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
          setPause(paused, FIRST - 1800);
      }, 1800);
    };
    setPause(true);  // 始まるまでは止めておく
    paused = reduce;
    var wait = setInterval(function () {
      if (fv.classList.contains('is-loaded')) { clearInterval(wait); start(); }
    }, 200);
  })();
