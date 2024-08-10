// Función para filtrar las opciones de un campo de formulario
function filterOptions(searchInputId, optionsContainerClass) {
    var searchInput = document.getElementById(searchInputId);
    console.log("searchInput: ", searchInput);

    searchInput.addEventListener("keyup", function (event) {
      var query = event.target.value.toLowerCase();
      // console.log("Query: ", query); // Imprime la consulta de búsqueda

      var labels = document.querySelectorAll("." + optionsContainerClass + " label");
      //console.log("Labels: ", labels);  Imprime las etiquetas de las opciones del campo de formulario

      labels.forEach(function (label) {
        if (label.textContent.toLowerCase().indexOf(query) === -1) {
          label.style.display = "none";
        } else {
          label.style.display = "";
        }
      });
    });
  }

  // Filtrar las opciones de los campos de formulario
  filterOptions("search-companies", "companies_to_monitor");
  filterOptions("search-vehicle", "vehicles_to_monitor");
  filterOptions("search-group", "group_vehicles");
