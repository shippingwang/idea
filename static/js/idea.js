(() => {
  const board = document.querySelector(".desk__board");
  const bird = document.querySelector(".desk__bird");
  const photo = document.querySelector(".desk__photo");
  if (!board) return;

  const scraps = Array.from(board.querySelectorAll(".scrap"));
  if (!scraps.length) return;

  // seagull in jeju-beach / idea-bg (normalized image coords)
  const BIRD_NX = 0.485;
  const BIRD_NY = 0.495;

  let zTop = 10;
  let drag = null;

  const styleWidth = {
    slip: 240,
    receipt: 208,
    kraft: 288,
    lined: 320,
    textbook: 416,
  };

  function clamp(n, lo, hi) {
    return Math.max(lo, Math.min(hi, n));
  }

  function setPos(el, x, y, { animate = false } = {}) {
    if (animate) el.classList.add("is-settling");
    el.style.setProperty("--x", `${Math.round(x)}px`);
    el.style.setProperty("--y", `${Math.round(y)}px`);
    if (animate) {
      window.setTimeout(() => el.classList.remove("is-settling"), 520);
    }
  }

  /** Map image point → viewport under object-fit: cover + center */
  function coverPoint(nx, ny) {
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const iw = (photo && photo.naturalWidth) || 3600;
    const ih = (photo && photo.naturalHeight) || 2400;
    const scale = Math.max(vw / iw, vh / ih);
    const dw = iw * scale;
    const dh = ih * scale;
    const left = (vw - dw) / 2;
    const top = (vh - dh) / 2;
    return {
      x: left + nx * dw,
      y: top + ny * dh,
    };
  }

  function placeBird() {
    if (!bird) return;
    const { x, y } = coverPoint(BIRD_NX, BIRD_NY);
    const size = Math.max(56, Math.min(88, window.innerWidth * 0.055));
    bird.style.width = `${size}px`;
    bird.style.height = `${size}px`;
    bird.style.left = `${x}px`;
    bird.style.top = `${y}px`;
  }

  function compactLayout() {
    const pad = 12;
    const gap = 14;
    const boardW = board.clientWidth;
    const maxCol = Math.min(boardW - pad * 2, 560);
    let x = pad;
    let y = pad;
    let rowH = 0;

    const order = [...scraps].sort((a, b) => {
      const wa = styleWidth[a.dataset.style] || 280;
      const wb = styleWidth[b.dataset.style] || 280;
      return wa - wb;
    });

    order.forEach((el, i) => {
      const style = el.dataset.style || "kraft";
      const prefer = styleWidth[style] || 280;
      const w = Math.min(prefer, boardW - pad * 2);
      el.style.width = `${w}px`;
      el.style.zIndex = String(10 + i);

      const tilts = [-1.5, 1, -0.8, 1.2, -1];
      el.style.setProperty("--tilt", `${tilts[i % tilts.length]}deg`);

      if (x + w > pad + maxCol && x > pad) {
        x = pad;
        y += rowH + gap;
        rowH = 0;
      }

      setPos(el, x, y, { animate: true });
      rowH = Math.max(rowH, el.offsetHeight);
      x += w + gap;
    });

    const bottom = order.reduce((m, el) => {
      const yv = parseFloat(el.style.getPropertyValue("--y")) || 0;
      return Math.max(m, yv + el.offsetHeight);
    }, 0);
    board.style.minHeight = `${Math.max(bottom + 220, window.innerHeight * 0.72)}px`;
  }

  function onPointerDown(e) {
    if (e.button != null && e.button !== 0) return;
    if (e.target.closest("a")) return;
    const el = e.currentTarget;
    const rect = el.getBoundingClientRect();
    const x = parseFloat(el.style.getPropertyValue("--x")) || 0;
    const y = parseFloat(el.style.getPropertyValue("--y")) || 0;

    zTop += 1;
    el.style.zIndex = String(zTop);
    el.classList.add("is-dragging");
    el.setPointerCapture(e.pointerId);

    drag = {
      el,
      pointerId: e.pointerId,
      ox: e.clientX - rect.left,
      oy: e.clientY - rect.top,
      startX: x,
      startY: y,
    };
  }

  function onPointerMove(e) {
    if (!drag || e.pointerId !== drag.pointerId) return;
    const boardRect = board.getBoundingClientRect();
    const w = drag.el.offsetWidth;
    const h = drag.el.offsetHeight;
    let nx = e.clientX - boardRect.left - drag.ox;
    let ny = e.clientY - boardRect.top - drag.oy;
    nx = clamp(nx, -20, board.clientWidth - w + 20);
    ny = clamp(ny, -20, Math.max(board.clientHeight, window.innerHeight) - h + 40);
    setPos(drag.el, nx, ny);
  }

  function onPointerUp(e) {
    if (!drag || e.pointerId !== drag.pointerId) return;
    drag.el.classList.remove("is-dragging");
    try {
      drag.el.releasePointerCapture(e.pointerId);
    } catch (_) {
      /* ignore */
    }
    drag = null;
  }

  scraps.forEach((el) => {
    el.addEventListener("pointerdown", onPointerDown);
    el.addEventListener("pointermove", onPointerMove);
    el.addEventListener("pointerup", onPointerUp);
    el.addEventListener("pointercancel", onPointerUp);
  });

  if (bird) {
    bird.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      compactLayout();
    });
  }

  function layoutAll() {
    placeBird();
    compactLayout();
  }

  const ready = () => {
    layoutAll();
    window.setTimeout(layoutAll, 140);
  };

  if (photo && !photo.complete) {
    photo.addEventListener("load", ready, { once: true });
  }
  requestAnimationFrame(ready);

  let resizeTimer = 0;
  window.addEventListener("resize", () => {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(layoutAll, 120);
  });
})();
