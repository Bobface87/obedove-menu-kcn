async function loadMenu() {
  try {
    const res = await fetch("menu.json");
    const data = await res.json();

    const app = document.getElementById("app");
    app.innerHTML = "";

    data.forEach(r => {

      const div = document.createElement("div");
      div.className = "card";

      let html = `<h2>${r.restaurant}</h2>`;

      // Reštaurácie iba s odkazom
      if (r.type === "link_menu") {
        html += `<a href="${r.menu_url}" target="_blank">Zobraziť menu</a>`;
      }

      // Quo Vadis - obrázok menu s otvorením vo veľkom
      if (r.type === "image_menu") {
        html += `
          <a href="${r.image_url}" target="_blank">
            <img
              src="${r.image_url}"
              alt="Denné menu"
              class="qv-image">
          </a>
        `;
      }

      // Klasické menu
      if (r.meals && r.meals.length > 0) {

        html += `<p><strong>Polievka:</strong> ${r.soup}</p>`;

        html += `<ul>`;

        r.meals.forEach(m => {

          html += `<li>`;

          if (m.menu) {
            html += `<strong>${m.menu}.</strong> `;
          }

          html += `${m.name} - ${m.price}`;

          html += `</li>`;

        });

        html += `</ul>`;

        if (r.dessert) {

          html += `<p><strong>🍰 Dezert:</strong> `;

          html += r.dessert.name;

          if (r.dessert.weight) {
            html += ` (${r.dessert.weight})`;
          }

          if (r.dessert.delivery === false) {
            html += ` <em>– neplatí pre donášku</em>`;
          }

          html += `</p>`;
        }
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