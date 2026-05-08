(function () {
  'use strict';

  var docsify = window.$docsify = window.$docsify || {};
  var existingPlugins = docsify.plugins || [];

  function customPlugin(hook) {
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
