async function loadMenu() {
  const res = await fetch("menu.json");
  const data = await res.json();

  const app = document.getElementById("app");
  app.innerHTML = "";

  data.forEach(r => {
    const div = document.createElement("div");

    let html = `<h2>${r.restaurant}</h2>`;

    // 🔥 LINK-BASED RESTAURÁCIE (Quo Vadis)
    if (r.type === "link_menu") {
      html += `<a href="${r.menu_url}" target="_blank">Zobraziť menu</a>`;
    }

    // 🔥 klasické menu (Hoffer atď.)
    if (r.meals && r.meals.length > 0) {
      if (r.soup) {
        html += `<p><strong>Polievka:</strong> ${r.soup}</p>`;
      }

      html += `<ul>`;

      r.meals.forEach(m => {
        html += `<li>${m.name} - ${m.price} €</li>`;
      });

      html += `</ul>`;
    }

    div.innerHTML = html;
    app.appendChild(div);
  });
}

loadMenu();