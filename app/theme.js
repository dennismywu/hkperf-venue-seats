// Light/dark toggle shared by the viewer and the planner.
// The choice lasts for this page view only: the site keeps no browser storage (see Privacy and usage),
// so a reload returns to the system preference.
(function () {
  const root = document.documentElement;
  const btn = document.getElementById("theme");
  if (!btn) return;
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  // what is actually shown: an explicit choice, else the system preference
  const current = () => root.dataset.theme || (mq.matches ? "dark" : "light");
  function render() {
    const dark = current() === "dark";
    btn.setAttribute("aria-checked", String(dark));
    btn.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
    btn.title = btn.getAttribute("aria-label");
  }
  btn.addEventListener("click", () => {
    root.dataset.theme = current() === "dark" ? "light" : "dark";
    render();
    document.dispatchEvent(new Event("themechange"));
  });
  mq.addEventListener("change", () => { render(); document.dispatchEvent(new Event("themechange")); });
  render();
})();
