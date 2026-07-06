async function loadMenu() {
  const res = await fetch("menu.json");
  const data = await res.json();

  const app = document.getElementById("app");
  app.innerHTML = "";

  data.forEach(r => {
    const div = document.createElement("div");
    div.className = "restaurant";

    let html = `<h2>${r.restaurant}</h2>`;

    if (r.soup) {
      html += `<p><strong>Polievka:</strong> ${r.soup}</p>`;
    }

    html += `<ul>`;

    r.meals.forEach(m => {
      html += `<li>
        ${m.name}
        ${m.price !== null ? ` - ${m.price} €` : ""}
      </li>`;
    });

    html += `</ul>`;

    div.innerHTML = html;
    app.appendChild(div);
  });
}

loadMenu();
