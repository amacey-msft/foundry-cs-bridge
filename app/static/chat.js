// Granite Peak — chat widget client.
// Streams from /api/chat (SSE). Single concierge — Foundry agent decides
// whether to delegate to the Copilot Studio orders agent for order/return
// questions. Consumer never sees the seam.

(function () {
  const launcher = document.getElementById("chat-launcher");
  const panel    = document.getElementById("chat-panel");
  const closeBtn = document.getElementById("chat-close");
  const heroBtn  = document.getElementById("open-chat");
  const log      = document.getElementById("chat-log");
  const form     = document.getElementById("chat-form");
  const input    = document.getElementById("chat-input");

  let sessionId = null;
  let greeted   = false;

  function openPanel() {
    panel.hidden = false;
    input.focus();
    if (!greeted) {
      addBot(
        "Hi — I'm the Granite Peak concierge. Ask me about a ski, a bike, " +
        "your last order, our return policy, or anything else."
      );
      greeted = true;
    }
  }
  function closePanel() { panel.hidden = true; }

  launcher.addEventListener("click", openPanel);
  heroBtn.addEventListener("click", openPanel);
  closeBtn.addEventListener("click", closePanel);

  function addUser(text) {
    const el = document.createElement("div");
    el.className = "msg user";
    el.textContent = text;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
  }
  function addBot(text, opts) {
    const wrap = document.createElement("div");
    wrap.className = "msg bot" + (opts && opts.thinking ? " thinking" : "");
    const badge = document.createElement("span");
    badge.className = "badge badge-concierge";
    badge.textContent = "Concierge";
    const body = document.createElement("span");
    body.className = "msg-body";
    body.textContent = text;
    wrap.appendChild(badge);
    wrap.appendChild(body);
    log.appendChild(wrap);
    log.scrollTop = log.scrollHeight;
    wrap.badgeEl = badge;
    wrap.bodyEl = body;
    return wrap;
  }

  function setSource(bubble, source) {
    if (!bubble || !bubble.badgeEl) return;
    if (source === "orders_agent") {
      bubble.badgeEl.textContent = "Orders Agent";
      bubble.badgeEl.className = "badge badge-orders";
    } else {
      bubble.badgeEl.textContent = "Concierge";
      bubble.badgeEl.className = "badge badge-concierge";
    }
  }

  async function sendMessage(text) {
    addUser(text);
    const placeholder = addBot("…", { thinking: true });
    let acc = "";

    try {
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      if (!r.ok || !r.body) {
        placeholder.classList.remove("thinking");
        placeholder.textContent = "(sorry — couldn't reach the concierge)";
        return;
      }
      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        let idx;
        while ((idx = buf.indexOf("\n\n")) !== -1) {
          const frame = buf.slice(0, idx).trim();
          buf = buf.slice(idx + 2);
          if (!frame.startsWith("data:")) continue;
          const json = frame.slice(5).trim();
          let evt;
          try { evt = JSON.parse(json); } catch { continue; }

          if (evt.type === "session" && evt.session_id) {
            sessionId = evt.session_id;
          } else if (evt.type === "source") {
            setSource(placeholder, evt.source);
          } else if (evt.type === "delta" && evt.text) {
            if (placeholder.classList.contains("thinking")) {
              placeholder.classList.remove("thinking");
              placeholder.bodyEl.textContent = "";
            }
            acc += evt.text;
            placeholder.bodyEl.textContent = acc;
            log.scrollTop = log.scrollHeight;
          } else if (evt.type === "error") {
            placeholder.classList.remove("thinking");
            placeholder.bodyEl.textContent = "(error: " + (evt.message || "unknown") + ")";
          }
        }
      }
      if (placeholder.classList.contains("thinking")) {
        placeholder.classList.remove("thinking");
        placeholder.bodyEl.textContent = "(no reply)";
      }
    } catch (err) {
      placeholder.classList.remove("thinking");
      placeholder.bodyEl.textContent = "(network error: " + err.message + ")";
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    sendMessage(text);
  });
})();
