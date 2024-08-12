$(document).ready(function () {
    var deviceSelect = $('#id_device'); // Asume que este es el ID del select de dispositivos en tu formulario
    var companySelect = $('#id_company'); // Selector del select de compañía
    var vehicleId = $('#id_vehicle').val(); // Asume que tienes un campo oculto con el ID del vehículo al editar

    // Función para inicializar Select2
    function initializeSelect2() {
        console.log("Inicializando Select2");
        deviceSelect.select2({
            dropdownParent: $('#miModal')
        });
        companySelect.select2({
            dropdownParent: $('#miModal')
        });

        // Añadir la clase form-control al contenedor correcto
        $('.select2-container').addClass('form-control');

        // Eliminar el estilo de ancho en línea
        $('.select2-container').css('width', '');

        console.log("Select2 inicializado");
    }

    // Inicializar Select2 cuando el documento esté listo
    initializeSelect2();

    // Inicializar Select2 cada vez que el modal se muestra
    $('#miModal').on('shown.bs.modal', function () {
        console.log("Modal mostrado");
        initializeSelect2();
        companySelect.select2('open'); // Abrir el dropdown de Select2
        companySelect.select2('close'); // Cerrar el dropdown de Select2
        companySelect.focus(); // Forzar el foco en el campo Select2
    });

    // Deshabilitar deviceSelect por defecto
    deviceSelect.prop('disabled', true);

    // Función para cargar dispositivos según la compañía seleccionada
    function loadDevices(companyId, vehicleId) {
        // Construye la URL dependiendo de si estás creando o editando un vehículo
        var endpoint = vehicleId ? `/es/realtime/vehicles/api/available-devices/${companyId}/${vehicleId}/` : `/es/realtime/vehicles/api/available-devices/${companyId}/`;
        deviceSelect.empty();

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
                }

                // Si estás editando, asegúrate de que el dispositivo actual esté seleccionado
                if (vehicleId) {
                    var currentDevice = deviceSelect.data('current');
                    if (currentDevice) {
                        deviceSelect.val(currentDevice).trigger('change');
                    }
                }

                // Habilitar deviceSelect después de cargar los dispositivos
                deviceSelect.prop('disabled', false);
            })
            .catch(error => {
                console.error('Error al cargar los dispositivos:', error);
                deviceSelect.empty().append('<option value="">Error al cargar</option>');
                deviceSelect.prop('disabled', true); // Mantener deshabilitado en caso de error
            });
    }

    // Evento de cambio para el select de compañía
    companySelect.change(function () {
        var companyId = $(this).val();
        if (companyId) {
            loadDevices(companyId, vehicleId);
        } else {
            deviceSelect.empty();
            deviceSelect.prop('disabled', true); // Deshabilitar si no hay compañía seleccionada
        }
    });

    // Cargar dispositivos si estás en la página de edición o si se selecciona una compañía
    if (companySelect.val()) {
        loadDevices(companySelect.val(), vehicleId);
    }
});
