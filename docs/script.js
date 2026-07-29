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
        "Smíchov"
      ],

      [
        "Sakura",
        "Buganka"
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




        /*
          BUGANKA OCR MENU
          - platí iba pre Buganku
          - ostatné reštaurácie nemeníme
        */

        if (
          r.restaurant === "Buganka"
          &&
          r.type === "ocr_menu"
        ) {


          if (
            r.soup
            &&
            r.soup.items
            &&
            r.soup.items.length
          ) {


            html += `

              <p>

                <strong>🍲 Polievky:</strong>

              </p>

              <ul>

            `;


            r.soup.items.forEach(item => {

              html += `

                <li>

                  ${item}

                </li>

              `;

            });


            html += `

              </ul>

              <p>

                <strong>Cena: ${r.soup.price}</strong>

              </p>

            `;

          }





          if (
            r.meals
            &&
            r.meals.items
            &&
            r.meals.items.length
          ) {


            html += `

              <p>

                <strong>🍽 Hlavné jedlá:</strong>

              </p>

              <ul>

            `;


            r.meals.items.forEach(item => {


              html += `

                <li>

                  ${item}

                </li>

              `;


            });


            html += `

              </ul>

              <p>

                <strong>Cena: ${r.meals.price}</strong>

              </p>

            `;


          }





          if (
            r.dessert
            &&
            r.dessert.items
            &&
            r.dessert.items.length
          ) {


            html += `

              <p>

                <strong>🍰 Dezert:</strong>

              </p>


              <ul>

            `;


            r.dessert.items.forEach(item => {


              html += `

                <li>

                  ${item}

                </li>

              `;


            });


            html += `

              </ul>


              <p>

                <strong>Cena: ${r.dessert.price}</strong>

              </p>

            `;


          }


        }





        /*
          Obrázkové menu
          (ostatné reštaurácie)
        */

        else if (r.type === "image_menu") {


          html += `

              <img

                src="${r.image_url}"

                alt="Denné menu"

                class="qv-image">

          `;

        }






        /*
          Klasické menu
        */

        if (
          r.type !== "image_menu"
          &&
          r.restaurant !== "Buganka"
          &&
          r.meals
          &&
          Array.isArray(r.meals)
        ) {



          if (r.starter) {

            html += `

              <p>

                <strong>🥗 Predjedlo:</strong>

                ${r.starter}

              </p>

            `;

          }





          if (r.soup) {

            html += `

              <p>

                <strong>🍲 Polievka:</strong>

                ${r.soup}

              </p>

            `;

          }





          if (r.extra_soup) {

            html += `

              <p>

                <strong>🍲 Každodenná polievka:</strong>

                ${r.extra_soup}

              </p>

            `;

          }





          html += `<ul>`;



          r.meals.forEach(m => {


            html += `<li>`;


            if (m.menu) {

              html += `<strong>${m.menu}.</strong> `;

            }


            html += `<strong>${m.name}</strong>`;



            if (m.description) {

              html += `

                <br>

                <span class="description">

                  ${m.description}

                </span>

              `;

            }



            if (m.price) {

              html += `

                <br>

                <strong>${m.price}</strong>

              `;

            }



            html += `</li>`;


          });



          html += `</ul>`;

        }






        /*
          Sakura
        */

        if (r.restaurant === "Sakura") {



          if (
            r.soups
            &&
            r.soups.length > 0
          ) {


            html += `

              <p>

                <strong>🍲 Polievky:</strong>

              </p>

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



            if (
              items
              &&
              items.length > 0
            ) {


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