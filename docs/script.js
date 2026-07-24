async function loadMenu() {

  try {

    const res = await fetch("menu.json");

    const data = await res.json();


    const app = document.getElementById("app");

    app.innerHTML = "";



    const rows = [

      [
        "Hoffer",
        "Hospúdka u Slováka",
        "Kotolňa"
      ],

      [
        "Quo Vadis",
        "Bellissimo",
        "Buganka"
      ],

      [
        "Sakura"
      ],

      [
        "Smíchov"
      ]

    ];



    rows.forEach(row => {


      const rowDiv = document.createElement("div");

      rowDiv.className = "menu-row";



      row.forEach(name => {


        const r = data.find(
          item => item.restaurant === name
        );


        if (!r) return;



        const div = document.createElement("div");

        div.className = "card";



        let html = `<h2>${r.restaurant}</h2>`;



        // Obrázkové menu

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



          if (r.soup) {

            html += `

              <p>

                <strong>Polievka:</strong>

                ${r.soup}

              </p>

            `;

          }



          html += `<ul>`;



          r.meals.forEach(m => {



            html += `<li>`;



            if (m.menu) {

              html += `<strong>${m.menu}.</strong> `;

            }



            html += `${m.name}`;



            if (m.price) {

              html += ` - <strong>${m.price}</strong>`;

            }



            html += `</li>`;



          });



          html += `</ul>`;

        }





        // Sakura menu

        if (r.restaurant === "Sakura") {



          if (r.soups && r.soups.length > 0) {


            html += `

              <p><strong>🍲 Polievky:</strong></p>

              <ul>

            `;


            r.soups.forEach(s => {


              html += `

                <li>

                  ${s.name} - ${s.price}

                </li>

              `;


            });


            html += `</ul>`;

          }





          const sections = [

            ["🍣 Sushi", r.sushi],

            ["🍜 Denné menu", r.daily_menu],

            ["📅 Týždenné menu", r.weekly_menu]

          ];





          sections.forEach(([title, items]) => {



            if (items && items.length > 0) {



              html += `<p><strong>${title}:</strong></p>`;

              html += `<ul>`;




              items.forEach(m => {



                html += `<li>`;



                if (m.number) {

                  html += `<strong>${m.number}.</strong> `;

                }



                html += m.name;



                if (m.price) {

                  html += ` - <strong>${m.price}</strong>`;

                }



                html += `</li>`;



              });



              html += `</ul>`;

            }



          });



        }





        // Dezert

        if (r.dessert) {



          html += `

            <p>

              <strong>🍰 Dezert:</strong>

              ${r.dessert.name}

          `;



          if (r.dessert.weight) {

            html += ` (${r.dessert.weight})`;

          }



          if (r.dessert.delivery === false) {

            html += ` <em>– neplatí pre donášku</em>`;

          }



          html += `</p>`;

        }




        div.innerHTML = html;


        rowDiv.appendChild(div);



      });



      app.appendChild(rowDiv);



    });



  }


  catch (e) {



    document.getElementById("app").innerHTML =

      "❌ Chyba načítania menu";



    console.error(e);



  }


}



loadMenu();