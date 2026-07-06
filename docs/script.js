async function loadMenu() {
  const res = await fetch("menu.json");
  const data = await res.json();

  const app = document.getElementById("app");
  app.innerHTML = "";

  data.forEach(r => {
    const div = document.createElement("div");

    div.innerHTML = `
      <h2>${r.restaurant}</h2>
      <p><strong>Polievka:</strong> ${r.soup}</p>
      <ul>
        ${r.meals.map(m => `
          <li>${m.name} - ${m.price} €</li>
        `).join("")}
      </ul>
    `;

    app.appendChild(div);
  });
}

loadMenu();