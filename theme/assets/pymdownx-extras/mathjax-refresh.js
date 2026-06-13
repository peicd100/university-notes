(function () {
  "use strict";

  const MATHJAX_SCRIPT_ID = "peicd-mathjax-runtime";
  const MATHJAX_SRC = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js";

  let refreshToken = 0;
  let queue = Promise.resolve();
  let mathjaxPromise = null;

  function getMathTarget() {
    const target = document.querySelector(".md-content__inner") || document.body;
    if (!target?.querySelector(".arithmatex")) return null;
    return target;
  }

  function loadMathJax() {
    if (window.MathJax?.typesetPromise) {
      return Promise.resolve(window.MathJax);
    }

    if (mathjaxPromise) return mathjaxPromise;

    mathjaxPromise = new Promise((resolve, reject) => {
      const existing = document.getElementById(MATHJAX_SCRIPT_ID);
      if (existing) {
        existing.addEventListener("load", () => resolve(window.MathJax), { once: true });
        existing.addEventListener("error", reject, { once: true });
        return;
      }

      const script = document.createElement("script");
      script.id = MATHJAX_SCRIPT_ID;
      script.src = MATHJAX_SRC;
      script.async = true;
      script.addEventListener("load", () => resolve(window.MathJax), { once: true });
      script.addEventListener("error", reject, { once: true });
      document.head.appendChild(script);
    });

    return mathjaxPromise;
  }

  async function refreshMath() {
    const target = getMathTarget();
    if (!target) return;

    const token = ++refreshToken;
    queue = queue.catch(() => {}).then(async () => {
      if (token !== refreshToken) return;
      const math = await loadMathJax();
      if (!math || typeof math.typesetPromise !== "function") return;
      if (math.startup?.promise) await math.startup.promise;
      if (token !== refreshToken) return;
      math.startup?.output?.clearCache?.();
      math.typesetClear?.([target]);
      math.texReset?.();
      await math.typesetPromise([target]);
    }).catch((error) => {
      console.warn("MathJax load/refresh failed", error);
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
