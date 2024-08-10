$(document).ready(function() {
    var simcardSelect = $('#id_simcard');
    var deviceIMEI = $('#id_imei').val(); // IMEI del dispositivo en modo edición

    function loadSimcards(companyId, imei) {
        // Verificar si se ha seleccionado una compañía
        if (!companyId) {
            // Si no se ha seleccionado una compañía, vaciar el select de SIM cards y salir de la función
            simcardSelect.empty();
            return;
        }

        var endpoint = imei ? `/es/realtime/devices/api/available-simcards/${companyId}/${imei}/` : `/es/realtime/devices/api/available-simcards/${companyId}/`;

        fetch(endpoint)
            .then(response => {
                if (!response.ok) throw new Error("Network response was not ok");
                return response.json();
            })
            .then(data => {
                simcardSelect.empty();
                var foundCurrent = false;

                // Primero agregar la SIM card actualmente asignada como primera opción
                data.forEach(function(simcard) {
                    if (imei && !foundCurrent && $('#current_simcard_id').val() == simcard.id) {
                        simcardSelect.append(new Option(simcard.phone_number, simcard.id, false, true)); // Añadir y seleccionar
                        foundCurrent = true;
                    } else {
                        simcardSelect.append(new Option(simcard.phone_number, simcard.id));
                    }
                });

                if (!foundCurrent && imei) {
                    // Si la SIM actual no está en la lista, obtener sus detalles y agregarla
                    fetch(`/path/to/simcard/details/${$('#current_simcard_id').val()}`) // Asume que tienes una ruta para obtener detalles
                        .then(response => response.json())
                        .then(simcard => {
                            simcardSelect.prepend(new Option(simcard.phone_number, simcard.id, false, true)); // Añadir al principio y seleccionar
                        });
                }
            })
            .catch(error => {
                console.error("Error loading the simcards:", error);
            });
    }

    $('#id_company').change(function() {
        var companyId = $(this).val();
        loadSimcards(companyId, deviceIMEI);
    });

    // Cargar al inicio si estás en modo de edición y se ha seleccionado una compañía
    if ($('#id_company').val() && deviceIMEI) {
        $('#id_company').change();
    } else {
        // Si no se ha seleccionado una compañía al inicio, vaciar el select de SIM cards
        simcardSelect.empty();
    }
});
