$(document).ready(function() {
    // Guarda el plan de datos seleccionado inicialmente
    var initialProcessId = $('#id_process_type').val();

    // Función para cargar los planes de datos
    function loadProcess(companyId, selectedProcessId = initialProcessId) {
        var url = `/es/users/process/${companyId}/`;

        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error("Network response was not ok");
                return response.json();
            })
            .then(data => {
                var processSelect = $('#id_process_type');
                processSelect.empty().append('<option value="">---------</option>');

                // Asegúrate de acceder a data.process si es el nombre de la clave en la respuesta JSON
                data.process.forEach(function(process) {
                    var optionElement = new Option(process.process_type, process.id);  // Corrige plan.id a process.id
                    processSelect.append(optionElement);
                });

                // Establece el plan de datos previamente seleccionado si está en las nuevas opciones
                if (selectedProcessId && $(`#id_process_type option[value=${selectedProcessId}]`).length > 0) {
                    processSelect.val(selectedProcessId);
                }
            })
            .catch(error => {
                console.error("Error loading the process:", error);
            });
    }

    // Evento 'change' para el select de compañía
    $('#id_company').change(function() {
        var companyId = $(this).val();
        loadProcess(companyId); // No pasamos el selectedDataPlanId aquí porque queremos reutilizar el valor inicial si es necesario
    });

    // Inicializa los planes de datos en el load si hay un valor de compañía
    if ($('#id_company').val()) {
        $('#id_company').trigger('change');
    } else {
        $('#id_process_type').empty().append('<option value="">---------</option>');
    }
  });
