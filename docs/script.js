
async function loadMenu() {
	const res = await fetch("menu.json");
	const data = await res.json();

	render(data);
}

function render(data) {
	const app = document.getElementById("app");
	const search = document.getElementById("search");

	function draw(filter = "") {
		app.innerHTML = "";

		data.forEach(r => {
			let meals = r.meals.filter(m =>
				m.name.toLowerCase().includes(filter.toLowerCase())
			);

			if (meals.length === 0) return;

			let html = `
				<div class="card">
					<h2>🍽 ${r.restaurant}</h2>
					<p>🥣 ${r.soup}</p>
			`;

			meals.forEach(m => {
				html += `
					<div>
						${m.name}
						<span class="price">${m.price.toFixed(2)} €</span>
					</div>
				`;
			});

			html += `</div>`;

			app.innerHTML += html;
		});
	}

	search.addEventListener("input", e => {
		draw(e.target.value);
	});

	draw();
}

loadMenu();
