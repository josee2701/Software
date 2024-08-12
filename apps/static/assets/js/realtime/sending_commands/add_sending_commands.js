$(document).ready(function () {
  // Función para inicializar Select2
  function initializeSelect2() {
      console.log("Inicializando Select2");
      var deviceId = $('#id_device');
      deviceId.select2({
          dropdownParent: $("#miModal"),
      });

      // Añadir la clase form-control al contenedor correcto
      $(".select2-container").addClass("form-control");

      // Eliminar el estilo de ancho en línea
      $(".select2-container").css("width", "");

      console.log("Select2 inicializado");

      // Adjuntar el evento change después de inicializar Select2
      deviceId.on("change", function() {
          var deviceIdValue = this.value;
          console.log("Device ID cambiado a:", deviceIdValue);
          if (deviceIdValue) {
              fetchCommands(deviceIdValue);
          }
      });
  }

  // Inicializar Select2 cuando el documento esté listo
  initializeSelect2();

  // Inicializar Select2 cada vez que el modal se muestra
  $("#miModal").on("shown.bs.modal", function () {
      console.log("Modal mostrado");
      initializeSelect2();
      // Forzar el foco en el primer campo de Select2
      $("#id_device").select2("open").select2("close");
  });

  // Función para obtener comandos basados en el ID del dispositivo
  function fetchCommands(deviceId) {
      fetch(`/es/realtime/commands/get-commands/${deviceId}/`)
          .then(response => response.json())
          .then(data => {
              var commandSelect = document.getElementById("id_command");
              commandSelect.innerHTML = "";
              data.commands.forEach(function(command) {
                  var option = document.createElement("option");
                  option.value = command.id;
                  option.textContent = command.name;
                  commandSelect.appendChild(option);
              });
              document.getElementById("command-error").style.display = "none";
              console.log("Comandos obtenidos:", data.commands);
          })
          .catch(error => console.error('Error fetching commands:', error));
  }

  // Función para confirmar y enviar el formulario
  function confirmSubmit(event) {
      event.preventDefault(); // Evita el envío por defecto
      var deviceId = document.getElementById("id_device").value;
      if (!deviceId) {
          alert(translations.selectDevice);
          return false; // No se envía el formulario si no se ha seleccionado ningún dispositivo
      }
      var isConfirmed = window.confirm(translations.confirmMessage);
      if (isConfirmed) {
          // Añadir el ID del dispositivo al formulario antes de enviarlo
          var form = document.getElementById("confirmForm");
          var hiddenInput = document.createElement("input");
          hiddenInput.type = "hidden";
          hiddenInput.name = "device_id";
          hiddenInput.value = deviceId;
          form.appendChild(hiddenInput);

          // Enviar el formulario usando HTMX
          htmx.trigger(form, 'submit');
      }
  }

  // Escuchar el evento de clic en el botón de guardar
  document.getElementById("saveButton").addEventListener('click', confirmSubmit);
});
