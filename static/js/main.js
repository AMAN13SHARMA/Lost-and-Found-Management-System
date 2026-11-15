/* ==========================================================================
   NITC Lost & Found - client-side interactions (vanilla JavaScript)
   All rules are re-checked on the server; JS only improves usability (NFR-12).
   ========================================================================== */
(function () {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  /* ---------- Mobile navigation ---------- */
  const toggle = $(".nav-toggle");
  const nav = $("#site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
  }

  /* ---------- Flash messages: dismiss + auto-dismiss success/info ---------- */
  $$(".alert").forEach((alert) => {
    const close = $(".alert-close", alert);
    const remove = () => {
      alert.style.transition = "opacity .25s, transform .25s";
      alert.style.opacity = "0";
      alert.style.transform = "translateY(-6px)";
      setTimeout(() => alert.remove(), 260);
    };
    if (close) close.addEventListener("click", remove);
    if (alert.hasAttribute("data-autodismiss") &&
        (alert.classList.contains("alert-success") || alert.classList.contains("alert-info"))) {
      setTimeout(remove, 7000);
    }
  });

  /* ---------- Confirmation for state-changing actions ---------- */
  $$("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!window.confirm(form.getAttribute("data-confirm"))) {
        e.preventDefault();
        return;
      }
      const btn = $("button[type=submit]", form);
      if (btn) { btn.disabled = true; btn.textContent = "Please wait…"; }
    });
  });

  /* ---------- Photo upload: preview + size/type check (FR-09) ---------- */
  const dropzone = $("#photo-dropzone");
  if (dropzone) {
    const input = $("input[type=file]", dropzone);
    const preview = $("#photo-preview");
    const previewImg = preview ? $("img", preview) : null;
    const text = $("#photo-text");
    const errorEl = $("#photo-client-error");
    const maxBytes = parseInt(input.dataset.maxBytes || "5242880", 10);
    const allowed = ["image/jpeg", "image/png", "image/webp"];

    const showError = (msg) => {
      errorEl.textContent = msg;
      errorEl.hidden = !msg;
    };

    const handle = () => {
      showError("");
      const file = input.files && input.files[0];
      if (!file) {
        preview.hidden = true;
        text.hidden = false;
        return;
      }
      if (!allowed.includes(file.type)) {
        showError("Unsupported photo type. Please choose a JPEG, PNG or WebP image.");
        input.value = "";
        preview.hidden = true; text.hidden = false;
        return;
      }
      if (file.size > maxBytes) {
        const mb = (file.size / 1048576).toFixed(1);
        showError(`The photo is too large (${mb} MB). The maximum allowed size is ${Math.round(maxBytes / 1048576)} MB.`);
        input.value = "";
        preview.hidden = true; text.hidden = false;
        return;
      }
      const reader = new FileReader();
      reader.onload = (ev) => {
        previewImg.src = ev.target.result;
        preview.hidden = false;
        text.hidden = true;
      };
      reader.readAsDataURL(file);
    };

    input.addEventListener("change", handle);
    ["dragenter", "dragover"].forEach((evt) =>
      dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add("dragover"); }));
    ["dragleave", "drop"].forEach((evt) =>
      dropzone.addEventListener(evt, () => dropzone.classList.remove("dragover")));
  }

  /* ---------- Prevent double submission of the report form ---------- */
  const itemForm = $("#item-form");
  if (itemForm) {
    itemForm.addEventListener("submit", () => {
      const btn = $("button[type=submit]", itemForm);
      if (btn) { btn.disabled = true; btn.textContent = "Submitting…"; }
    });
  }

  /* ---------- Show / hide password ---------- */
  $$("[data-toggle-password]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = btn.parentElement.querySelector("input");
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
    });
  });

  /* ---------- Character counter for the claim explanation ---------- */
  $$("textarea[data-counter]").forEach((ta) => {
    const max = parseInt(ta.getAttribute("maxlength") || "1000", 10);
    const min = parseInt(ta.getAttribute("minlength") || "0", 10);
    const counter = document.createElement("small");
    counter.className = "char-counter";
    ta.insertAdjacentElement("afterend", counter);
    const update = () => {
      const len = ta.value.trim().length;
      counter.textContent = len < min ? `${len} / ${max} · at least ${min} characters` : `${len} / ${max}`;
      counter.classList.toggle("low", len < min);
    };
    ta.addEventListener("input", update);
    update();
  });

  /* ---------- Tabs (My Items) ---------- */
  $$("[data-tabs]").forEach((root) => {
    const tabs = $$("[data-tab]", root);
    const panels = $$("[data-panel]", root);
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const name = tab.dataset.tab;
        tabs.forEach((t) => {
          const active = t === tab;
          t.classList.toggle("active", active);
          t.setAttribute("aria-selected", String(active));
        });
        panels.forEach((p) => { p.hidden = p.dataset.panel !== name; });
        const url = new URL(window.location);
        url.searchParams.set("tab", name);
        window.history.replaceState({}, "", url);
      });
    });
  });

  /* ---------- Filter bar: auto-submit when a dropdown changes ---------- */
  const filterForm = $("#filter-form");
  if (filterForm) {
    $$("select", filterForm).forEach((sel) => sel.addEventListener("change", () => filterForm.submit()));
  }

  /* ---------- Dashboard: count-up animation ---------- */
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    $$("[data-countup]").forEach((el) => {
      const target = parseInt(el.textContent, 10) || 0;
      if (target <= 0) return;
      let cur = 0;
      const step = Math.max(1, Math.ceil(target / 20));
      el.textContent = "0";
      const timer = setInterval(() => {
        cur = Math.min(target, cur + step);
        el.textContent = String(cur);
        if (cur >= target) clearInterval(timer);
      }, 30);
    });
  }
})();
