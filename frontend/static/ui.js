function peBoot() {
  if (window.__peBooted) return;
  var app = document.getElementById("pe-app");
  if (!app) {
    setTimeout(peBoot, 120);
    return;
  }
  window.__peBooted = true;

  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- background: dot grid and flowing curves ---------- */

  var FX = {
    dot: "31, 30, 29",
    dotA: 0.2,
    dotR: 1,
    grid: 24,
    lineColor: "217, 119, 87",
    lineA: 0.24,
    lineW: 1.3,
    amp: 18,
    glow: 9,
    gap: 78
  };
  var fxT = 0;
  var panels = [];

  function mountCanvases() {
    var hosts = document.querySelectorAll(".hero, .pe-panel");
    var previous = panels;
    panels = [];
    for (var i = 0; i < hosts.length; i++) {
      var host = hosts[i];
      var cv = host.querySelector(":scope > .panel-fx");
      if (!cv) {
        cv = document.createElement("canvas");
        cv.className = "panel-fx";
        cv.setAttribute("aria-hidden", "true");
        host.insertBefore(cv, host.firstChild);
      }
      /* Keep the measured size of a canvas we have already mounted. Resetting it to
         zero makes panelFrame reallocate the backing store on every re-render. */
      var prior = null;
      for (var j = 0; j < previous.length; j++) {
        if (previous[j].cv === cv) { prior = previous[j]; break; }
      }
      panels.push(prior || { el: host, cv: cv, ctx: cv.getContext("2d"), w: 0, h: 0 });
    }
  }

  function panelFrame(pf, t) {
    var el = pf.el, cv = pf.cv, ctx = pf.ctx;
    if (!el || !ctx) return;
    var w = el.clientWidth, h = el.clientHeight;
    if (w <= 0 || h <= 0) return;
    if (pf.w !== w || pf.h !== h) {
      cv.width = Math.round(w * dpr);
      cv.height = Math.round(h * dpr);
      cv.style.width = w + "px";
      cv.style.height = h + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      pf.w = w;
      pf.h = h;
    }
    var c = FX, gx, gy, b, x, y, baseY, k;
    ctx.clearRect(0, 0, w, h);
    for (gy = c.grid * 0.5; gy < h; gy += c.grid) {
      for (gx = c.grid * 0.5; gx < w; gx += c.grid) {
        b = 0.4 + 0.6 * (0.5 + 0.5 * Math.sin(gx * 0.018 + gy * 0.02 - t * 0.02));
        ctx.fillStyle = "rgba(" + c.dot + "," + c.dotA * b + ")";
        ctx.beginPath();
        ctx.arc(gx, gy, c.dotR, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    ctx.lineWidth = c.lineW;
    ctx.shadowColor = "rgba(" + c.lineColor + ",0.9)";
    ctx.shadowBlur = c.glow;
    var nLines = Math.max(2, Math.round(h / c.gap));
    for (k = 0; k < nLines; k++) {
      baseY = (h * (k + 1)) / (nLines + 1);
      b = 0.4 + 0.6 * (0.5 + 0.5 * Math.sin(baseY * 0.02 - t * 0.02));
      ctx.strokeStyle = "rgba(" + c.lineColor + "," + c.lineA * b + ")";
      ctx.beginPath();
      for (x = -20; x <= w + 20; x += 8) {
        y =
          baseY +
          c.amp * Math.sin(x * 0.006 + t * 0.012 + k * 0.9) +
          c.amp * 0.5 * Math.sin(x * 0.013 - t * 0.017 + k * 1.7);
        if (x <= -20) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
    ctx.shadowBlur = 0;
  }

  /* ---------- breathing ring while the agent is running ---------- */

  var ring = document.createElement("canvas");
  ring.className = "reasoning-canvas";
  ring.setAttribute("aria-hidden", "true");
  document.body.appendChild(ring);
  var rctx = ring.getContext("2d");
  var RING_M = 60;
  var ringW = 0, ringH = 0, breatheP = 0, ringPts = null, ringKey = "";

  function roundRectPath(x, y, w, h, r, step) {
    r = Math.min(r, w / 2, h / 2);
    var out = [];
    function line(x1, y1, x2, y2) {
      var ax = x2 - x1, ay = y2 - y1, len = Math.sqrt(ax * ax + ay * ay);
      var s, n = Math.max(1, Math.round(len / step));
      for (s = 0; s < n; s++) out.push({ x: x1 + (ax * s) / n, y: y1 + (ay * s) / n });
    }
    function arc(cx, cy, a0, a1) {
      var len = Math.abs(a1 - a0) * r, s, n = Math.max(1, Math.round(len / step)), an;
      for (s = 0; s < n; s++) {
        an = a0 + ((a1 - a0) * s) / n;
        out.push({ x: cx + Math.cos(an) * r, y: cy + Math.sin(an) * r });
      }
    }
    var rt = x + w, bt = y + h, q = Math.PI / 2;
    line(x + r, y, rt - r, y);
    arc(rt - r, y + r, -q, 0);
    line(rt, y + r, rt, bt - r);
    arc(rt - r, bt - r, 0, q);
    line(rt - r, bt, x + r, bt);
    arc(x + r, bt - r, q, Math.PI);
    line(x, bt - r, x, y + r);
    arc(x + r, y + r, Math.PI, Math.PI * 1.5);
    return out;
  }

  function ringFrame(advance) {
    if (!document.body.classList.contains("is-reasoning")) {
      ring.style.opacity = "0";
      return;
    }
    var key = ringW + "x" + ringH;
    if (key !== ringKey) {
      ringPts = roundRectPath(RING_M, RING_M, window.innerWidth, window.innerHeight, 22, 12);
      ringKey = key;
    }
    if (advance) breatheP += 0.016;
    ring.style.opacity = 0.3 + 0.6 * (0.5 + 0.5 * Math.sin(breatheP));
    var p = ringPts, n = p.length, i, a, b;
    rctx.clearRect(0, 0, ringW, ringH);
    rctx.lineCap = "round";
    rctx.lineJoin = "round";
    rctx.lineWidth = 50;
    rctx.strokeStyle = "rgb(217, 119, 87)";
    for (i = 0; i < n; i++) {
      a = p[i];
      b = p[(i + 1) % n];
      rctx.beginPath();
      rctx.moveTo(a.x, a.y);
      rctx.lineTo(b.x, b.y);
      rctx.stroke();
    }
  }

  function resizeRing() {
    ringW = window.innerWidth + 2 * RING_M;
    ringH = window.innerHeight + 2 * RING_M;
    ring.width = Math.round(ringW * dpr);
    ring.height = Math.round(ringH * dpr);
    ring.style.width = ringW + "px";
    ring.style.height = ringH + "px";
    rctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ringKey = "";
  }

  var drawnOnce = false;

  function tick() {
    for (var i = 0; i < panels.length; i++) panelFrame(panels[i], fxT);
    ringFrame(!reduce);
    if (reduce) {
      /* The background is decorative. With reduced motion asked for, draw it once and
         stop: the frame never changes, and redrawing it sixty times a second costs a
         shared 2 vCPU instance real work for no visible difference. */
      drawnOnce = true;
      return;
    }
    fxT += 1;
    requestAnimationFrame(tick);
  }

  /* ---------- state that must survive a Gradio re-render ---------- */

  var openKeys = {};
  var activeTab = null;
  var activeScope = null;

  /* ---------- resizable and hideable three-panel layout ---------- */

  var LAYOUT_KEY = "physearth-panel-layout-v1";
  var DEFAULT_LAYOUT = {
    ratios: [1.16, 1, 0.96],
    hidden: [false, false, false]
  };
  var layout = loadLayout();
  var layoutStage = null;
  var layoutHandles = [];
  var layoutDrag = null;
  var layoutPointerEventsBound = false;
  var layoutMouseEventsBound = false;

  function loadLayout() {
    try {
      var raw = window.localStorage.getItem(LAYOUT_KEY);
      if (!raw) return { ratios: DEFAULT_LAYOUT.ratios.slice(), hidden: DEFAULT_LAYOUT.hidden.slice() };
      var value = JSON.parse(raw);
      var ratios = Array.isArray(value.ratios) && value.ratios.length === 3
        ? value.ratios.map(Number) : DEFAULT_LAYOUT.ratios.slice();
      var hidden = Array.isArray(value.hidden) && value.hidden.length === 3
        ? value.hidden.map(Boolean) : DEFAULT_LAYOUT.hidden.slice();
      if (ratios.some(function (n) { return !isFinite(n) || n <= 0; })) {
        ratios = DEFAULT_LAYOUT.ratios.slice();
      }
      if (hidden.every(Boolean)) hidden[0] = false;
      return { ratios: ratios, hidden: hidden };
    } catch (e) {
      return { ratios: DEFAULT_LAYOUT.ratios.slice(), hidden: DEFAULT_LAYOUT.hidden.slice() };
    }
  }

  function saveLayout() {
    try { window.localStorage.setItem(LAYOUT_KEY, JSON.stringify(layout)); } catch (e) {}
  }

  function panelName(index) {
    return ["Chat", "Trace", "Evidence"][index];
  }

  function visibleIndexes() {
    var out = [];
    for (var i = 0; i < 3; i++) if (!layout.hidden[i]) out.push(i);
    return out;
  }

  function panelElements() {
    if (!layoutStage) return [];
    var ids = ["pe-panel-chat", "pe-panel-trace", "pe-panel-evid"];
    var panels = [];
    for (var i = 0; i < ids.length; i++) {
      var panel = document.getElementById(ids[i]);
      if (!panel || !layoutStage.contains(panel)) return [];
      panels.push(panel);
    }
    return panels;
  }

  function applyLayout() {
    if (!layoutStage) return;
    var els = panelElements();
    if (els.length !== 3) return;
    for (var i = 0; i < 3; i++) {
      els[i].classList.toggle("is-panel-hidden", !!layout.hidden[i]);
    }
    var visible = visibleIndexes();
    var total = visible.reduce(function (sum, index) { return sum + layout.ratios[index]; }, 0);
    if (!isFinite(total) || total <= 0) return;
    var columns = visible.map(function (index) {
      return "minmax(180px, " + layout.ratios[index] + "fr)";
    });
    layoutStage.style.setProperty("grid-template-columns", columns.join(" "), "important");
    layoutStage.classList.toggle("has-hidden-panel", visible.length < 3);
    requestAnimationFrame(positionLayoutHandles);
  }

  function positionLayoutHandles() {
    if (!layoutStage) return;
    var visible = visibleIndexes();
    var stageRect = layoutStage.getBoundingClientRect();
    for (var i = 0; i < layoutHandles.length; i++) {
      var handle = layoutHandles[i];
      var leftIndex = visible[i], rightIndex = visible[i + 1];
      if (leftIndex === undefined || rightIndex === undefined) {
        handle.hidden = true;
        continue;
      }
      var els = panelElements();
      var leftRect = els[leftIndex].getBoundingClientRect();
      var rightRect = els[rightIndex].getBoundingClientRect();
      handle.hidden = false;
      /* Put the hit area in the middle of the gap. This keeps it visible and
         clickable even when the neighboring panel has an elevated child layer. */
      handle.style.left = (((leftRect.right + rightRect.left) / 2) - stageRect.left) + "px";
      handle.setAttribute("aria-label", "Resize " + panelName(leftIndex) + " and " + panelName(rightIndex));
      handle.dataset.leftIndex = leftIndex;
      handle.dataset.rightIndex = rightIndex;
    }
  }

  function buildLayoutControls() {
    var stage = document.querySelector("#pe-app .stage");
    if (!stage) return;
    layoutStage = stage;
    if (layoutHandles.length !== 2 || layoutHandles.some(function (handle) {
      return handle.parentNode !== stage;
    })) {
      layoutHandles = [];
      for (var i = 0; i < 2; i++) {
        var handle = document.createElement("div");
        handle.className = "pe-layout-handle";
        handle.setAttribute("role", "separator");
        handle.setAttribute("tabindex", "0");
        stage.appendChild(handle);
        layoutHandles.push(handle);
        bindLayoutHandle(handle);
      }
    }
    bindLayoutPointerEvents();
    applyLayout();
  }

  function moveLayout(event) {
    if (!layoutDrag || layoutDrag.pointer !== event.pointerId || !layoutStage) return;
    var stageWidth = layoutStage.clientWidth;
    if (!stageWidth) return;
    var delta = (event.clientX - layoutDrag.x) / stageWidth;
    var left = layoutDrag.left, right = layoutDrag.right;
    var nextLeft = layout.ratios[left] + delta;
    var nextRight = layout.ratios[right] - delta;
    var min = 0.12;
    if (nextLeft < min || nextRight < min) return;
    layout.ratios[left] = nextLeft;
    layout.ratios[right] = nextRight;
    layoutDrag.x = event.clientX;
    applyLayout();
    event.preventDefault();
  }

  function finishLayoutDrag(event) {
    if (!layoutDrag || layoutDrag.pointer !== event.pointerId) return;
    var handle = layoutDrag.handle;
    layoutDrag = null;
    if (handle) handle.classList.remove("is-dragging");
    saveLayout();
    positionLayoutHandles();
  }

  function moveLayoutMouse(event) {
    if (!layoutDrag || layoutDrag.pointer !== "mouse") return;
    moveLayout({
      pointerId: "mouse",
      clientX: event.clientX,
      preventDefault: function () { event.preventDefault(); },
    });
  }

  function finishLayoutMouse(event) {
    if (!layoutDrag || layoutDrag.pointer !== "mouse") return;
    finishLayoutDrag({ pointerId: "mouse" });
    event.preventDefault();
  }

  function bindLayoutPointerEvents() {
    if (layoutPointerEventsBound) return;
    layoutPointerEventsBound = true;
    document.addEventListener("pointermove", moveLayout, true);
    document.addEventListener("pointerup", finishLayoutDrag, true);
    document.addEventListener("pointercancel", finishLayoutDrag, true);
    if (!layoutMouseEventsBound) {
      layoutMouseEventsBound = true;
      document.addEventListener("mousemove", moveLayoutMouse, true);
      document.addEventListener("mouseup", finishLayoutMouse, true);
    }
  }

  function bindLayoutHandle(handle) {
    handle.addEventListener("pointerdown", function (event) {
      if (handle.hidden || !layoutStage) return;
      var left = Number(handle.dataset.leftIndex), right = Number(handle.dataset.rightIndex);
      if (!isFinite(left) || !isFinite(right)) return;
      try { handle.setPointerCapture(event.pointerId); } catch (e) {}
      handle.classList.add("is-dragging");
      layoutDrag = {
        handle: handle,
        pointer: event.pointerId,
        left: left,
        right: right,
        x: event.clientX,
      };
      event.preventDefault();
    });
    handle.addEventListener("mousedown", function (event) {
      if (event.button !== 0 || handle.hidden || !layoutStage) return;
      var left = Number(handle.dataset.leftIndex), right = Number(handle.dataset.rightIndex);
      if (!isFinite(left) || !isFinite(right)) return;
      handle.classList.add("is-dragging");
      layoutDrag = { handle: handle, pointer: "mouse", left: left, right: right, x: event.clientX };
      event.preventDefault();
    });
    handle.addEventListener("dblclick", function () {
      layout.ratios = DEFAULT_LAYOUT.ratios.slice();
      saveLayout();
      applyLayout();
    });
  }

  function rememberOpen(node) {
    var key = node.getAttribute("data-key");
    if (key) openKeys[key] = node.open;
  }

  function restoreState(root) {
    var items = root.querySelectorAll("details[data-key]");
    for (var i = 0; i < items.length; i++) {
      var key = items[i].getAttribute("data-key");
      if (Object.prototype.hasOwnProperty.call(openKeys, key)) items[i].open = openKeys[key];
      if (!items[i].dataset.bound) {
        items[i].dataset.bound = "1";
        items[i].addEventListener("toggle", function () { rememberOpen(this); });
      }
    }
    if (activeTab) {
      var tab = document.getElementById(activeTab);
      if (tab) tab.checked = true;
    }
    if (activeScope) {
      var scope = document.getElementById(activeScope);
      if (scope) scope.checked = true;
    }
  }

  document.addEventListener("change", function (event) {
    var target = event.target;
    if (!target || !target.id) return;
    if (target.classList.contains("tab-input")) activeTab = target.id;
    if (target.classList.contains("scope-input")) activeScope = target.id;
  });

  /* ---------- keep the scrolling panes pinned to the newest content ---------- */

  function scrollToEnd(node, force) {
    /* Keep the latest conversation visible while respecting a reader who scrolled up
       to inspect the paper brief or an earlier answer. */
    if (!node) return;
    if (force || node.scrollHeight - node.scrollTop - node.clientHeight < 48) {
      node.scrollTop = node.scrollHeight;
    }
  }

  function autoScroll() {
    /* The transcript is the left-panel scroll surface. New streamed context and review
       cards should always leave the latest exchange visible; the plan itself is a
       collapsible card, so this does not create a second scrollbar. */
    scrollToEnd(document.getElementById("pe-chat-scroll"), true);
    scrollToEnd(document.querySelector(".pe-panel--trace .subpanel__scroll"));
  }

  /* ---------- clicks: examples, model choice, citation jumps ---------- */

  function textarea() {
    var box = document.getElementById("pe-input");
    return box ? box.querySelector("textarea") : null;
  }

  document.addEventListener("click", function (event) {
    var pick = event.target.closest ? event.target.closest("[data-model]") : null;
    if (pick) {
      event.preventDefault();
      var bridge = document.getElementById("pe-model-bridge");
      var input = bridge ? bridge.querySelector("textarea, input") : null;
      if (input) {
        var proto = input.tagName === "TEXTAREA"
          ? window.HTMLTextAreaElement.prototype
          : window.HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(proto, "value").set.call(
          input,
          pick.getAttribute("data-model")
        );
        input.dispatchEvent(new Event("input", { bubbles: true }));
      }
      var group = pick.parentElement.querySelectorAll("[data-model]");
      for (var i = 0; i < group.length; i++) group[i].classList.remove("is-active");
      pick.classList.add("is-active");
      return;
    }

    var chart = event.target.closest ? event.target.closest("[data-chart-id]") : null;
    if (chart) {
      event.preventDefault();
      var chartBridge = document.getElementById("pe-chart-bridge");
      var chartInput = chartBridge ? chartBridge.querySelector("textarea, input") : null;
      if (chartInput) {
        var chartProto = chartInput.tagName === "TEXTAREA"
          ? window.HTMLTextAreaElement.prototype
          : window.HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(chartProto, "value").set.call(
          chartInput,
          chart.getAttribute("data-chart-id")
        );
        chartInput.dispatchEvent(new Event("input", { bubbles: true }));
        chart.classList.add("is-selected");
        setTimeout(function () {
          var submitChart = document.getElementById("pe-chart-submit");
          if (submitChart) submitChart.click();
        }, 0);
      }
      return;
    }

    var jump = event.target.closest ? event.target.closest("[data-jump]") : null;
    if (jump) {
      event.preventDefault();
      var wanted = jump.getAttribute("data-jump");
      var tabFor = jump.getAttribute("data-tab");
      if (tabFor) {
        var radio = document.getElementById(tabFor);
        if (radio) {
          radio.checked = true;
          activeTab = tabFor;
        }
      }
      var card = document.querySelector('[data-anchor="' + wanted + '"]');
      if (card) {
        var focused = document.querySelectorAll(".is-focus");
        for (var k = 0; k < focused.length; k++) focused[k].classList.remove("is-focus");
        card.classList.add("is-focus");
        card.scrollIntoView({ block: "center", behavior: "smooth" });
      }
    }
  });

  /* ---------- acknowledge the click before the server can ----------

     Only change UI state that is outside Gradio-managed output components here. Writing
     innerHTML into a gr.HTML root destroys the DOM node that Gradio/Svelte owns. The run
     then continues normally on the server, but later answer frames can no longer replace
     the hand-written "Waiting for the first token" placeholder. The authoritative first
     frame is fast enough to render the question and placeholder itself. */

  var pendingUntil = 0;
  var reviewInFlight = false;
  var reviewPhaseAtClick = "";

  function optimisticSend() {
    var area = textarea();
    var text = area ? area.value.trim() : "";
    if (!text) return;
    /* A chat revision supersedes the expanded draft immediately.  Collapse the
       current card while the agent validates the request; the server also marks a
       successful new plan version collapsed, so a rerender cannot reopen the old
       long body. */
    var currentPlan = document.querySelector(".research-plan-details[open]");
    if (currentPlan) currentPlan.removeAttribute("open");
    pendingUntil = Date.now() + 20000;
    document.body.classList.add("is-reasoning");

    /* Empty the box on the next turn of the event loop, not now. Gradio reads the value
       during its own bubble-phase handler for this same click; clearing it here, in the
       capture phase, would hand the server an empty question. The timeout runs after that
       handler, and it deliberately does not dispatch an input event: Gradio's store keeps
       the text it already captured, and the first frame back sets the box to empty anyway,
       so the two agree. */
    setTimeout(function () {
      var box = textarea();
      if (box) box.value = "";
    }, 0);
  }

  function optimisticClear() {
    pendingUntil = 0;
    document.body.classList.remove("is-reasoning");
    var box = textarea();
    if (box) box.value = "";
  }

  function syncResearchControls() {
    var card = document.querySelector(".approve--research[data-research-phase]");
    if (!card) {
      reviewInFlight = false;
      reviewPhaseAtClick = "";
      return;
    }
    var phase = card.getAttribute("data-research-phase");
    if (reviewInFlight && phase !== reviewPhaseAtClick) {
      reviewInFlight = false;
      reviewPhaseAtClick = "";
    }
    var labels = ["Approve plan", "Satisfied with figures"];
    if (!labels) return;
    var buttons = [
      document.getElementById("pe-approve-yes"),
      document.getElementById("pe-approve-all")
    ];
    for (var i = 0; i < buttons.length; i++) {
      if (buttons[i] && buttons[i].textContent.trim() !== labels[i]) {
        buttons[i].textContent = labels[i];
      }
    }
    if (buttons[0]) buttons[0].disabled = reviewInFlight || !["plan_review", "plan_approved"].includes(phase);
    if (buttons[1]) buttons[1].disabled = reviewInFlight || !["pseudo_preview", "chart_selected"].includes(phase);
  }

  document.addEventListener("click", function (event) {
    var target = event.target.closest ? event.target.closest("button") : null;
    if (!target) return;
    if (target.id === "pe-send") optimisticSend();
    if (target.id === "pe-clear") optimisticClear();
    if (target.id === "pe-approve-yes" || target.id === "pe-approve-all") {
      var card = document.querySelector(".approve--research[data-research-phase]");
      if (reviewInFlight) {
        event.preventDefault();
        event.stopImmediatePropagation();
        return;
      }
      if (card) {
        reviewInFlight = true;
        reviewPhaseAtClick = card.getAttribute("data-research-phase") || "";
        var reviewButtons = [
          document.getElementById("pe-approve-yes"),
          document.getElementById("pe-approve-all")
        ];
        for (var r = 0; r < reviewButtons.length; r++) {
          if (reviewButtons[r]) reviewButtons[r].disabled = true;
        }
        /* A lost network response must not permanently lock the review controls. */
        setTimeout(function () {
          if (reviewInFlight) {
            reviewInFlight = false;
            reviewPhaseAtClick = "";
            syncResearchControls();
          }
        }, 30000);
      }
    }
  }, true);

  /* Enter sends, shift+Enter makes a new line.

     Registered in the capture phase and stopping propagation, because Gradio's own
     Textbox handler binds on the target and, with lines > 1, treats shift+Enter as a
     submit while suppressing the newline. Left alone it would both refuse to break the
     line and start a second concurrent run on the same session. */
  document.addEventListener("keydown", function (event) {
    var area = textarea();
    if (!area || event.target !== area) return;
    if (event.key !== "Enter" || event.isComposing) return;
    event.stopPropagation();
    if (event.shiftKey) return;
    event.preventDefault();
    var send = document.getElementById("pe-send");
    if (send) send.click();
  }, true);

  /* ---------- react to every Gradio re-render ---------- */

  var pending = null;
  var observer = new MutationObserver(function () {
    if (pending) return;
    pending = requestAnimationFrame(function () {
      pending = null;
      mountCanvases();
      buildLayoutControls();
      silenceBridge();
      if (reduce && drawnOnce) {
        for (var i = 0; i < panels.length; i++) panelFrame(panels[i], fxT);
      }
      restoreState(document);
      syncResearchControls();
      autoScroll();
      var running = !!document.querySelector("[data-running]");
      if (running) pendingUntil = 0;
      document.body.classList.toggle(
        "is-reasoning",
        running || Date.now() < pendingUntil
      );
    });
  });
  observer.observe(app, { childList: true, subtree: true });

  /* The model bridge is offscreen but still an editable textbox in the tab order.
     Keyboard users tabbing through the composer would land in an invisible field. */
  function silenceBridge() {
    var bridges = [
      document.getElementById("pe-model-bridge"),
      document.getElementById("pe-review-command"),
      document.getElementById("pe-chart-bridge"),
      document.getElementById("pe-chart-submit")
    ];
    for (var b = 0; b < bridges.length; b++) {
      var bridge = bridges[b];
      if (!bridge) continue;
      bridge.setAttribute("aria-hidden", "true");
      var fields = bridge.querySelectorAll("textarea, input");
      for (var i = 0; i < fields.length; i++) fields[i].setAttribute("tabindex", "-1");
    }
  }

  mountCanvases();
  buildLayoutControls();
  silenceBridge();
  restoreState(document);
  syncResearchControls();
  resizeRing();
  window.addEventListener("resize", function () {
    resizeRing();
    positionLayoutHandles();
  });
  tick();
}

peBoot();
