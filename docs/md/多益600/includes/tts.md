<!--
整段放入 tts.md（snippets）即可。

新增功能：
1) 反白任何文字 → 浮動播放鍵出現 → 點了朗讀反白內容（播放時三角形→方塊）
2) 浮動工具同時顯示繁中翻譯（Google gtx endpoint，無 key）
-->

<style>
/* wrapper：文字與按鈕分開，避免 st/nd 斷行跑位 */
.tts-wrap{
  display: inline-flex;
  align-items: center;
  gap: 10px;                 /* 可改：按鈕與文字距離 */
}

.tts{ display: inline; }

/* 透明按鈕：顏色跟隨主題 */
.tts-btn{
  background: transparent;
  border: 0;
  font: inherit;

  width: 44px;               /* 可改：點擊區寬 */
  height: 44px;              /* 可改：點擊區高 */
  padding: 0;

  cursor: pointer;
  line-height: 1;

  display: inline-grid;
  place-items: center;
  position: relative;

  color: var(--md-primary-fg-color, currentColor);
  touch-action: manipulation;
}

.tts-btn:hover{
  color: var(--md-accent-fg-color, var(--md-primary-fg-color, currentColor));
}

.tts-btn[aria-pressed="true"]{
  color: var(--md-accent-fg-color, var(--md-primary-fg-color, currentColor));
  opacity: 0.85;
}

.tts-btn:focus-visible{
  outline: 2px solid var(--md-accent-fg-color, currentColor);
  outline-offset: 3px;
  border-radius: 10px;
}

/* 播放：三角形 */
.tts-btn[data-state="play"]::before{
  content: "";
  display: block;
  width: 0;
  height: 0;

  border-style: solid;
  border-width: 9px 0 9px 14px;   /* 可改：三角形比例 */
  border-color: transparent transparent transparent currentColor;
  transform: translateX(1px);
}

/* 停止：方塊 */
.tts-btn[data-state="stop"]::before{
  content: "";
  display: block;
  width: 16px;                    /* 可改：方塊大小 */
  height: 16px;
  background: currentColor;
  border-radius: 3px;
}

/* Voice bar */
#tts-topbar{
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 10px 12px;
  margin: 12px 0 16px;

  border: 1px solid var(--md-default-fg-color--lightest, rgba(0,0,0,.12));
  border-radius: 12px;
  background: var(--md-default-bg-color, rgba(255,255,255,.95));
  font-size: 14px;
}

#tts-voice-picker{
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--md-default-fg-color--lightest, rgba(0,0,0,.2));
  background: transparent;
  color: inherit;
  font: inherit;
  max-width: min(720px, 85vw);
}

#tts-voice-hint{
  color: var(--md-default-fg-color--light, #777);
  font-size: 12px;
}

/* 你 mkdocs.yml 的 scheme 是 slate（不是 dracula） */
[data-md-color-scheme="slate"] #tts-voice-picker{
  background-color: #1e1e1e;
  color: #fff;
  border-color: rgba(255,255,255,.25);
}
[data-md-color-scheme="slate"] #tts-voice-picker option{
  background-color: #1e1e1e;
  color: #fff;
}

/* 手機按鈕加大 */
@media (max-width: 600px){
  .tts-btn{ width: 52px; height: 52px; }
  .tts-btn[data-state="play"]::before{ border-width: 10px 0 10px 16px; }
  .tts-btn[data-state="stop"]::before{ width: 18px; height: 18px; }
}

/* =========================
   反白浮動工具（播放 + 翻譯）
   ========================= */
#tts-selection-pop{
  position: fixed;
  z-index: 9999;
  display: none;

  padding: 10px 12px;
  border-radius: 14px;

  background: var(--md-default-bg-color, rgba(20,20,20,.92));
  border: 1px solid var(--md-default-fg-color--lightest, rgba(255,255,255,.18));
  box-shadow: 0 10px 30px rgba(0,0,0,.25);

  /* 內容排列：左按鈕、右翻譯文字 */
  display: none;
  align-items: center;
  gap: 12px;
  max-width: min(520px, 92vw);
}

#tts-selection-zh{
  font-size: 13px;
  line-height: 1.35;
  color: var(--md-default-fg-color, #ddd);
  word-break: break-word;
  max-width: min(440px, 78vw);
}

#tts-selection-zh .muted{
  opacity: .75;
}
</style>

