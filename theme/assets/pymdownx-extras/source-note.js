/* Source-appearance notes: sandboxed content owns its typography; the site owns sizing. */
(function () {
  "use strict";
  if (window.__peicdSourceNotes) { window.__peicdSourceNotes.scan(); return; }
  const selector = "iframe[data-peicd-note-frame][srcdoc]";
  const frames = new Set();
  const initialized = new WeakSet();
  let scheduled = false;

  const style = document.createElement("style");
  style.textContent = `
    .md-typeset .peicd-source-note{width:100%;min-width:0;margin:1em 0;overflow:hidden;border-radius:8px}
    .md-typeset .peicd-source-note>iframe[data-peicd-note-frame]{display:block;width:100%;max-width:100%;border:0;margin:0;padding:0;color-scheme:normal}
    .md-typeset details.peicd-note-markdown{margin:1em 0}
    @media print{.peicd-source-note{overflow:visible!important;break-inside:auto}.peicd-note-markdown:not([open]){display:none!important}}
  `;
  document.head.appendChild(style);

  function request(frame) {
    frame.contentWindow?.postMessage({ type: "peicd-note-measure", id: frame.dataset.peicdNoteFrame }, "*");
  }
  function scan() {
    scheduled = false;
    for (const frame of frames) if (!frame.isConnected) frames.delete(frame);
    document.querySelectorAll(selector).forEach((frame) => {
      frames.add(frame);
      if (!initialized.has(frame)) {
        initialized.add(frame);
        frame.addEventListener("load", () => { if (frame.isConnected) request(frame); });
      }
      request(frame);
    });
  }
  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(scan);
  }
  window.addEventListener("message", (event) => {
    const data = event.data;
    if (!data || data.type !== "peicd-note-size" || typeof data.id !== "string"
        || !Number.isFinite(data.height) || data.height < 1 || data.height > 2000000) return;
    for (const frame of frames) {
      if (!frame.isConnected || event.source !== frame.contentWindow || data.id !== frame.dataset.peicdNoteFrame) continue;
      const height = Math.ceil(data.height);
      if (frame.getAttribute("height") !== String(height)) frame.setAttribute("height", String(height));
      break;
    }
  });
  window.__peicdSourceNotes = { scan: schedule };
  window.addEventListener("beforeprint", scan);
  window.addEventListener("load", schedule, { once: true });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", schedule, { once: true });
  else schedule();
  if (window.document$?.subscribe) window.document$.subscribe(schedule);
})();
