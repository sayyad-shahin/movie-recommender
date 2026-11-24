(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const ICON = {Action:"💥",Adventure:"🧭",Animation:"🎨",Children:"🧸",Comedy:"😂",Crime:"🕵️",Documentary:"🎥",Drama:"🎭",
    Fantasy:"🧙",Horror:"👻",Musical:"🎵",Mystery:"🔍",Romance:"💕","Sci-Fi":"🚀",Thriller:"😰",War:"🪖",Western:"🤠"};
  const myRatings = new Map();   // movie id -> {title, rating}
  let lastSimilar = null;

  const hue = (s) => { let h = 0; for (const c of s) h = (h * 31 + c.charCodeAt(0)) % 360; return h; };
  const alpha = () => 1 - $("audience").value / 100;     // weight of content
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };

  async function api(url, opts) {
    const r = await fetch(url, opts);
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || "Request failed");
    return d;
  }
  function showError(msg) { const e = $("error"); e.textContent = msg || ""; e.classList.toggle("hidden", !msg); }

  function renderMovies(box, list, showScore) {
    box.innerHTML = "";
    if (!list.length) { box.appendChild(el("p", "muted", "No results.")); return; }
    list.forEach((m, k) => {
      const card = el("article", "movie");
      const poster = el("div", "poster", ICON[m.genres[0]] || "🎬");
      poster.style.background = `linear-gradient(145deg, hsl(${hue(m.title)} 55% 38%), hsl(${(hue(m.title) + 50) % 360} 60% 22%))`;
      const info = el("div", "info");
      const t = el("div", "mtitle", `${k + 1}. ${m.title} `);
      if (m.year) t.appendChild(el("span", "", `(${m.year})`));
      info.appendChild(t);
      const chips = el("div", "chips");
      m.genres.forEach((g) => chips.appendChild(el("span", "chip", g)));
      info.appendChild(chips);
      if (m.overview) info.appendChild(el("div", "ov", m.overview));
      const bits = [];
      if (m.director) bits.push("Directed by " + m.director);
      if (m.avg_rating) bits.push(`Avg rating ${m.avg_rating} (${m.votes} votes)`);
      if (bits.length) info.appendChild(el("div", "meta", bits.join(" · ")));
      if (m.reason) info.appendChild(el("div", "why", m.reason));
      card.append(poster, info);
      if (showScore && m.score !== null) card.appendChild(el("span", "badge", Math.round(Math.min(m.score, 1) * 100) + "%"));
      box.appendChild(card);
    });
  }

  // ---- search box with suggestions --------------------------------------
  function attachSearch(input, sug, onPick) {
    let timer;
    input.addEventListener("input", () => {
      clearTimeout(timer);
      const q = input.value.trim();
      if (!q) { sug.classList.add("hidden"); return; }
      timer = setTimeout(async () => {
        try {
          const list = await api("/api/movies/search?q=" + encodeURIComponent(q));
          sug.innerHTML = "";
          list.forEach((m) => {
            const b = el("button", "", m.title + " ");
            b.type = "button";
            b.appendChild(el("small", "", m.year ? `(${m.year})` : ""));
            b.addEventListener("click", () => { sug.classList.add("hidden"); input.value = ""; onPick(m); });
            sug.appendChild(b);
          });
          sug.classList.toggle("hidden", !list.length);
        } catch (e) { showError(e.message); }
      }, 180);
    });
    document.addEventListener("click", (e) => { if (!sug.contains(e.target) && e.target !== input) sug.classList.add("hidden"); });
  }

  // ---- tab 1: similar -----------------------------------------------------
  async function loadSimilar(m) {
    showError("");
    lastSimilar = m;
    $("picked").textContent = `Movies like ${m.title}${m.year ? " (" + m.year + ")" : ""}:`;
    try {
      const d = await api(`/api/movies/${m.id}/similar?n=10&audience=${(1 - alpha()).toFixed(2)}`);
      renderMovies($("out-similar"), d.results, true);
    } catch (e) { showError(e.message); }
  }

  // ---- tab 2: my ratings --------------------------------------------------
  function drawMyList() {
    const ul = $("mylist");
    ul.innerHTML = "";
    myRatings.forEach((v, id) => {
      const li = el("li");
      li.appendChild(el("span", "t", v.title));
      const sel = el("select");
      sel.setAttribute("aria-label", "Your rating for " + v.title);
      [5, 4, 3, 2, 1].forEach((n) => {
        const o = el("option", "", "★".repeat(n) + ` ${n}`); o.value = n; if (n === v.rating) o.selected = true; sel.appendChild(o);
      });
      sel.addEventListener("change", () => { v.rating = +sel.value; });
      const x = el("button", "x", "✕"); x.type = "button"; x.setAttribute("aria-label", "Remove " + v.title);
      x.addEventListener("click", () => { myRatings.delete(id); drawMyList(); });
      li.append(sel, x);
      ul.appendChild(li);
    });
  }
  async function getRecs() {
    showError("");
    if (!myRatings.size) { showError("Add and rate at least one movie first."); return; }
    const btn = $("recBtn"); btn.disabled = true;
    try {
      const ratings = {}; myRatings.forEach((v, id) => { ratings[id] = v.rating; });
      const d = await api("/api/recommend", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ratings, alpha: alpha(), n: 10 }) });
      renderMovies($("out-mine"), d.results, true);
    } catch (e) { showError(e.message); } finally { btn.disabled = false; }
  }

  // ---- tab 3: top rated ---------------------------------------------------
  async function loadTop() {
    showError("");
    try { renderMovies($("out-top"), await api("/api/top?n=12&genre=" + encodeURIComponent($("genre").value)), false); }
    catch (e) { showError(e.message); }
  }

  // ---- wiring -------------------------------------------------------------
  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t === b));
    ["similar", "mine", "top"].forEach((n) => $("tab-" + n).classList.toggle("hidden", n !== b.dataset.tab));
    $("audience").closest(".mix").classList.toggle("hidden", b.dataset.tab === "top");
    showError("");
  }));
  attachSearch($("q1"), $("sug1"), loadSimilar);
  attachSearch($("q2"), $("sug2"), (m) => { myRatings.set(m.id, { title: m.title, rating: 4 }); drawMyList(); });
  $("recBtn").addEventListener("click", getRecs);
  $("sampleBtn").addEventListener("click", async () => {
    try {
      const d = await api("/api/sample-user");
      myRatings.clear();
      d.ratings.forEach((m) => myRatings.set(m.id, { title: m.title, rating: m.rating }));
      drawMyList(); getRecs();
    } catch (e) { showError(e.message); }
  });
  $("audience").addEventListener("change", () => {
    if (!$("tab-similar").classList.contains("hidden") && lastSimilar) loadSimilar(lastSimilar);
    else if (!$("tab-mine").classList.contains("hidden") && myRatings.size) getRecs();
  });
  $("genre").addEventListener("change", loadTop);
  api("/api/genres").then((gs) => gs.forEach((g) => { const o = el("option", "", g); o.value = g; $("genre").appendChild(o); }))
    .then(loadTop).catch((e) => showError(e.message));
})();
