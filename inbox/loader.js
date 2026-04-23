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

    hook.beforeEach(function (content) {
      if (!state.hasPlayedOnce) {
        state.hasPlayedOnce = true;
        state.shouldFinishOnce = true;
        start();
      }
      return content;
    });

    hook.doneEach(function () {
      if (state.shouldFinishOnce) {
        state.shouldFinishOnce = false;
        finish();
      }
    });
  }

  docsify.plugins = [].concat(docsify.plugins || [], install);
})();
