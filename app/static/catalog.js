// Pull catalog from the orders API (proxied via /api/catalog) and render
// a featured grid of products.
(function () {
  const ICONS = {
    ski: "🎿", "ski-touring": "🥾", "ski-powder": "❄️",
    snowboard: "🏂", "ski-boot": "🥾",
    jacket: "🧥",
    "bike-mtb": "🚵", "bike-fs": "🚵‍♂️", "bike-gravel": "🚴", "bike-road": "🚴‍♀️",
    helmet: "⛑️", pack: "🎒",
  };
  const grid = document.getElementById("catalog-grid");
  fetch("/api/catalog")
    .then((r) => r.json())
    .then((items) => {
      grid.innerHTML = "";
      items.slice(0, 8).forEach((it) => {
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `
          <div class="icon">${ICONS[it.icon] || "🏔️"}</div>
          <h3>${it.name}</h3>
          <div class="desc">${it.short_description}</div>
          <div class="price">$${it.price_usd.toFixed(0)}</div>
        `;
        grid.appendChild(card);
      });
    })
    .catch(() => {
      grid.innerHTML = '<div class="card placeholder">Catalog offline</div>';
    });
})();
