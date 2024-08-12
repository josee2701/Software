document.addEventListener('DOMContentLoaded', function () {
    var companySelect = $('#id_company');
    var vehicleSelect = $('#id_Imei');
    var eventSelect = $('#id_event');

    companySelect.select2();
    vehicleSelect.select2();
    eventSelect.select2();

    // Añade la clase form-control al contenedor de select2
    $('.select2-container').addClass('form-control');

    function moveErrorsToSelect2() {
        $('.select2-error-message').remove();
        $('.has-error').removeClass('has-error');

        var companyError = $('.error-message:has(#id_company)').text().trim();
        var vehicleError = $('.error-message:has(#id_Imei)').text().trim();
        var eventError = $('.error-message:has(#id_event)').text().trim();

        if (companyError) {
            showError(companySelect, companyError);
        }
        if (vehicleError) {
            showError(vehicleSelect, vehicleError);
        }
        if (eventError) {
            showError(eventSelect, eventError);
        }
    }

    function updateVehicleOptions() {
        var selectedCompany = companySelect.val();
        var previouslySelectedVehicle = vehicleSelect.val(); // Guarda el vehículo seleccionado

        if (selectedCompany) {
            fetch(`/es/checkpoints/reports/vehicles-by-company/${selectedCompany}/`)
                .then(response => response.json())
                .then(data => {
                    vehicleSelect.empty();

                    if (data.length > 0) {
                        data.forEach(function (vehicle) {
                            var isSelected = vehicle.imei === previouslySelectedVehicle; // Verifica si es el vehículo seleccionado
                            var option = new Option(vehicle.vehicle__license, vehicle.imei, isSelected, isSelected);
                            vehicleSelect.append(option);
                        });
                        vehicleSelect.trigger('change'); // Dispara el evento 'change' para actualizar la interfaz
                    }
                    vehicleSelect.prop('disabled', false);
                })
                .catch(error => {
                    console.error('Error al obtener los vehículos:', error);
                    vehicleSelect.prop('disabled', false);
                });
        } else {
            vehicleSelect.empty();
            vehicleSelect.prop('disabled', true);
        }
    }

    function updateEventsOptions() {
        var selectedCompany = companySelect.val();
        var previouslySelectedEvent = eventSelect.val();

        if (selectedCompany) {
            fetch(`/es/checkpoints/reports/events-by-company/${selectedCompany}/`)
                .then(response => response.json())
                .then(data => {
                    eventSelect.empty();
                    var allOption = new Option(translations.allEvents, '', true, true);
                    eventSelect.append(allOption);

                    data.forEach(function (event) {
                        var option = new Option(event, event, false, false);
                        eventSelect.append(option);
                    });

                    if (previouslySelectedEvent) {
                        eventSelect.val(previouslySelectedEvent).trigger('change');
                    }

                    eventSelect.prop('disabled', false);
                })
                .catch(error => {
                    console.error('Error fetching events:', error);
                    eventSelect.prop('disabled', false);
                });
        } else {
            eventSelect.empty();
            eventSelect.prop('disabled', true);
        }
    }

    companySelect.on('change', updateVehicleOptions);
    companySelect.on('change', updateEventsOptions);

    updateVehicleOptions();
    updateEventsOptions();

    function showError(selectElement, message) {
        var container = selectElement.data('select2').$container;
        container.addClass('has-error');
        var errorElement = $('<span class="select2-error-message"></span>').text(message);
        container.append(errorElement);
    }

    companySelect.on('change', function() {
        var container = $(this).data('select2').$container;
        container.removeClass('has-error');
        container.find('.select2-error-message').remove();
    });

    vehicleSelect.on('change', function() {
        var container = $(this).data('select2').$container;
        container.removeClass('has-error');
        container.find('.select2-error-message').remove();
    });

    eventSelect.on('change', function() {
        var container = $(this).data('select2').$container;
        container.removeClass('has-error');
        container.find('.select2-error-message').remove();
    });

    moveErrorsToSelect2();

    $('#search-form').on('submit', function(e) {
        if ($('#id_Imei').val() === "") {
            e.preventDefault();
            showError(vehicleSelect, 'Debe seleccionar un vehículo.');
        }
    });
});
