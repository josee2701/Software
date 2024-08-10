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
    })
    .catch(error => console.error('Error fetching commands:', error));
}

document.getElementById("id_device").addEventListener("change", function() {
  var deviceId = this.value;
  if (deviceId) {
    fetchCommands(deviceId);
  }
});

function confirmSubmit(event) {
  event.preventDefault(); // Evita el envío por defecto
  var deviceId = document.getElementById("id_device").value;
  if (!deviceId) {
    alert(translations.selectDevice);
    return false; // No se envía el formulario si no se ha seleccionado ningún dispositivo
  }
  var isConfirmed = window.confirm(translations.confirmMessage);
  if (isConfirmed) {
    // Enviar el formulario usando HTMX
    htmx.trigger('#confirmForm', 'submit');
  }
}

document.getElementById("saveButton").addEventListener('click', confirmSubmit);

function filterDevices(searchInputId, selectId) {
  var searchInput = document.getElementById(searchInputId);
  var select = document.getElementById(selectId);
  var selectOptions = select.getElementsByTagName('option');

  searchInput.addEventListener("keyup", function () {
    var query = searchInput.value.toLowerCase();

    select.size = selectOptions.length > 5 ? 5 : selectOptions.length;
    for (var i = 0; i < selectOptions.length; i++) {
      var option = selectOptions[i];
      var plateNumber = option.textContent.toLowerCase();
      option.style.display = plateNumber.includes(query) ? "" : "none";
    }
  });

  searchInput.addEventListener("focusout", function () {
    if (!select.matches(':hover')) {
      select.size = 1;
    }
  });

  select.addEventListener("change", function () {
    searchInput.value = "";
    select.size = 1;
  });
}

filterDevices("search-device", "id_device");
