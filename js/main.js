(function () {
  const root = document.documentElement;
  root.classList.add("js");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const header = document.querySelector(".site-header");
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".nav");

  function onScroll() {
    if (header) header.classList.toggle("is-shrunk", window.scrollY > 24);
    const stage = document.querySelector(".hero-stage");
    if (!reduce && stage) {
      const rect = stage.getBoundingClientRect();
      const view = window.innerHeight || 800;
      if (rect.bottom > 0 && rect.top < view) {
        const shift = Math.max(-40, Math.min(40, (window.scrollY - stage.offsetTop) * 0.08));
        stage.style.setProperty("--py", shift.toFixed(2) + "px");
        const glow = stage.querySelector(".hero-glow");
        if (glow) glow.style.transform = "translateX(-50%) translateY(" + (shift * 0.45).toFixed(2) + "px)";
      }
    }
  }
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.classList.toggle("nav-open", open);
    });
    nav.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        document.body.classList.remove("nav-open");
      });
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
  }

  const revealNodes = document.querySelectorAll(".reveal");
  if (!reduce && "IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.16 }
    );
    revealNodes.forEach((node) => io.observe(node));
  } else {
    revealNodes.forEach((node) => node.classList.add("is-in"));
  }

  document.querySelectorAll("[data-count]").forEach((el) => {
    const target = parseFloat(el.dataset.count);
    const decimals = parseInt(el.dataset.decimals || "0", 10);
    const suffix = el.dataset.suffix || "";
    const finalText = target.toFixed(decimals) + suffix;
    el.textContent = finalText;
    if (reduce || !("IntersectionObserver" in window)) return;
    const start = () => {
      const t0 = performance.now();
      const dur = 1100;
      const step = (now) => {
        const p = Math.min(1, (now - t0) / dur);
        const eased = 1 - Math.pow(1 - p, 3);
        el.textContent = (target * eased).toFixed(decimals) + suffix;
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          start();
          io.disconnect();
        }
      },
      { threshold: 0.6 }
    );
    io.observe(el);
  });

  if (!reduce && window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    document.querySelectorAll(".service-card").forEach((card) => {
      card.addEventListener("pointermove", (event) => {
        const rect = card.getBoundingClientRect();
        const px = (event.clientX - rect.left) / rect.width;
        const py = (event.clientY - rect.top) / rect.height;
        const rx = (0.5 - py) * 7;
        const ry = (px - 0.5) * 9;
        card.style.transform = "rotateX(" + rx.toFixed(2) + "deg) rotateY(" + ry.toFixed(2) + "deg) translateY(-4px)";
      });
      card.addEventListener("pointerleave", () => {
        card.style.transform = "";
      });
    });
  }

  const slides = Array.from(document.querySelectorAll(".review"));
  const dots = Array.from(document.querySelectorAll(".dots button"));
  const prev = document.querySelector(".review-prev");
  const next = document.querySelector(".review-next");
  let index = 0;
  let timer = 0;

  function show(i) {
    if (!slides.length) return;
    index = (i + slides.length) % slides.length;
    slides.forEach((slide, n) => {
      const on = n === index;
      slide.classList.toggle("is-active", on);
      slide.hidden = !on;
    });
    dots.forEach((dot, n) => {
      if (n === index) dot.setAttribute("aria-current", "true");
      else dot.removeAttribute("aria-current");
    });
  }

  function queue() {
    if (reduce || slides.length < 2) return;
    window.clearInterval(timer);
    timer = window.setInterval(() => show(index + 1), 8000);
  }

  if (slides.length) {
    show(0);
    queue();
    const panel = document.querySelector(".review-panel");
    if (panel) {
      panel.addEventListener("mouseenter", () => window.clearInterval(timer));
      panel.addEventListener("mouseleave", queue);
      panel.addEventListener("focusin", () => window.clearInterval(timer));
      panel.addEventListener("focusout", queue);
    }
    if (prev) prev.addEventListener("click", () => { show(index - 1); queue(); });
    if (next) next.addEventListener("click", () => { show(index + 1); queue(); });
    dots.forEach((dot, n) => dot.addEventListener("click", () => { show(n); queue(); }));
    document.addEventListener("keydown", (event) => {
      if (!panel) return;
      const active = document.activeElement;
      if (!panel.contains(active) && active !== prev && active !== next) return;
      if (event.key === "ArrowLeft") show(index - 1);
      if (event.key === "ArrowRight") show(index + 1);
    });
  }

  const shots = Array.from(document.querySelectorAll(".shot"));
  const dialog = document.querySelector(".lightbox");
  const lbImg = dialog ? dialog.querySelector("img") : null;
  const lbCap = dialog ? dialog.querySelector("figcaption") : null;
  let lbIndex = 0;

  function openShot(i) {
    if (!dialog || !lbImg) return;
    lbIndex = i;
    const shot = shots[i];
    const img = shot.querySelector("img");
    lbImg.src = img.currentSrc || img.src;
    lbImg.alt = img.alt;
    if (lbCap) lbCap.textContent = shot.dataset.caption || img.alt;
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
  }

  shots.forEach((shot, i) => {
    shot.addEventListener("click", () => openShot(i));
  });

  if (dialog) {
    dialog.querySelector(".lb-close").addEventListener("click", () => dialog.close());
    dialog.querySelector(".lb-prev").addEventListener("click", () => openShot((lbIndex - 1 + shots.length) % shots.length));
    dialog.querySelector(".lb-next").addEventListener("click", () => openShot((lbIndex + 1) % shots.length));
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        openShot((lbIndex - 1 + shots.length) % shots.length);
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        openShot((lbIndex + 1) % shots.length);
      }
    });
  }

  const form = document.querySelector("#appointment-form");
  if (form) {
    const status = form.querySelector(".form-status");
    const preview = form.querySelector(".compose");

    function message() {
      const data = new FormData(form);
      const lines = [
        "Appointment request for Bayard Auto Center",
        "Name: " + (data.get("name") || ""),
        "Phone: " + (data.get("phone") || ""),
        "Vehicle: " + (data.get("vehicle") || "Not given"),
        "Preferred day: " + (data.get("day") || "Not given"),
        "What I need: " + (data.get("need") || "Not given")
      ];
      return lines.join("\n");
    }

    function validate() {
      let ok = true;
      form.querySelectorAll(".error").forEach((node) => (node.textContent = ""));
      const name = form.name.value.trim();
      const phone = form.phone.value.trim();
      if (!name) {
        form.querySelector("[data-error='name']").textContent = "Enter your name.";
        ok = false;
      }
      const digits = phone.replace(/\D/g, "");
      if (digits.length < 7) {
        form.querySelector("[data-error='phone']").textContent = "Enter a phone number we can reach.";
        ok = false;
      }
      return ok;
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!validate()) {
        status.textContent = "Add your name and phone, then send it again.";
        return;
      }
      const text = message();
      if (preview) {
        preview.hidden = false;
        preview.textContent = text;
      }
      const channel = (event.submitter && event.submitter.dataset.channel) || "sms";
      if (channel === "email") {
        const href = "mailto:?subject=" + encodeURIComponent("Appointment request for Bayard Auto Center") + "&body=" + encodeURIComponent(text);
        status.textContent = "Opening your email app with the request written out. Texting (904) 400-4100 is the direct line to the shop.";
        window.location.href = href;
        return;
      }
      const href = "sms:+19044004100?&body=" + encodeURIComponent(text);
      status.textContent = "Opening a text to (904) 400-4100. If a texting app does not open, copy the message below.";
      window.location.href = href;
    });

    const copyBtn = form.querySelector("[data-copy]");
    if (copyBtn) {
      copyBtn.addEventListener("click", async () => {
        if (!validate()) {
          status.textContent = "Add your name and phone first.";
          return;
        }
        const text = message();
        if (preview) {
          preview.hidden = false;
          preview.textContent = text;
        }
        try {
          await navigator.clipboard.writeText(text);
          status.textContent = "Copied. Paste it into a text to (904) 400-4100.";
        } catch (err) {
          status.textContent = "Select the message below and copy it, then text (904) 400-4100.";
        }
      });
    }
  }
})();
