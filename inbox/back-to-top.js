(function () {
  'use strict';

  if (window.__SCORPIUS_BACK_TO_TOP__) return;
  window.__SCORPIUS_BACK_TO_TOP__ = true;

  var BUTTON_CLASS = 'progress-wrap';
  var ACTIVE_CLASS = 'active-progress';
  var SVG_PATH_SELECTOR = '.progress-circle path';
  var SHOW_OFFSET = 150;

  function injectStyle() {
    if (document.getElementById('docsify-backtotop-style')) return;

    var style = document.createElement('style');
    style.id = 'docsify-backtotop-style';
    style.textContent = `
      .${BUTTON_CLASS} {
        position: fixed;
        right: 30px;
        bottom: 30px;
        width: 46px;
        height: 46px;
        border-radius: 999px;
        cursor: pointer;
        z-index: 9999;
        opacity: 0;
        visibility: hidden;
        transform: translateY(20px);
        transition: all 0.28s ease;
        background: rgba(17, 17, 17, 0.88);
        box-shadow: inset 0 0 0 1px rgba(198, 169, 107, 0.25);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
      }

      .${BUTTON_CLASS}.${ACTIVE_CLASS} {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
      }

      .${BUTTON_CLASS}::after {
        content: '↑';
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #c6a96b;
        font-size: 18px;
        font-weight: 700;
        line-height: 1;
        z-index: 2;
        transition: transform 0.2s ease, color 0.2s ease;
      }

      .${BUTTON_CLASS}:hover::after {
        transform: translateY(-2px);
        color: #d6ba7d;
      }

      .${BUTTON_CLASS} svg {
        width: 100%;
        height: 100%;
        transform: rotate(-90deg);
      }

      .${BUTTON_CLASS} svg path {
        fill: none;
      }

      .${BUTTON_CLASS} svg.progress-circle path {
        stroke: #c6a96b;
        stroke-width: 4;
        box-sizing: border-box;
        transition: stroke-dashoffset 0.08s linear;
      }

      @media (max-width: 768px) {
        .${BUTTON_CLASS} {
          right: 18px;
          bottom: 18px;
          width: 42px;
          height: 42px;
        }

        .${BUTTON_CLASS}::after {
          font-size: 16px;
        }
      }
    `;
    document.head.appendChild(style);
  }

  function createButton() {
    var existing = document.querySelector('.' + BUTTON_CLASS);
    if (existing) return existing;

    var button = document.createElement('div');
    button.className = BUTTON_CLASS + ' cursor-pointer';
    button.setAttribute('role', 'button');
    button.setAttribute('aria-label', 'Back to top');
    button.innerHTML = `
      <svg class="progress-circle" viewBox="-1 -1 102 102" aria-hidden="true">
        <path d="M50,1 a49,49 0 0,1 0,98 a49,49 0 0,1 0,-98"></path>
      </svg>
    `;
    document.body.appendChild(button);
    return button;
  }

  function getScrollTop() {
    return window.pageYOffset ||
      document.documentElement.scrollTop ||
      document.body.scrollTop ||
      0;
  }

  function getScrollHeight() {
    var doc = document.documentElement;
    var body = document.body;
    var fullHeight = Math.max(
      body.scrollHeight, doc.scrollHeight,
      body.offsetHeight, doc.offsetHeight,
      body.clientHeight, doc.clientHeight
    );
    return Math.max(fullHeight - window.innerHeight, 0);
  }

  function smoothToTop() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }

  function init() {
    if (!document.body) return;

    injectStyle();
    var button = createButton();
    var progressPath = button.querySelector(SVG_PATH_SELECTOR);
    if (!progressPath) return;

    var pathLength = progressPath.getTotalLength();
    progressPath.style.strokeDasharray = pathLength + ' ' + pathLength;
    progressPath.style.strokeDashoffset = pathLength;
    progressPath.getBoundingClientRect();

    var ticking = false;

    function update() {
      var scrollTop = getScrollTop();
      var scrollHeight = getScrollHeight();

      if (scrollTop > SHOW_OFFSET) {
        button.classList.add(ACTIVE_CLASS);
      } else {
        button.classList.remove(ACTIVE_CLASS);
      }

      var progress = pathLength;
      if (scrollHeight > 0) {
        progress = pathLength - (scrollTop * pathLength / scrollHeight);
      }
      progressPath.style.strokeDashoffset = progress;

      ticking = false;
    }

    function requestUpdate() {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(update);
    }

    button.addEventListener('click', function (event) {
      event.preventDefault();
      smoothToTop();
    }, { passive: false });

    window.addEventListener('scroll', requestUpdate, { passive: true });
    window.addEventListener('resize', requestUpdate, { passive: true });
    window.addEventListener('hashchange', function () {
      setTimeout(requestUpdate, 60);
    });

    setTimeout(requestUpdate, 60);
    setTimeout(requestUpdate, 300);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
