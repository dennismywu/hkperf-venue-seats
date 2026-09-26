// Usage statistics: page views and named interface events (e.g. "planner-category-added"), never
// anything a visitor types or selects. Sent to GoatCounter when window.SEATS_CONFIG.goatcounter holds
// its endpoint (e.g. "https://stats.denniswu.org/count"); otherwise nothing is loaded or sent.
// The viewer starts statistics on load; the planner only after the visitor agrees to its terms.
(function () {
  const endpoint = (window.SEATS_CONFIG || {}).goatcounter || "";
  let started = false;
  window.statsEnabled = !!endpoint;
  window.startStats = function () {
    if (!endpoint || started) return;
    started = true;
    const s = document.createElement("script");
    s.async = true;
    s.dataset.goatcounter = endpoint;
    s.src = endpoint.replace(/\/count$/, "/count.js");
    document.head.append(s);
  };
  window.track = function (name) {
    if (started && window.goatcounter && window.goatcounter.count)
      window.goatcounter.count({ path: name, title: name, event: true });
  };
})();
