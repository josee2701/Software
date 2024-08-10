$(document).ready(function () {
    var deviceSelect = $('#id_device'); // Asume que este es el ID del select de dispositivos en tu formulario
    var companySelect = $('#id_company'); // Selector del select de compañía
    var vehicleId = $('#id_vehicle').val(); // Asume que tienes un campo oculto con el ID del vehículo al editar

    function loadDevices(companyId, vehicleId) {
        // Construye la URL dependiendo de si estás creando o editando un vehículo
        var endpoint = vehicleId ? `/es/realtime/vehicles/api/available-devices/${companyId}/${vehicleId}/` : `/es/realtime/vehicles/api/available-devices/${companyId}/`;
        deviceSelect.empty();

        // Primero, limpia el select y agrega una opción predeterminada
        deviceSelect.empty().append('<option value="">---------</option>');

        // Llama a la API para obtener los dispositivos
        fetch(endpoint)
            .then(response => response.json())
            .then(devices => {
                // Limpia el select y verifica si hay dispositivos disponibles
                deviceSelect.empty();
                if (devices.length > 0) {
                    // Agrega los dispositivos disponibles al select
                    devices.forEach(function (device) {
                        deviceSelect.append(new Option(device.imei, device.imei, false, device.imei === deviceSelect.data('current')));
                    });
                } else {
                    // Agrega una opción que indica que no hay dispositivos disponibles
                    deviceSelect.append('<option value="">---------</option>');
                }

                // Si estás editando, asegúrate de que el dispositivo actual esté seleccionado
                if (vehicleId) {
                    deviceSelect.val(deviceSelect.data('current'));
                }
            })
            .catch(error => {
                console.error('Error al cargar los dispositivos:', error);
                deviceSelect.empty().append('<option value="">Error al cargar</option>');
            });
    }

    // Evento de cambio para el select de compañía
    companySelect.change(function () {
        var companyId = $(this).val();
        loadDevices(companyId, vehicleId);
    });

    // Cargar dispositivos si estás en la página de edición o si se selecciona una compañía
    if (companySelect.val()) {
        loadDevices(companySelect.val(), vehicleId);
    }
});