<script>
(function () {
  let currentBtn = null;

  /* 可改：預設語音 */
  const DEFAULT_LANG = "en-US";
  const DEFAULT_NAME_INCLUDES = "Google US English";

  /* 可改：反白朗讀設定 */
  const SELECTION_MAX_CHARS = 500;     // 太長不顯示
  const SELECTION_LANG = "en-US";      // 反白朗讀語言（實際 voice 仍會用上方選到的）
  const TRANSLATE_TO = "zh-TW";        // 中文翻譯語言
  const TRANSLATE_FROM = "en";         // 來源語言（你主要是英文單字/句子；想自動可改成 "auto" 但成功率較不穩）

  const translateCache = new Map();    // 翻譯快取（避免一直打 API）

  function supported() {
    return ("speechSynthesis" in window) && ("SpeechSynthesisUtterance" in window);
  }

  function stop() {
    try { speechSynthesis.cancel(); } catch (_) {}
    if (currentBtn) {
      currentBtn.setAttribute("data-state", "play");
      currentBtn.setAttribute("aria-pressed", "false");
      currentBtn = null;
    }
  }

  function getMainContainer() {
    return (
      document.querySelector(".md-content .md-content__inner") ||
      document.querySelector("main") ||
      document.body
    );
  }

  function ensureTopBar() {
    let bar = document.getElementById("tts-topbar");
    if (bar) return bar;

    bar = document.createElement("div");
    bar.id = "tts-topbar";

    const label = document.createElement("span");
    label.textContent = "Voice:";
    label.style.color = "#555";

    const sel = document.createElement("select");
    sel.id = "tts-voice-picker";

    const hint = document.createElement("span");
    hint.id = "tts-voice-hint";

    bar.appendChild(label);
    bar.appendChild(sel);
    bar.appendChild(hint);

    const container = getMainContainer();
    const h1 = container.querySelector("h1");
    if (h1 && h1.parentNode) h1.insertAdjacentElement("afterend", bar);
    else container.insertBefore(bar, container.firstChild);

    return bar;
  }

  function populateVoicesAndSelectDefault() {
    const sel = document.getElementById("tts-voice-picker");
    const hint = document.getElementById("tts-voice-hint");
    if (!sel) return;

    const voices = speechSynthesis.getVoices() || [];
    sel.innerHTML = "";

    voices.forEach((v, idx) => {
      const opt = document.createElement("option");
      opt.value = String(idx);
      opt.textContent = `${v.lang} — ${v.name}${v.localService ? "" : " (cloud)"}`;
      sel.appendChild(opt);
    });

    hint.textContent = voices.length ? `Detected ${voices.length} voices.` : "No voices found.";
    if (!voices.length) return;

    const needle = DEFAULT_NAME_INCLUDES.toLowerCase();

    let idx = voices.findIndex(v =>
      (v.lang || "").toLowerCase() === DEFAULT_LANG.toLowerCase() &&
      (v.name || "").toLowerCase().includes(needle)
    );
    if (idx < 0) idx = voices.findIndex(v => (v.name || "").toLowerCase().includes(needle));
    if (idx < 0) idx = voices.findIndex(v => (v.lang || "").toLowerCase() === DEFAULT_LANG.toLowerCase());
    if (idx < 0) idx = voices.findIndex(v => (v.lang || "").toLowerCase().startsWith("en"));
    if (idx < 0) idx = 0;

    sel.value = String(idx);
  }

  function getSelectedVoice() {
    const sel = document.getElementById("tts-voice-picker");
    const voices = speechSynthesis.getVoices() || [];
    if (!sel || !voices.length) return null;
    const idx = parseInt(sel.value, 10);
    return Number.isFinite(idx) ? voices[idx] : null;
  }

  function speak(text, preferredLang, btn) {
    if (!supported()) return;

    const t = (text || "").trim();
    if (!t) return;

    // ✅ 修正：只有當這顆按鈕目前真的是 pressed 才視為「再按一次停止」
    const pressed = btn.getAttribute("aria-pressed") === "true";
    if (currentBtn === btn && pressed) {
      stop();
      return;
    }

    stop();

    const u = new SpeechSynthesisUtterance(t);
    const v = getSelectedVoice();

    if (v) {
      u.voice = v;
      u.lang = v.lang || preferredLang || DEFAULT_LANG;
    } else {
      u.lang = preferredLang || DEFAULT_LANG;
    }

    /* 可改：語速/音高 */
    u.rate = 1.0;
    u.pitch = 1.0;

    btn.setAttribute("data-state", "stop");
    btn.setAttribute("aria-pressed", "true");
    currentBtn = btn;

    u.onend = stop;
    u.onerror = stop;

    speechSynthesis.getVoices();
    speechSynthesis.speak(u);
  }

  function attachButtons() {
    document.querySelectorAll(".tts").forEach(textSpan => {
      let wrap = textSpan.closest(".tts-wrap");
      if (!wrap) {
        wrap = document.createElement("span");
        wrap.className = "tts-wrap";
        textSpan.parentNode.insertBefore(wrap, textSpan);
        wrap.appendChild(textSpan);
      }

      if (wrap.querySelector(":scope > button.tts-btn")) return;

      const pure = (textSpan.getAttribute("data-tts") || textSpan.textContent || "").trim();
      textSpan.setAttribute("data-tts", pure);

      const btn = document.createElement("button");
      btn.className = "tts-btn";
      btn.type = "button";
      btn.setAttribute("data-state", "play");
      btn.setAttribute("aria-pressed", "false");
      btn.setAttribute("aria-label", "Play/Stop");

      const lang = textSpan.getAttribute("data-lang") || DEFAULT_LANG;
      btn.onclick = () => speak(textSpan.getAttribute("data-tts"), lang, btn);

      wrap.appendChild(btn);
    });
  }

  /* =========================
     反白浮動工具：播放 + 翻譯
     ========================= */

  function ensureSelectionPop() {
    let pop = document.getElementById("tts-selection-pop");
    if (pop) return pop;

    pop = document.createElement("div");
    pop.id = "tts-selection-pop";

    const btn = document.createElement("button");
    btn.className = "tts-btn";
    btn.type = "button";
    btn.setAttribute("data-state", "play");
    btn.setAttribute("aria-pressed", "false");
    btn.setAttribute("aria-label", "Speak selection");

    const zh = document.createElement("div");
    zh.id = "tts-selection-zh";
    zh.innerHTML = '<span class="muted">翻譯載入中…</span>';

    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();

      const text = getSelectionText();
      if (!text) { hideSelectionPop(); return; }

      speak(text, SELECTION_LANG, btn);
    });

    pop.appendChild(btn);
    pop.appendChild(zh);
    document.body.appendChild(pop);
    return pop;
  }

  function hideSelectionPop() {
    const pop = document.getElementById("tts-selection-pop");
    if (pop) pop.style.display = "none";
  }

  function getSelectionText() {
    const sel = window.getSelection ? window.getSelection() : null;
    if (!sel || sel.rangeCount === 0) return "";
    const text = (sel.toString() || "").trim();
    if (!text || text.length > SELECTION_MAX_CHARS) return "";
    return text;
  }

  function getSelectionRect() {
    const sel = window.getSelection ? window.getSelection() : null;
    if (!sel || sel.rangeCount === 0) return null;
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    if (!rect || (rect.width === 0 && rect.height === 0)) return null;
    return rect;
  }

  async function translateToZh(text) {
    const key = `${TRANSLATE_FROM}|${TRANSLATE_TO}|${text}`;
    if (translateCache.has(key)) return translateCache.get(key);

    // Google gtx endpoint（無 key），有時候可能被網路環境擋；失敗就回傳空字串
    const url =
      "https://translate.googleapis.com/translate_a/single" +
      `?client=gtx&sl=${encodeURIComponent(TRANSLATE_FROM)}` +
      `&tl=${encodeURIComponent(TRANSLATE_TO)}` +
      `&dt=t&q=${encodeURIComponent(text)}`;

    try {
      const res = await fetch(url, { method: "GET" });
      if (!res.ok) throw new Error("http " + res.status);
      const data = await res.json();
      // data[0] 是分段翻譯陣列，取每段的 [0] 串起來
      const translated = Array.isArray(data?.[0]) ? data[0].map(x => x?.[0] || "").join("") : "";
      translateCache.set(key, translated);
      return translated;
    } catch (_) {
      translateCache.set(key, "");
      return "";
    }
  }

  async function showSelectionPop() {
    if (!supported()) return;

    const text = getSelectionText();
    if (!text) return hideSelectionPop();

    const rect = getSelectionRect();
    if (!rect) return hideSelectionPop();

    const pop = ensureSelectionPop();
    const zh = document.getElementById("tts-selection-zh");
    pop.style.display = "flex";

    // 定位
    const offset = 8;
    const popW = pop.offsetWidth || 240;
    const popH = pop.offsetHeight || 56;

    let left = rect.left + rect.width / 2 - popW / 2;
    let top  = rect.top - popH - offset;

    left = Math.max(8, Math.min(left, window.innerWidth - popW - 8));
    if (top < 8) top = rect.bottom + offset;

    pop.style.left = `${left}px`;
    pop.style.top  = `${top}px`;

    // 顯示翻譯
    if (zh) {
      zh.innerHTML = '<span class="muted">翻譯載入中…</span>';
      const translated = await translateToZh(text);
      zh.textContent = translated ? translated : "（翻譯失敗或被阻擋）";
    }
  }

  function bindSelectionEvents() {
    document.addEventListener("mouseup", () => setTimeout(showSelectionPop, 0));
    document.addEventListener("keyup", () => setTimeout(showSelectionPop, 0));

    // 點空白處關閉（點浮動工具本身不關）
    document.addEventListener("mousedown", (e) => {
      const pop = document.getElementById("tts-selection-pop");
      if (!pop) return;
      if (!pop.contains(e.target)) hideSelectionPop();
    });

    // 捲動/縮放關閉
    window.addEventListener("scroll", hideSelectionPop, true);
    window.addEventListener("resize", hideSelectionPop);
  }

  function init() {
    if (!supported()) return;
    ensureTopBar();
    populateVoicesAndSelectDefault();
    attachButtons();

    ensureSelectionPop();
    bindSelectionEvents();
  }

  if ("speechSynthesis" in window) {
    speechSynthesis.onvoiceschanged = () => {
      ensureTopBar();
      populateVoicesAndSelectDefault();
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
</script>
