async function loadMenu() {
  try {
    const res = await fetch("menu.json");
    const data = await res.json();

    const app = document.getElementById("app");
    app.innerHTML = "";

    data.forEach(r => {
      const div = document.createElement("div");

      let html = `<h2>${r.restaurant}</h2>`;

      if (r.type === "link_menu") {
        html += `<a href="${r.menu_url}" target="_blank">Zobraziť menu</a>`;
      }

      if (r.meals && r.meals.length > 0) {
        html += `<p><strong>Polievka:</strong> ${r.soup}</p>`;
        html += `<ul>`;

        r.meals.forEach(m => {
          html += `<li>${m.name} - ${m.price} €</li>`;
        });

        html += `</ul>`;
      }

      div.innerHTML = html;
      app.appendChild(div);
    });

  } catch (e) {
    document.getElementById("app").innerHTML =
      "❌ Chyba načítania menu";
    console.error(e);
  }
}

loadMenu();