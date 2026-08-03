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
      panels.push({ el: host, cv: cv, ctx: cv.getContext("2d"), w: 0, h: 0 });
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

  function tick() {
    for (var i = 0; i < panels.length; i++) panelFrame(panels[i], fxT);
    ringFrame(!reduce);
    if (!reduce) fxT += 1;
    requestAnimationFrame(tick);
  }

  /* ---------- column widths: drag and collapse ---------- */

  var STORE = "physearth.layout.v1";
  var RAIL = "46px";
  var DEFAULTS = { chat: "1.16fr", trace: "1fr", evid: "0.96fr" };
  var layout = { chat: DEFAULTS.chat, trace: DEFAULTS.trace, evid: DEFAULTS.evid, collapsed: {} };

  try {
    var saved = JSON.parse(window.localStorage.getItem(STORE) || "null");
    if (saved && saved.chat) layout = saved;
  } catch (e) {
    /* a broken entry just means default widths */
  }

  function stage() {
    return document.querySelector(".stage");
  }

  function panelOf(key) {
    return document.querySelector(".pe-panel--" + key);
  }

  function applyLayout() {
    var st = stage();
    if (!st) return;
    ["chat", "trace", "evid"].forEach(function (key) {
      var collapsed = !!layout.collapsed[key];
      st.style.setProperty("--w-" + key, collapsed ? RAIL : layout[key]);
      var panel = panelOf(key);
      if (panel) panel.classList.toggle("is-collapsed", collapsed);
    });
    try {
      window.localStorage.setItem(STORE, JSON.stringify(layout));
    } catch (e) {
      /* private mode; the layout just does not persist */
    }
  }

  function mountRails() {
    [["trace", "Run trace"], ["evid", "Evidence"], ["chat", "Conversation"]].forEach(function (pair) {
      var panel = panelOf(pair[0]);
      if (!panel || panel.querySelector(":scope > .panel__rail")) return;
      var rail = document.createElement("div");
      rail.className = "panel__rail";
      rail.title = "Expand " + pair[1];
      rail.innerHTML = "<span></span>";
      rail.firstChild.textContent = pair[1];
      rail.addEventListener("click", function () {
        layout.collapsed[pair[0]] = false;
        applyLayout();
      });
      panel.appendChild(rail);
    });
  }

  function mountResizers() {
    var st = stage();
    if (!st) return;
    var handles = st.querySelectorAll(".resizer");
    for (var i = 0; i < handles.length; i++) {
      if (handles[i].dataset.bound) continue;
      handles[i].dataset.bound = "1";
      handles[i].addEventListener("mousedown", startDrag);
    }
  }

  function startDrag(event) {
    var st = stage();
    if (!st) return;
    var edge = event.currentTarget.classList.contains("resizer--left") ? "left" : "right";
    var panels3 = [panelOf("chat"), panelOf("trace"), panelOf("evid")];
    if (panels3.some(function (p) { return !p; })) return;
    var startX = event.clientX;
    var widths = panels3.map(function (p) { return p.getBoundingClientRect().width; });
    var total = widths[0] + widths[1] + widths[2];
    event.preventDefault();
    document.body.classList.add("is-resizing");

    function move(e) {
      var delta = e.clientX - startX;
      var next = widths.slice();
      if (edge === "left") {
        next[0] = widths[0] + delta;
        next[1] = widths[1] - delta;
      } else {
        next[1] = widths[1] + delta;
        next[2] = widths[2] - delta;
      }
      if (next[0] < 320 || next[1] < 260 || next[2] < 260) return;
      layout.chat = ((next[0] / total) * 3).toFixed(3) + "fr";
      layout.trace = ((next[1] / total) * 3).toFixed(3) + "fr";
      layout.evid = ((next[2] / total) * 3).toFixed(3) + "fr";
      applyLayout();
    }

    function stop() {
      document.body.classList.remove("is-resizing");
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", stop);
    }

    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", stop);
  }

  /* ---------- state that must survive a Gradio re-render ---------- */

  var openKeys = {};
  var activeTab = null;
  var activeScope = null;

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

  function scrollToEnd(node) {
    if (node) node.scrollTop = node.scrollHeight;
  }

  function autoScroll() {
    scrollToEnd(document.getElementById("pe-chat-scroll"));
    var trace = document.querySelector(".pe-panel--trace .subpanel__scroll");
    scrollToEnd(trace);
  }

  /* ---------- clicks: examples, collapse buttons, citation jumps ---------- */

  function textarea() {
    var box = document.getElementById("pe-input");
    return box ? box.querySelector("textarea") : null;
  }

  function setQuestion(text) {
    var area = textarea();
    if (!area) return false;
    var setter = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype,
      "value"
    ).set;
    setter.call(area, text);
    area.dispatchEvent(new Event("input", { bubbles: true }));
    return true;
  }

  document.addEventListener("click", function (event) {
    var chip = event.target.closest ? event.target.closest("[data-example]") : null;
    if (chip) {
      event.preventDefault();
      if (setQuestion(chip.getAttribute("data-example"))) {
        var send = document.getElementById("pe-send");
        if (send) setTimeout(function () { send.click(); }, 30);
      }
      return;
    }

    var toggle = event.target.closest ? event.target.closest("[data-collapse]") : null;
    if (toggle) {
      event.preventDefault();
      var key = toggle.getAttribute("data-collapse");
      layout.collapsed[key] = !layout.collapsed[key];
      applyLayout();
      return;
    }

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
      if (layout.collapsed.evid) {
        layout.collapsed.evid = false;
        applyLayout();
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

  /* Enter sends, shift+Enter makes a new line. */
  document.addEventListener("keydown", function (event) {
    var area = textarea();
    if (!area || event.target !== area) return;
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      var send = document.getElementById("pe-send");
      if (send) send.click();
    }
  });

  /* ---------- react to every Gradio re-render ---------- */

  var pending = null;
  var observer = new MutationObserver(function () {
    if (pending) return;
    pending = requestAnimationFrame(function () {
      pending = null;
      mountCanvases();
      mountRails();
      mountResizers();
      applyLayout();
      restoreState(document);
      autoScroll();
      document.body.classList.toggle(
        "is-reasoning",
        !!document.querySelector("[data-running]")
      );
    });
  });
  observer.observe(app, { childList: true, subtree: true });

  mountCanvases();
  mountRails();
  mountResizers();
  applyLayout();
  restoreState(document);
  resizeRing();
  window.addEventListener("resize", function () {
    resizeRing();
  });
  tick();
}

peBoot();
