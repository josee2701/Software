

document.addEventListener('DOMContentLoaded', function () {
    var startDateInput = document.getElementById('id_start_date');
    var endDateInput = document.getElementById('id_end_date');
    var errorMessage = document.getElementById('date_error');
    var reportButton = document.querySelector('.btn-primary');
    var companySelect = document.getElementById('id_company');
    var vehicleSelect = document.getElementById('id_Imei');
    var eventSelect = document.getElementById('id_event');
    var utcStartDateInput = document.getElementById('utc_start_date');
    var utcEndDateInput = document.getElementById('utc_end_date');
    var searchEventInput = document.getElementById('search-event');


    function filterEvents(searchInputId, selectId) {
        var searchInput = document.getElementById(searchInputId);
        var select = document.getElementById(selectId);
        var selectOptions = select.getElementsByTagName('option');

        searchInput.addEventListener("keyup", function () {
            var query = event.target.value.toLowerCase();

            // Desplegar la lista de opciones al empezar a escribir en el campo de búsqueda
            select.size = selectOptions.length > 5 ? 5 : selectOptions.length;

            for (var i = 0; i < selectOptions.length; i++) {
                var option = selectOptions[i];
                var eventName = option.textContent.toLowerCase();

                if (eventName.indexOf(query) === -1) {
                    option.style.display = "none"; // Ocultar opciones no coincidentes
                } else {
                    option.style.display = ""; // Mostrar opciones coincidentes
                }
            }
        });

        searchInput.addEventListener("focusout", function () {
            // Esto asegura que la lista se cierre solo si no se está seleccionando una opción
            if (!select.matches(':hover')) {
                select.size = 1;
            }
        });

        select.addEventListener("change", function () {
            searchInput.value = ""; // Limpiar el campo de búsqueda
            select.size = 1; // Cerrar la lista desplegable
        });
    }

    // Llamar a la función para filtrar las opciones del campo de selección de eventos
    filterEvents("search-event", "id_event");

    // Función para actualizar las opciones de vehicles basadas en la compañía seleccionada
    function updateVehicleOptions() {
        var selectedCompany = companySelect.value;
        var previouslySelectedImei = vehicleSelect.value;  // Guarda el IMEI actualmente seleccionado

        // Verifica si se seleccionó una compañía antes de realizar la solicitud AJAX
        if (selectedCompany && selectedCompany !== 'none') {
            // Realiza una solicitud AJAX para obtener las opciones de vehicles
            fetch(`/es/checkpoints/reports/vehicles-by-company/${selectedCompany}/`)
                .then(response => response.json())
                .then(data => {
                    // Elimina las opciones actuales
                    vehicleSelect.innerHTML = '';

                    // Agrega un elemento de opción con el texto "------------" al principio
                    var allOption = document.createElement('option');
                    allOption.value = '';
                    allOption.text = '------------';  // Texto genérico para representar ninguna selección
                    vehicleSelect.appendChild(allOption);

                    // Agrega las nuevas opciones
                    data.forEach(function (vehicle) {
                        var option = document.createElement('option');
                        option.value = vehicle.imei;
                        option.text = vehicle.vehicle__license;  // Ajusta esto según la propiedad de nombre de tu modelo Vehicle
                        vehicleSelect.appendChild(option);
                    });

                    // Vuelve a seleccionar el IMEI si aún está disponible en las opciones
                    if (vehicleSelect.querySelector(`option[value="${previouslySelectedImei}"]`)) {
                        vehicleSelect.value = previouslySelectedImei;
                    }

                    // Habilita el campo una vez se han cargado las opciones
                    vehicleSelect.disabled = false;
                })
                .catch(error => {
                    console.error('Error fetching vehicles:', error);
                    vehicleSelect.disabled = false;
                });
        } else {
            // Si no se selecciona una compañía, deja el campo de vehicle deshabilitado y sin opciones

        }
    }

    // Escucha cambios en la selección de la compañía
    companySelect.addEventListener('change', updateVehicleOptions);

    // Llama a la función una vez para configurar las opciones de vehicles inicialmente
    updateVehicleOptions();

    // Bloquea la opcion de busqueda de eventos si aun no se se ha seleccionado compañia
    searchEventInput.disabled = true

    // Función para actualizar las opciones de events basadas en la compañía seleccionada
    function updateEventsOptions() {
        var selectedCompany = companySelect.value;

        // Verifica si se seleccionó una compañía antes de realizar la solicitud AJAX
        if (selectedCompany && selectedCompany !== 'none') {
            // Realiza una solicitud AJAX para obtener las opciones de events
            fetch(`/es/checkpoints/reports/events-by-company/${selectedCompany}/`)
                .then(response => response.json())
                .then(data => {
                    // Elimina las opciones actuales
                    eventSelect.innerHTML = '';

                    // Agrega un elemento de opción con el texto "Todos" al principio
                    var allOption = document.createElement('option');
                    allOption.value = '';
                    allOption.text = '------------'; // Puedes cambiar 'Todos' por 'All' si prefieres
                    eventSelect.appendChild(allOption);

                    // Agrega las nuevas opciones
                    data.forEach(function (eventName) {
                        var option = document.createElement('option');
                        // Como no tienes un identificador único, puedes usar el nombre del evento como valor
                        option.value = eventName;
                        option.text = eventName;
                        eventSelect.appendChild(option);
                    });

                    // Habilita el campo una vez se han cargado las opciones
                    eventSelect.disabled = false;
                    searchEventInput.disabled = false
                })
                .catch(error => console.error('Error fetching events:', error));
        } else {
            // Si no se selecciona una compañía, deja el campo de events deshabilitado y sin opciones
            eventSelect.innerHTML = '';
            eventSelect.disabled = true;
        }
    }

    // Escucha cambios en la selección de la compañía
    companySelect.addEventListener('change', updateEventsOptions);

    // Llama a la función una vez para configurar las opciones de events inicialmente
    updateEventsOptions();

});
