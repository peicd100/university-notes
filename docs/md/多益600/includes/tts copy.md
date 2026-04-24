<!--
把這整段放在你的 tts.md（snippets）即可。

新增功能：
✅ 使用者反白任何文字 → 出現浮動播放鍵 → 點了朗讀反白內容
-->

<style>
/* =========================
   你可以改的地方：按鈕大小/外觀
   ========================= */

/* wrapper：把文字與按鈕放同一行，但文字本身維持正常排版 */
.tts-wrap{
  display: inline-flex;
  align-items: center;
  gap: 10px;                 /* ✅ 可改：按鈕與文字距離 */
}

/* 文字本體：保持正常 inline 流 */
.tts{
  display: inline;
}

/* 透明按鈕：顏色跟隨主題（亮/暗自動） */
.tts-btn{
  background: transparent;
  border: 0;
  font: inherit;

  width: 44px;               /* ✅ 可改：點擊區寬 */
  height: 44px;              /* ✅ 可改：點擊區高 */
  padding: 0;

  cursor: pointer;
  line-height: 1;

  display: inline-grid;
  place-items: center;
  position: relative;

  color: var(--md-primary-fg-color, currentColor);
  touch-action: manipulation;
}

/* hover：改成 accent */
.tts-btn:hover{
  color: var(--md-accent-fg-color, var(--md-primary-fg-color, currentColor));
}

/* 播放中狀態：用 accent */
.tts-btn[aria-pressed="true"]{
  color: var(--md-accent-fg-color, var(--md-primary-fg-color, currentColor));
  opacity: 0.85;             /* ✅ 可改：播放中視覺提示 */
}

/* 鍵盤焦點可視化 */
.tts-btn:focus-visible{
  outline: 2px solid var(--md-accent-fg-color, currentColor);
  outline-offset: 3px;
  border-radius: 10px;
}

/* ===== 用 CSS 畫圖示（用 currentColor 上色） ===== */
/* 播放：三角形 */
.tts-btn[data-state="play"]::before{
  content: "";
  display: block;
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 9px 0 9px 14px;   /* ✅ 可改：三角形比例 */
  border-color: transparent transparent transparent currentColor;
  transform: translateX(1px);
}

/* 停止：方塊 */
.tts-btn[data-state="stop"]::before{
  content: "";
  display: block;
  width: 16px;                    /* ✅ 可改：方塊大小 */
  height: 16px;
  background: currentColor;
  border-radius: 3px;             /* ✅ 可改：0 = 更方 */
}

/* =========================
   Voice bar：插在第一個 H1 後
   ========================= */
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

/* ===== 語音選單：暗色模式下黑底（你 scheme 是 slate）===== */
[data-md-color-scheme="slate"] #tts-voice-picker{
  background-color: #1e1e1e;
  color: #fff;
  border-color: rgba(255,255,255,.25);
}
[data-md-color-scheme="slate"] #tts-voice-picker option{
  background-color: #1e1e1e;
  color: #fff;
}

/* ✅ 可改：手機再大一點（可刪除整段） */
@media (max-width: 600px){
  .tts-btn{
    width: 52px;
    height: 52px;
  }
  .tts-btn[data-state="play"]::before{
    border-width: 10px 0 10px 16px;
  }
  .tts-btn[data-state="stop"]::before{
    width: 18px;
    height: 18px;
  }
}

/* =========================
   新增：反白浮動按鈕（Selection TTS）
   ========================= */
#tts-selection-pop{
  position: fixed;
  z-index: 9999;
  display: none;             /* 預設不顯示 */
  padding: 6px;
  border-radius: 12px;

  /* ✅ 可改：浮層背景/邊框（跟主題走） */
  background: var(--md-default-bg-color, rgba(0,0,0,.8));
  border: 1px solid var(--md-default-fg-color--lightest, rgba(255,255,255,.2));

  box-shadow: 0 10px 30px rgba(0,0,0,.25);
}
</style>

