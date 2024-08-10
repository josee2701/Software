$(document).ready(function () {
    function initializeSelect2() {
      console.log("Inicializando Select2");
      $("#id_vehicle").select2({
        dropdownParent: $("#miModal"),
      });

      // Añadir la clase form-control al contenedor correcto
      $(".select2-container").addClass("form-control");

      // Eliminar el estilo de ancho en línea
      $(".select2-container").css("width", "");

      console.log("Select2 inicializado");
    }

    // Inicializar Select2 cuando el documento esté listo
    initializeSelect2();

    // Inicializar Select2 cada vez que el modal se muestra
    $("#miModal").on("shown.bs.modal", function () {
      console.log("Modal mostrado");
      initializeSelect2();
      // Forzar el foco en el primer campo de Select2
      $("#id_vehicle").select2("open").select2("close");
    });
  });
