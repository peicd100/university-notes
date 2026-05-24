(function () {
  "use strict";

  const schemes = ["default", "slate", "dracula"];
  const DARK_FLOWCHART_THEME = {
    darkMode: true,
    background: "#000000",
    mainBkg: "#31284d",
    textColor: "#f8fbff",
    lineColor: "#d9c7ff",
    primaryColor: "#31284d",
    primaryTextColor: "#f8fbff",
    primaryBorderColor: "#72e3fd",
    secondaryColor: "#173d4a",
    secondaryTextColor: "#e9fbff",
    secondaryBorderColor: "#72e3fd",
    tertiaryColor: "#20263a",
    tertiaryTextColor: "#f8fbff",
    tertiaryBorderColor: "#9fb3ff",
    edgeLabelBackground: "#141b2a",
    edgeLabelText: "#f8fbff",
    defaultLinkColor: "#d9c7ff",
    clusterBkg: "#171d2c",
    clusterBorder: "#72e3fd"
  };

  const DARK_FLOWCHART_CSS = `
    * {
      --peicd-flow-node-bg: #31284d;
      --peicd-flow-node-border: #72e3fd;
      --peicd-flow-text: #f8fbff;
      --peicd-flow-edge: #d9c7ff;
      --peicd-flow-edge-label-bg: #141b2a;
    }
    .node rect,
    .node circle,
    .node ellipse,
    .node polygon,
    .node path {
      fill: var(--peicd-flow-node-bg) !important;
      stroke: var(--peicd-flow-node-border) !important;
      stroke-width: 1.5px !important;
    }
    .labelText,
    :not(.branchLabel) > .label text,
    .nodeLabel,
    .nodeLabel p,
    .edgeLabel,
    .edgeLabel p,
    .edgeLabel span {
      color: var(--peicd-flow-text) !important;
      fill: var(--peicd-flow-text) !important;
    }
    .edgeLabel rect,
    .edgeLabel .labelBkg {
      fill: var(--peicd-flow-edge-label-bg) !important;
      opacity: 0.96 !important;
    }
    .flowchart-link,
    .edgePath .path,
    marker path {
      stroke: var(--peicd-flow-edge) !important;
    }
  `;

  function ensureSchemeConfig(name) {
    const root = window.mermaidConfig || (window.mermaidConfig = {});
    const current = root[name] || (root[name] = {});
    const flowchart = current.flowchart || (current.flowchart = {});

    root.htmlLabels = true;
    current.htmlLabels = true;
    flowchart.htmlLabels = true;
    if (current.useMaxWidth === undefined) current.useMaxWidth = false;
    if (flowchart.useMaxWidth === undefined) flowchart.useMaxWidth = false;

    if (name === "slate" || name === "dracula") {
      current.themeVariables = Object.assign({}, current.themeVariables || {}, DARK_FLOWCHART_THEME);
      current.themeCSS = (current.themeCSS || "") + DARK_FLOWCHART_CSS;
    }
  }

  schemes.forEach(ensureSchemeConfig);
})();
