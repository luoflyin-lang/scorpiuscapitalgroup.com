(function () {
  'use strict';

  var docsify = window.$docsify = window.$docsify || {};
  var existingPlugins = docsify.plugins || [];
  var styleInjected = false;

  function injectCustomStyle() {
    if (styleInjected || !document.head) return;
    styleInjected = true;

    var style = document.createElement('style');
    style.id = 'scg-custom-layout-style';
    style.textContent = [
      '.content {',
      '  min-height: 100vh;',
      '  display: flex;',
      '}',
      '.markdown-section#main {',
      '  flex: 1 1 auto;',
      '}',
      '.markdown-section {',
      '  display: flex;',
      '  flex-direction: column;',
      '  min-height: 100%;',
      '}',
      '.markdown-section > footer {',
      '  margin-top: auto;',
      '  padding-top: 32px;',
      '}'
    ].join('\n');
    document.head.appendChild(style);
  }

  function buildFooterHtml(isEnglish) {
    if (isEnglish) {
      return '\n\n<footer>Copyright &copy; 2026 Scorpius Capital Group LLC. All rights reserved. | <a href="#/en/privacy">Privacy Policy</a> | <a href="#/en/terms">Terms of Use</a> | <a href="mailto:support@scorpiuscapitalgroup.com">support@scorpiuscapitalgroup.com</a> | 1209 MOUNTAIN ROAD PL NE, STE N, ALBUQUERQUE, NM 87110, United States</footer>';
    }

    return '\n\n<footer>版权所有 &copy; 2026 Scorpius Capital Group LLC | <a href="#/privacy">隐私政策</a> | <a href="#/terms">服务条款</a> | <a href="mailto:support@scorpiuscapitalgroup.com">support@scorpiuscapitalgroup.com</a> | 1209 MOUNTAIN ROAD PL NE, STE N, ALBUQUERQUE, NM 87110, United States</footer>';
  }

  function isEnglishRoute() {
    return location.hash === '#/en' || location.hash === '#/en/' || location.hash.indexOf('#/en/') === 0;
  }

  function customPlugin(hook) {
    hook.mounted(function () {
      injectCustomStyle();
    });

    hook.afterEach(function (html, next) {
      next(html + buildFooterHtml(isEnglishRoute()));
    });

    hook.doneEach(function () {
      var marker = document.getElementById('docsify-404-redirect');
      if (!marker) return;

      var target = marker.dataset.target || './404.html';
      var from = encodeURIComponent(location.hash || '#/');
      location.replace(target + '?from=' + from);
    });
  }

  docsify.plugins = existingPlugins.concat(customPlugin);
})();
