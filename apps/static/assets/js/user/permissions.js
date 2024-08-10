$(document).ready(function () {
    function togglePermissions(moduleId, show) {
      $('.permission-row[data-module="' + moduleId + '"]').toggle(show);
    }

    $(".module-checkbox").change(function () {
      var moduleId = $(this).attr("id");
      var isChecked = $(this).prop("checked");
      togglePermissions(moduleId, isChecked);
    });

    $(".module-checkbox").each(function () {
      var moduleId = $(this).attr("id");
      var isChecked = $(this).prop("checked");
      togglePermissions(moduleId, isChecked);
    });

    $(".select-all-permissions").change(function () {
      var isChecked = $(this).prop("checked");
      $(this).closest("tr").find('input[name="user_permissions"]').prop("checked", isChecked);
    });
  });

  function toggleSelectAllPermissions(source) {
    var checkboxes = document.querySelectorAll('input[name="user_permissions"]');
    for (var i = 0; i < checkboxes.length; i++) {
      checkboxes[i].checked = source.checked;
    }
  }

  // Obtén el campo de entrada de búsqueda
  var searchInput = document.getElementById("search-groups");

  // Agrega un evento de escucha al campo de entrada
  searchInput.addEventListener("keyup", function (event) {
    // Obtén la consulta de búsqueda
    var query = event.target.value.toLowerCase();

    // Obtén todas las filas de la tabla
    var rows = document.querySelectorAll(".module-row");

    // Itera sobre las filas
    rows.forEach(function (row) {
      // Obtén el texto de la celda del módulo
      var moduleCell = row.querySelector("td:first-child");
      var moduleText = moduleCell.textContent || moduleCell.innerText;

      // Si el texto del módulo no coincide con la consulta de búsqueda, oculta la fila
      if (moduleText.toLowerCase().indexOf(query) === -1) {
        row.style.display = "none";
      } else {
        // De lo contrario, asegúrate de que la fila sea visible
        row.style.display = "";
      }
    });
  });
