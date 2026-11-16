(() => {
  const nodes = Array.from(document.querySelectorAll(".reveal"));
  if (!nodes.length) return;

  if (!("IntersectionObserver" in window)) {
    nodes.forEach((el) => el.classList.add("is-in"));
    return;
  }

  const io = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.classList.add("is-in");
        io.unobserve(entry.target);
      }
    },
    { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
  );

  nodes.forEach((el, i) => {
    el.style.transitionDelay = `${Math.min(i * 70, 280)}ms`;
    io.observe(el);
  });
})();
