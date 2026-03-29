(function () {
  "use strict";

  const PATCH_FLAG = "__peicdLegacyFlowchartCompatPatched";
  const CONFIG_DELIMITER = "---";
  const FLOWCHART_HEADER_RE = /^(?:flowchart|graph)\b/i;
  const RECT_LABEL_RE = /([A-Za-z_][\w-]*)(\[(?!\[)([^\]\r\n]*?)\])(?!\])/g;
  const TROUBLESOME_LABEL_RE = /[()（）]/;

  function stripLeadingConfigBlock(source) {
    const trimmed = source.trimStart();
    if (!trimmed.startsWith(CONFIG_DELIMITER)) return trimmed;

    const lines = trimmed.split(/\r?\n/);
    if (lines[0].trim() !== CONFIG_DELIMITER) return trimmed;

    let endIndex = 1;
    while (endIndex < lines.length && lines[endIndex].trim() !== CONFIG_DELIMITER) {
      endIndex += 1;
    }

    if (endIndex >= lines.length) return trimmed;
    return lines.slice(endIndex + 1).join("\n").trimStart();
  }

  function isFlowchartSource(source) {
    if (typeof source !== "string") return false;
    return FLOWCHART_HEADER_RE.test(stripLeadingConfigBlock(source));
  }

  function quoteLabel(label) {
    return `"${label.replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
  }

  function normalizeLegacyFlowchartSource(source) {
    if (!isFlowchartSource(source)) return source;

    let changed = false;
    const normalized = source
      .split(/\r?\n/)
      .map((line) => {
        const trimmed = line.trimStart();
        if (!trimmed || trimmed.startsWith("%%")) return line;

        return line.replace(RECT_LABEL_RE, (match, nodeId, bracketed, labelText) => {
          const trimmedLabel = labelText.trimStart();
          if (!trimmedLabel || /^["'`]/.test(trimmedLabel)) return match;
          if (!TROUBLESOME_LABEL_RE.test(labelText)) return match;

          changed = true;
          return `${nodeId}[${quoteLabel(labelText)}]`;
        });
      })
      .join("\n");

    return changed ? normalized : source;
  }

  function patchMermaidRender() {
    const mermaid = window.mermaid;
    if (!mermaid || mermaid[PATCH_FLAG]) return;

    const originalRender = mermaid.render.bind(mermaid);

    mermaid.render = async function patchedRender(id, source, container) {
      try {
        return await originalRender(id, source, container);
      } catch (error) {
        const fallbackSource = normalizeLegacyFlowchartSource(source);
        if (!fallbackSource || fallbackSource === source) {
          throw error;
        }

        try {
          return await originalRender(id, fallbackSource, container);
        } catch (fallbackError) {
          console.error("Mermaid legacy flowchart compatibility fallback failed", {
            error: fallbackError,
            originalError: error
          });
          throw fallbackError;
        }
      }
    };

    mermaid[PATCH_FLAG] = true;
  }

  patchMermaidRender();
})();
