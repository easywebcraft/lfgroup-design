/* トップのヒーローを派手にする追加分（試作 /top-flashy/）。ベースの recruit-fv.js は変えず、切り替え（data-season の変化）を見て演出を足す */
(function () {
  var sec = document.querySelector('.rf-flashy');
  if (!sec) return;
  var media = sec.querySelector('.rf-media');
  if (!media) return;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) return;

  function add(cls, html) {
    var d = document.createElement('div');
    d.className = cls;
    d.setAttribute('aria-hidden', 'true');
    if (html) d.innerHTML = html;
    media.appendChild(d);
    return d;
  }
  var flash = add('ff-flash');
  var streaks = add('ff-streaks', '<i></i><i></i><i></i><i></i><i></i>');
  var spot = add('ff-spot');
  var scroll = document.createElement('span');
  scroll.className = 'ff-scroll';
  scroll.setAttribute('aria-hidden', 'true');
  sec.appendChild(scroll);

  function hit() {
    [flash, streaks, media].forEach(function (el) {
      el.classList.remove('is-hit');
      void el.offsetWidth;
      el.classList.add('is-hit');
    });
    burst(46);
  }
  var last = sec.getAttribute('data-season');
  new MutationObserver(function () {
    var now = sec.getAttribute('data-season');
    if (now !== last) { last = now; hit(); }
  }).observe(sec, { attributes: true, attributeFilter: ['data-season'] });

  /* 金の粒：いつもゆっくり舞い上がり、切り替えの瞬間にまとめて噴き出す */
  var cv = document.createElement('canvas');
  cv.className = 'ff-sparks';
  cv.setAttribute('aria-hidden', 'true');
  media.appendChild(cv);
  var ctx = cv.getContext('2d');
  var W = 0, H = 0, dpr = Math.min(window.devicePixelRatio || 1, 2), ps = [];
  function size() {
    W = cv.clientWidth; H = cv.clientHeight;
    cv.width = W * dpr; cv.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  size();
  window.addEventListener('resize', size);
  function spawn(x, y, vx, vy, life) {
    ps.push({ x: x, y: y, vx: vx, vy: vy, r: 1 + Math.random() * 2.4, life: life, max: life, tw: Math.random() * 6 });
  }
  function burst(n) {
    for (var i = 0; i < n; i++) {
      var a = -Math.PI / 2 + (Math.random() - .5) * 1.8, s = 2 + Math.random() * 6;
      spawn(W * (.35 + Math.random() * .6), H * (.55 + Math.random() * .4), Math.cos(a) * s, Math.sin(a) * s, 70 + Math.random() * 60);
    }
  }
  var running = true, t = 0;
  new IntersectionObserver(function (e) { running = e[0].isIntersecting; if (running) tick(); }).observe(sec);
  function tick() {
    if (!running) return;
    t++;
    if (t % 5 === 0 && ps.length < 140) spawn(Math.random() * W, H + 10, (Math.random() - .5) * .4, -(.5 + Math.random() * 1.1), 200 + Math.random() * 120);
    ctx.clearRect(0, 0, W, H);
    for (var i = ps.length - 1; i >= 0; i--) {
      var p = ps[i];
      p.x += p.vx; p.y += p.vy; p.vx *= .985; p.vy = p.vy * .985 - .01; p.life--;
      if (p.life <= 0 || p.y < -20) { ps.splice(i, 1); continue; }
      var a = Math.min(1, p.life / p.max * 2) * (.55 + .45 * Math.sin(t * .15 + p.tw));
      var g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 4);
      g.addColorStop(0, 'rgba(255,236,190,' + a + ')');
      g.addColorStop(.4, 'rgba(242,182,60,' + a * .6 + ')');
      g.addColorStop(1, 'rgba(242,182,60,0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r * 4, 0, 6.2832); ctx.fill();
    }
    requestAnimationFrame(tick);
  }
  tick();

  /* マウスのスポットライト（PCのみ） */
  if (window.matchMedia('(hover: hover)').matches) {
    sec.addEventListener('mousemove', function (e) {
      var r = sec.getBoundingClientRect();
      sec.style.setProperty('--sx', (e.clientX - r.left) + 'px');
      sec.style.setProperty('--sy', (e.clientY - r.top) + 'px');
      sec.classList.add('is-hover');
    });
    sec.addEventListener('mouseleave', function () { sec.classList.remove('is-hover'); });
  }
})();
