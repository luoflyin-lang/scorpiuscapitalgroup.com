(function () {
  'use strict';

  var global = window;
  var docsify = global.$docsify = global.$docsify || {};
  var options = Object.assign({
    // 只影响“动画观感”，不会影响真实资源下载速度
    // 想更有“加载感”就把 minTime 再加一点，比如 600~700
    // 想更利落就降到 350~450
    minTime: 520,
    ghostTime: 140,
    trickleMax: 94,
    autoStart: true
  }, global.$docsifyScorpiusLoader || {});

  var state = {
    bootstrapped: false,
    initialDone: false,
    status: 'idle',
    progress: 0,
    startTime: 0,
    lastTime: 0,
    rafId: 0,
    finishTimer: 0,
    preloader: null,
    pace: null,
    paceProgress: null
  };

  var styleText = [
    '/* Scorpius original-style loader for Docsify */',
    '.pace {',
    '  pointer-events: none;',
    '  -webkit-user-select: none;',
    '  -moz-user-select: none;',
    '  -ms-user-select: none;',
    '  user-select: none;',
    '  z-index: 99999999999999;',
    '  position: fixed;',
    '  margin: auto;',
    '  top: 0;',
    '  left: 0;',
    '  right: 0;',
    '  bottom: 0;',
    '  width: 400px;',
    '  border: 0;',
    '  height: 1px;',
    '  overflow: hidden;',
    '  background: rgba(212, 184, 120, 0.16);',
    '  -webkit-transition: opacity 0.28s ease;',
    '  -o-transition: opacity 0.28s ease;',
    '  transition: opacity 0.28s ease;',
    '}',
    '.pace .pace-progress {',
    '  -webkit-transform: translate3d(0, 0, 0);',
    '  transform: translate3d(0, 0, 0);',
    '  max-width: 300px;',
    '  z-index: 99999999999999;',
    '  display: block;',
    '  position: absolute;',
    '  top: 0;',
    '  right: 100%;',
    '  height: 100%;',
    '  width: 100%;',
    '  background: #c6a96b;',
    '}',
    '.pace.pace-inactive {',
    '  width: 100vw;',
    '  opacity: 0;',
    '}',
    '.pace.pace-inactive .pace-progress {',
    '  max-width: 100vw;',
    '}',
    '#preloader {',
    '  width: 100%;',
    '  height: 100vh;',
    '  overflow: hidden;',
    '  position: fixed;',
    '  z-index: 9999999;',
    '  inset: 0;',
    '}',
    '#preloader:after,',
    '#preloader:before {',
    "  content: '';",
    '  position: fixed;',
    '  left: 0;',
    '  height: 50%;',
    '  width: 100%;',
    '  background: #111111;',
    '  -webkit-transition-timing-function: cubic-bezier(0.19, 1, 0.22, 1);',
    '  -o-transition-timing-function: cubic-bezier(0.19, 1, 0.22, 1);',
    '  transition-timing-function: cubic-bezier(0.19, 1, 0.22, 1);',
    '}',
    '#preloader:before { top: 0; }',
    '#preloader:after { bottom: 0; }',
    '#preloader.isdone {',
    '  visibility: hidden;',
    '  -webkit-transition-delay: 0s;',
    '  -o-transition-delay: 0s;',
    '  transition-delay: 0s;',
    '}',
    '#preloader.isdone:after,',
    '#preloader.isdone:before {',
    '  height: 0;',
    '  -webkit-transition: all 0.42s cubic-bezier(1, 0, 0.55, 1);',
    '  -o-transition: all 0.42s cubic-bezier(1, 0, 0.55, 1);',
    '  transition: all 0.42s cubic-bezier(1, 0, 0.55, 1);',
    '  -webkit-transition-delay: 0s;',
    '  -o-transition-delay: 0s;',
    '  transition-delay: 0s;',
    '}',
    '.loading-text {',
    '  font-size: 40px;',
    '  font-weight: 400;',
    '  letter-spacing: 4px;',
    '  position: absolute;',
    '  top: calc(50% - 30px);',
    '  left: 50%;',
    '  -webkit-transform: translate(-50%, -50%);',
    '  -ms-transform: translate(-50%, -50%);',
    '  transform: translate(-50%, -50%);',
    '  color: #c6a96b;',
    "  font-family: 'Oswald', sans-serif;",
    '  z-index: 9999;',
    '}',
    '.loading-text.isdone {',
    '  top: 50%;',
    '  opacity: 0;',
    '  -webkit-transition: all 0.32s cubic-bezier(0.19, 1, 0.22, 1);',
    '  -o-transition: all 0.32s cubic-bezier(0.19, 1, 0.22, 1);',
    '  transition: all 0.32s cubic-bezier(0.19, 1, 0.22, 1);',
    '  -webkit-transition-delay: 0s;',
    '  -o-transition-delay: 0s;',
    '  transition-delay: 0s;',
    '}',
    '@media (max-width: 480px) {',
    '  .pace { width: calc(100vw - 48px); }',
    '}'
  ].join('\n');

  function injectStyle() {
    if (document.getElementById('scg-original-loader-style')) return;
    var style = document.createElement('style');
    style.id = 'scg-original-loader-style';
    style.textContent = styleText;
    document.head.appendChild(style);
  }

  function ensureDom() {
    if (!document.body) return;

    state.preloader = document.getElementById('preloader');
    if (!state.preloader) {
      state.preloader = document.createElement('div');
      state.preloader.id = 'preloader';
      document.body.insertBefore(state.preloader, document.body.firstChild || null);
    }

    state.pace = document.querySelector('.pace.scg-original-loader');
    if (!state.pace) {
      state.pace = document.createElement('div');
      state.pace.className = 'pace pace-active scg-original-loader';
      state.pace.innerHTML = '<div class="pace-progress"><div class="pace-progress-inner"></div></div><div class="pace-activity"></div>';
      document.body.insertBefore(state.pace, document.body.firstChild || null);
    }

    state.paceProgress = state.pace.querySelector('.pace-progress');
  }

  function setBodyRunning(isRunning) {
    if (!document.body) return;
    document.body.classList.toggle('pace-running', !!isRunning);
    document.body.classList.toggle('pace-done', !isRunning);
  }

  function renderProgress(value) {
    state.progress = Math.max(0, Math.min(100, value));
    if (!state.paceProgress) return;

    var transform = 'translate3d(' + state.progress + '%, 0, 0)';
    state.paceProgress.style.webkitTransform = transform;
    state.paceProgress.style.msTransform = transform;
    state.paceProgress.style.transform = transform;
    state.paceProgress.setAttribute('data-progress-text', (state.progress | 0) + '%');

    var display = state.progress >= 100 ? '99' : (state.progress < 10 ? '0' : '') + (state.progress | 0);
    state.paceProgress.setAttribute('data-progress', display);
  }

  function clearTimers() {
    if (state.rafId) {
      cancelAnimationFrame(state.rafId);
      state.rafId = 0;
    }
    if (state.finishTimer) {
      clearTimeout(state.finishTimer);
      state.finishTimer = 0;
    }
  }

  function tick(now) {
    if (state.status !== 'running') return;

    if (!state.lastTime) state.lastTime = now;
    var dt = now - state.lastTime;
    state.lastTime = now;

    var p = state.progress;
    var inc;

    // 视觉上慢一点，但不阻塞真实加载
    if (p < 10) inc = dt * 0.12;
    else if (p < 28) inc = dt * 0.075;
    else if (p < 55) inc = dt * 0.038;
    else if (p < 78) inc = dt * 0.017;
    else inc = dt * 0.006;

    renderProgress(Math.min(options.trickleMax, p + inc));
    state.rafId = requestAnimationFrame(tick);
  }

  function start() {
    // 只允许首次进入站点时跑一次
    if (state.initialDone || state.status === 'running' || state.status === 'finishing') return;

    injectStyle();
    ensureDom();
    if (!state.preloader || !state.pace || !state.paceProgress) return;

    clearTimers();
    state.status = 'running';
    state.startTime = performance.now();
    state.lastTime = 0;

    state.preloader.classList.remove('isdone');
    state.pace.classList.remove('pace-inactive');
    state.pace.classList.add('pace-active');

    setBodyRunning(true);
    renderProgress(0);

    state.rafId = requestAnimationFrame(tick);
  }

  function finish() {
    if (!state.preloader || !state.pace || !state.paceProgress) return;
    if (state.status !== 'running') return;

    state.status = 'finishing';
    clearTimers();
    renderProgress(100);
    state.preloader.classList.add('isdone');

    var elapsed = performance.now() - state.startTime;
    var finishDelay = Math.max(options.ghostTime, Math.max(options.minTime - elapsed, 0));

    state.finishTimer = setTimeout(function () {
      state.pace.classList.remove('pace-active');
      state.pace.classList.add('pace-inactive');
      setBodyRunning(false);
      state.status = 'idle';
      state.initialDone = true;
    }, finishDelay);
  }

  function bootstrap() {
    if (state.bootstrapped) return;
    state.bootstrapped = true;

    injectStyle();
    ensureDom();

    if (options.autoStart) start();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap, { once: true });
  } else {
    bootstrap();
  }

  function install(hook) {
    hook.mounted(function () {
      bootstrap();
    });

    // 这里只在首次加载完成时结束一次
    // 不再在站内切换页面时重新 start()
    hook.doneEach(function () {
      if (!state.initialDone) {
        finish();
      }
    });
  }

  docsify.plugins = [].concat(docsify.plugins || [], install);
})();