<script>
(function () {
  let currentBtn = null;

  /* =========================
     你可以改的地方：預設語音
     ========================= */
  const DEFAULT_LANG = "en-US";                      // ✅ 可改：例如 "en-GB"
  const DEFAULT_NAME_INCLUDES = "Google US English"; // ✅ 可改：例如 "Google UK English"
  /* ========================= */

  /* =========================
     新增：反白朗讀設定
     ========================= */
  const SELECTION_MAX_CHARS = 120;   // ✅ 可改：太長就不顯示（避免整段文章誤觸）
  const SELECTION_LANG = "en-US";    // ✅ 可改：反白朗讀預設語言
  /* ========================= */

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
    if (h1 && h1.parentNode) {
      h1.insertAdjacentElement("afterend", bar);
    } else {
      container.insertBefore(bar, container.firstChild);
    }

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

    // 同顆再按：停止
    if (currentBtn === btn) {
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

    /* ✅ 可改：語速/音高 */
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
     新增：反白朗讀（Selection TTS）
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

    // 點浮動按鈕：朗讀目前選取文字
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();

      const text = getSelectionText();
      if (!text) {
        hideSelectionPop();
        return;
      }
      speak(text, SELECTION_LANG, btn);
    });

    pop.appendChild(btn);
    document.body.appendChild(pop);
    return pop;
  }

  function getSelectionText() {
    const sel = window.getSelection ? window.getSelection() : null;
    if (!sel || sel.rangeCount === 0) return "";
    const text = (sel.toString() || "").trim();
    // 避免選到太長一段
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

  function showSelectionPop() {
    if (!supported()) return;

    const text = getSelectionText();
    if (!text) return hideSelectionPop();

    const rect = getSelectionRect();
    if (!rect) return hideSelectionPop();

    const pop = ensureSelectionPop();
    const btn = pop.querySelector("button.tts-btn");

    // 如果不是同一顆按鈕在播（避免狀態混亂）
    // 這裡不強制 stop()，因為你可能正在播別句；你要強制停止可取消註解：
    // stop();

    // 每次顯示時，先把浮動按鈕狀態重置成 play（避免上一輪是 stop）
    if (btn) {
      btn.setAttribute("data-state", "play");
      btn.setAttribute("aria-pressed", "false");
    }

    const offset = 8; // ✅ 可改：浮層距離選取區
    const popW = pop.offsetWidth || 56;
    const popH = pop.offsetHeight || 56;

    let left = rect.left + rect.width / 2 - popW / 2;
    let top  = rect.top - popH - offset;

    // 邊界修正（避免跑出螢幕）
    left = Math.max(8, Math.min(left, window.innerWidth - popW - 8));
    if (top < 8) top = rect.bottom + offset; // 上面放不下就放下面

    pop.style.left = `${left}px`;
    pop.style.top  = `${top}px`;
    pop.style.display = "block";
  }

  function hideSelectionPop() {
    const pop = document.getElementById("tts-selection-pop");
    if (pop) pop.style.display = "none";
  }

  function bindSelectionEvents() {
    // 滑鼠放開/鍵盤選取後顯示
    document.addEventListener("mouseup", () => {
      // 讓 selection 先更新
      setTimeout(showSelectionPop, 0);
    });

    document.addEventListener("keyup", () => {
      setTimeout(showSelectionPop, 0);
    });

    // 點空白處就關閉
    document.addEventListener("mousedown", (e) => {
      const pop = document.getElementById("tts-selection-pop");
      if (!pop) return;
      if (!pop.contains(e.target)) hideSelectionPop();
    });

    // 捲動/縮放就關閉（避免位置錯亂）
    window.addEventListener("scroll", hideSelectionPop, true);
    window.addEventListener("resize", hideSelectionPop);
  }

  /* =========================
     init
     ========================= */
  function init() {
    if (!supported()) return;
    ensureTopBar();
    populateVoicesAndSelectDefault();
    attachButtons();

    // 新增：反白朗讀
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
