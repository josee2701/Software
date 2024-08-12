$(document).ready(function() {
    var companySelect = $('#id_company');
    var dataPlanSelect = $('#id_data_plan');
    var initialDataPlanId = dataPlanSelect.val();

    // Función para inicializar Select2
    function initializeSelect2() {
        console.log("Inicializando Select2");
        companySelect.select2({
            dropdownParent: $('#miModal')
        });
        dataPlanSelect.select2({
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

    // Función para mover errores a Select2
    function moveErrorsToSelect2() {
        $('.select2-error-message').remove();
        $('.has-error').removeClass('has-error');

        var companyError = $('.error-message:has(#id_company)').text().trim();
        var dataPlanError = $('.error-message:has(#id_data_plan)').text().trim();

        if (companyError) {
            showError(companySelect, companyError);
        }
        if (dataPlanError) {
            showError(dataPlanSelect, dataPlanError);
        }
    }

    // Función para mostrar errores en Select2
    function showError(selectElement, message) {
        var container = selectElement.data('select2').$container;
        container.addClass('has-error');
        var errorElement = $('<span class="select2-error-message"></span>').text(message);
        container.append(errorElement);
    }

    // Función para cargar los planes de datos
    function loadDataPlans(companyId, selectedDataPlanId = initialDataPlanId) {
        var url = `/es/realtime/simcards/api/data-plans/${companyId}/`;

        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error("Network response was not ok");
                return response.json();
            })
            .then(data => {
                dataPlanSelect.empty();

                // Agrega los nuevos planes de datos al select
                data.forEach(function(plan) {
                    var optionText = `${plan.name} - ${plan.operator_name}`;
                    var optionElement = new Option(optionText, plan.id);
                    dataPlanSelect.append(optionElement);
                });

                // Establece el plan de datos previamente seleccionado si está en las nuevas opciones
                if (selectedDataPlanId && $(`#id_data_plan option[value=${selectedDataPlanId}]`).length > 0) {
                    dataPlanSelect.val(selectedDataPlanId).trigger('change');
                }
            })
            .catch(error => {
                console.error("Error loading the data plans:", error);
            });
    }

    // Evento 'change' para el select de compañía
    companySelect.change(function() {
        var companyId = $(this).val();
        console.log("Compañía seleccionada:", companyId);
        loadDataPlans(companyId); // No pasamos el selectedDataPlanId aquí porque queremos reutilizar el valor inicial si es necesario
    });

    // Inicializa los planes de datos en el load si hay un valor de compañía
    if (companySelect.val()) {
        console.log("Inicializando planes de datos para la compañía seleccionada:", companySelect.val());
        companySelect.trigger('change');
    }

    // Remover errores cuando los elementos cambian
    companySelect.on('change', function() {
        var container = $(this).data('select2').$container;
        container.removeClass('has-error');
        container.find('.select2-error-message').remove();
    });

    dataPlanSelect.on('change', function() {
        var container = $(this).data('select2').$container;
        container.removeClass('has-error');
        container.find('.select2-error-message').remove();
    });

    // Mover errores a Select2 al inicio
    moveErrorsToSelect2();
});
