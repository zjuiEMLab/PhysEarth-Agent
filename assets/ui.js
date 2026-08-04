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
    /* Only follow the newest content when the reader is already at the bottom. Pinning
       unconditionally makes it impossible to read back during a run. */
    if (!node) return;
    if (node.scrollHeight - node.scrollTop - node.clientHeight < 48) {
      node.scrollTop = node.scrollHeight;
    }
  }

  function autoScroll() {
    scrollToEnd(document.getElementById("pe-chat-scroll"));
    var trace = document.querySelector(".pe-panel--trace .subpanel__scroll");
    scrollToEnd(trace);
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

  /* ---------- answer the click before the server can ----------

     The server does 0.2 ms of work to build the first frame; everything the visitor
     experiences as lag is the round trip to it. So the click paints its own consequence
     immediately -- the running glow, the question in the transcript, the emptied box --
     and the first real frame replaces that a moment later with the authoritative version.
     Nothing here decides anything; it only shows sooner what is already going to happen. */

  var pendingUntil = 0;

  function optimisticSend() {
    var area = textarea();
    var text = area ? area.value.trim() : "";
    if (!text) return;
    pendingUntil = Date.now() + 20000;
    document.body.classList.add("is-reasoning");
    var live = document.querySelector("#pe-chat-scroll .pe-slot:last-child");
    if (live) {
      live.innerHTML =
        "<div class='msg-group'><div class='msg msg--user'><div class='msg__head'>" +
        "<span class='msg__who'>you</span><span class='msg__rule'></span></div>" +
        "<div class='msg__body'>" + escapeHtml(text) + "</div></div>" +
        "<div class='msg msg--agent'><div class='msg__head'>" +
        "<span class='msg__who'>physearth</span><span class='msg__rule'></span></div>" +
        "<div class='msg__body'><p class='hint'>Waiting for the first token.</p>" +
        "<span class='caret'></span></div></div></div>";
    }
    var hint = document.querySelector("#pe-chat-scroll .pane-empty");
    if (hint && hint.parentNode) hint.parentNode.removeChild(hint);
    autoScroll();

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

  var TRACE_EMPTY =
    "<div class='pane-empty'><div class='pane-empty__title'>Nothing has run yet</div>" +
    "<div class='pane-empty__hint'>Every model call, every tool call and every system " +
    "refusal appears here as it happens.</div></div>";

  function optimisticClear() {
    pendingUntil = 0;
    document.body.classList.remove("is-reasoning");
    var slots = document.querySelectorAll("#pe-chat-scroll .pe-slot");
    for (var i = 0; i < slots.length; i++) slots[i].innerHTML = "<div class='msg-group'></div>";
    /* The run trace is the panel the visitor is watching, so it has to empty with the
       conversation rather than a round trip later. Its meters keep their last values for
       that moment; the frame coming back replaces the whole panel. */
    var trace = document.querySelector(".pe-panel--trace .subpanel__scroll");
    if (trace) trace.innerHTML = TRACE_EMPTY;
    var approve = document.querySelector(".approve");
    if (approve) approve.setAttribute("hidden", "");
    var box = textarea();
    if (box) box.value = "";
  }

  function escapeHtml(value) {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#x27;")
      .replace(/\n/g, "<br>");
  }

  document.addEventListener("click", function (event) {
    var target = event.target.closest ? event.target.closest("button") : null;
    if (!target) return;
    if (target.id === "pe-send") optimisticSend();
    if (target.id === "pe-clear") optimisticClear();
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
      silenceBridge();
      if (reduce && drawnOnce) {
        for (var i = 0; i < panels.length; i++) panelFrame(panels[i], fxT);
      }
      restoreState(document);
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
    var bridge = document.getElementById("pe-model-bridge");
    if (!bridge) return;
    bridge.setAttribute("aria-hidden", "true");
    var fields = bridge.querySelectorAll("textarea, input");
    for (var i = 0; i < fields.length; i++) fields[i].setAttribute("tabindex", "-1");
  }

  mountCanvases();
  silenceBridge();
  restoreState(document);
  resizeRing();
  window.addEventListener("resize", function () {
    resizeRing();
  });
  tick();
}

peBoot();
