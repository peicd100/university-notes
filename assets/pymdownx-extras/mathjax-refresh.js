(function () {
  "use strict";

  let refreshToken = 0;
  let queue = Promise.resolve();

  function getMathTarget() {
    const target = document.querySelector(".md-content__inner") || document.body;
    if (!target?.querySelector(".arithmatex")) return null;
    return target;
  }

  function refreshMath() {
    const target = getMathTarget();
    const math = window.MathJax;
    if (!target || !math || typeof math.typesetPromise !== "function") return;

    const token = ++refreshToken;
    queue = queue.catch(() => {}).then(async () => {
      if (token !== refreshToken) return;
      if (math.startup?.promise) await math.startup.promise;
      if (token !== refreshToken) return;
      math.startup?.output?.clearCache?.();
      math.typesetClear?.([target]);
      math.texReset?.();
      await math.typesetPromise([target]);
    }).catch((error) => {
      console.warn("MathJax refresh failed", error);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", refreshMath, { once: true });
  } else {
    refreshMath();
  }

  if (window.document$?.subscribe) {
    window.document$.subscribe(refreshMath);
  }
})();
