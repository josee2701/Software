$(document).ready(function () {
    // Función para mostrar u ocultar permisos basados en el estado del checkbox del grupo
    function togglePermissions(moduleId, show) {
      var permissions = $('.permission-row[data-module="' + moduleId + '"]');
      permissions.toggle(show);
      if (!show) {
        permissions.find('input[type="checkbox"]').prop('checked', false);
      }
    }

    // Función para actualizar el estado del checkbox "All" basado en los permisos seleccionados
    function updateSelectAll(moduleId) {
      var allPermissions = $('.permission-row[data-module="' + moduleId + '"] input[name="user_permissions"]');
      var allChecked = true;
      allPermissions.each(function () {
        if (!$(this).prop("checked")) {
          allChecked = false;
        }
      });
      $('.select-all-permissions[data-module="' + moduleId + '"]').prop("checked", allChecked);
    }

    // Evento para manejar el cambio en los checkboxes de permisos individuales
    $('input[name="user_permissions"]').change(function () {
      var moduleId = $(this).closest('tr').find('.select-all-permissions').data("module");
      updateSelectAll(moduleId);
    });

    // Evento para manejar el cambio en los checkboxes de grupo
    $(".module-checkbox").change(function () {
      var moduleId = $(this).attr("id").replace("group_", "");
      var isChecked = $(this).prop("checked");
      togglePermissions(moduleId, isChecked);
      updateSelectAll(moduleId);
    });

    // Evento para manejar el cambio en el checkbox "All"
    $(".select-all-permissions").change(function () {
      var isChecked = $(this).prop("checked");
      var moduleId = $(this).data("module");
      $(this).closest("tr").find('input[name="user_permissions"]').prop("checked", isChecked);
      updateSelectAll(moduleId);
    });

    // Ajusta la visibilidad de los permisos al cargar la página
    $(".module-checkbox").each(function () {
      var moduleId = $(this).attr("id").replace("group_", "");
      var isChecked = $(this).prop("checked");
      togglePermissions(moduleId, isChecked);
      updateSelectAll(moduleId);
    });

    // Agrega un evento de escucha al campo de entrada
    $("#search-groups").on("keyup", function () {
      // Obtén la consulta de búsqueda
      var query = $(this).val().toLowerCase();

      // Obtén todas las filas de la tabla
      var rows = $(".module-row");

      // Itera sobre las filas
      rows.each(function () {
        // Obtén el texto de la celda del módulo
        var moduleText = $(this).find("td:first-child").text().toLowerCase();

        // Si el texto del módulo no coincide con la consulta de búsqueda, oculta la fila
        $(this).toggle(moduleText.indexOf(query) !== -1);
      });
    });
  });
