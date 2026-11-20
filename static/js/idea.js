/* idea: todo accordion + dual-column feed */
(function () {
  var root = document.querySelector(".todo");
  if (!root) return;

  root.addEventListener("click", function (ev) {
    var btn = ev.target.closest(".todo__head");
    if (!btn || !root.contains(btn)) return;
    var item = btn.closest(".todo__item");
    if (!item) return;
    var open = item.classList.contains("is-open");
    root.querySelectorAll(".todo__item.is-open").forEach(function (el) {
      el.classList.remove("is-open");
      var h = el.querySelector(".todo__head");
      if (h) h.setAttribute("aria-expanded", "false");
    });
    if (!open) {
      item.classList.add("is-open");
      btn.setAttribute("aria-expanded", "true");
    }
  });
})();
