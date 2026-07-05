// Constrói o layout comum (sidebar) em todas as páginas internas do painel.

function renderLayout(activePage, contentHtml) {
  const nav = [
    { href: "dashboard.html", label: "📊 Dashboard", key: "dashboard" },
    { href: "licenses.html", label: "🔑 Licenças", key: "licenses" },
    { href: "versions.html", label: "⬆️ Versões", key: "versions" },
    { href: "maintenance.html", label: "🛠️ Manutenção", key: "maintenance" },
  ];

  const navHtml = nav
    .map(
      (item) =>
        `<a href="${item.href}" class="${item.key === activePage ? "active" : ""}">${item.label}</a>`
    )
    .join("");

  document.getElementById("app").innerHTML = `
    <div class="row g-0">
      <div class="col-12 col-md-2 sidebar p-3">
        <div class="brand">🔐 Painel de Licenças</div>
        <nav class="mt-3">${navHtml}</nav>
        <a href="#" onclick="logout(); return false;" class="mt-4 text-danger">🚪 Sair</a>
      </div>
      <div class="col-12 col-md-10 p-4">
        ${contentHtml}
      </div>
    </div>
  `;
}
