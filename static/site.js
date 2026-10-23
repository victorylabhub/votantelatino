(function () {
  var VL = window.VL || { lang: "es", copied: "Copiado" };

  // Cuenta regresiva
  document.querySelectorAll("#countdown").forEach(function (c) {
    var p = c.dataset.date.split("-"), e = new Date(+p[0], +p[1] - 1, +p[2]);
    var n = new Date(); n.setHours(0, 0, 0, 0);
    var d = Math.round((e - n) / 86400000);
    c.textContent = d > 1 ? c.dataset.future.replace("{n}", d)
      : d === 1 ? c.dataset.one : d === 0 ? c.dataset.today : c.dataset.past;
  });

  // Selector de estado → vote.gov
  var f = document.getElementById("picker");
  if (f) f.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var v = f.querySelector("select").value;
    if (v) window.location.href = "https://vote.gov/register/" + v;
  });

  // Compartir
  function wireShare(root) {
    root.querySelectorAll("[data-share]").forEach(function (box) {
      var u = encodeURIComponent(location.href), tx = encodeURIComponent(document.title);
      box.querySelectorAll("[data-net]").forEach(function (a) {
        var n = a.dataset.net;
        if (n === "wa") a.href = "https://wa.me/?text=" + tx + "%20" + u;
        if (n === "fb") a.href = "https://www.facebook.com/sharer/sharer.php?u=" + u;
        if (n === "x") a.href = "https://twitter.com/intent/tweet?url=" + u + "&text=" + tx;
        if (n === "copy") a.onclick = function () {
          var done = function () { var o = a.textContent; a.textContent = VL.copied; setTimeout(function () { a.textContent = o; }, 1800); };
          if (navigator.clipboard) navigator.clipboard.writeText(location.href).then(done, done); else done();
        };
      });
    });
  }
  wireShare(document);

  // Buscador de estados (resultados)
  document.querySelectorAll("[data-filter]").forEach(function (inp) {
    var items = document.querySelectorAll(inp.dataset.filter);
    var norm = function (s) { return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); };
    inp.addEventListener("input", function () {
      var q = norm(inp.value.trim());
      items.forEach(function (a) { a.hidden = q && norm(a.dataset.name).indexOf(q) === -1; });
    });
  });

  // Filtros de la tienda
  var fbtns = document.querySelectorAll(".filters [data-cat]");
  fbtns.forEach(function (b) {
    b.addEventListener("click", function () {
      fbtns.forEach(function (x) { x.classList.toggle("on", x === b); x.setAttribute("aria-pressed", x === b); });
      document.querySelectorAll(".prod").forEach(function (p) {
        p.hidden = b.dataset.cat !== "all" && p.dataset.cat !== b.dataset.cat;
      });
    });
  });

  // Señal en vivo
  var blocks = document.querySelectorAll("[data-live]");
  var navLive = document.querySelector(".nav-live");
  var current = null;
  blocks.forEach(function (sec) { var pl = sec.querySelector("[data-player]"); pl.dataset.off = pl.innerHTML; });
  var fmt = new Intl.DateTimeFormat(VL.lang === "es" ? "es-US" : "en-US",
    { weekday: "long", day: "numeric", month: "long", hour: "numeric", minute: "2-digit", timeZoneName: "short" });

  function render(data) {
    var liveId = data.live ? data.live.id : null;
    if (navLive) navLive.hidden = !liveId;
    blocks.forEach(function (sec) {
      var player = sec.querySelector("[data-player]");
      var badge = sec.querySelector("[data-badge]");
      var title = sec.querySelector("[data-live-title]");
      var up = sec.querySelector("[data-upcoming]");
      if (sec.dataset.live === "home") sec.hidden = !liveId;
      badge.hidden = !liveId;
      if (liveId && liveId !== current) {
        player.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + liveId +
          '?autoplay=1&mute=1&rel=0" title="' + data.live.title.replace(/"/g, "&quot;") +
          '" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>';
        if (sec.dataset.live === "home") title.textContent = data.live.title;
      }
      if (!liveId && current) player.innerHTML = player.dataset.off;
      var list = up.querySelector("ul");
      list.innerHTML = "";
      (data.upcoming || []).forEach(function (u) {
        var li = document.createElement("li");
        var b = document.createElement("b"); b.textContent = u.title;
        var s = document.createElement("span"); s.textContent = fmt.format(new Date(u.start));
        li.append(b, s); list.append(li);
      });
      up.hidden = !(data.upcoming && data.upcoming.length);
    });
    current = liveId;
  }
  function poll() {
    fetch("/api/live", { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d) render(d); })
      .catch(function () {});
  }
  if (blocks.length) { poll(); setInterval(poll, 60000); }
})();

// Carrusel de portada
(function () {
  var car = document.querySelector("[data-car]");
  if (!car) return;
  var figs = car.querySelectorAll(".fig");
  var colors = ["#1D6FF2", "#14A04B", "#0B2655", "#E2373A"];
  var n = figs.length, active = 0, busy = false;
  function paint() {
    var roles = {};
    roles[active] = "center"; roles[(active + n - 1) % n] = "left";
    roles[(active + 1) % n] = "right"; roles[(active + 2) % n] = "back";
    figs.forEach(function (f, i) { f.dataset.role = roles[i]; });
    car.style.setProperty("--car-bg", colors[active % colors.length]);
  }
  function go(dir) {
    if (busy) return; busy = true;
    active = dir === "next" ? (active + 1) % n : (active + n - 1) % n;
    paint(); setTimeout(function () { busy = false; }, 650);
  }
  // Avance automático cada 2 s. Se detiene solo con la pestaña oculta
  // o si el visitante pulsa el botón de pausa.
  var timer = null, paused = false;
  var pbtn = car.querySelector("[data-pause]");
  function stop() { clearInterval(timer); timer = null; }
  function start() { stop(); if (!paused && !document.hidden) timer = setInterval(function () { go("next"); }, 2000); }
  document.addEventListener("visibilitychange", start);
  if (pbtn) pbtn.addEventListener("click", function () {
    paused = !paused;
    pbtn.setAttribute("aria-pressed", paused);
    pbtn.setAttribute("aria-label", paused ? pbtn.dataset.play : pbtn.dataset.pauseLabel);
    pbtn.classList.toggle("is-paused", paused);
    paused ? stop() : start();
  });
  car.querySelectorAll("[data-dir]").forEach(function (b) {
    b.addEventListener("click", function () { go(b.dataset.dir); start(); });
  });
  car.addEventListener("keydown", function (e) {
    if (e.key === "ArrowRight") go("next"); if (e.key === "ArrowLeft") go("prev");
  });
  var x0 = null;
  car.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; }, { passive: true });
  car.addEventListener("touchend", function (e) {
    if (x0 === null) return; var dx = e.changedTouches[0].clientX - x0; x0 = null;
    if (Math.abs(dx) > 40) { go(dx < 0 ? "next" : "prev"); start(); }
  });
  paint();
  start();
})();
