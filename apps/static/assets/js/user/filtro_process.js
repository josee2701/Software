$(document).ready(function() {
    var companySelect = $('#id_company');
    var processSelect = $('#id_process_type');
    var alarm =$('#id_alarm');
    var userID = $('#id_user').val();

    // Función para inicializar Select2
    function initializeSelect2() {
        console.log("Inicializando Select2");
        companySelect.select2({
            dropdownParent: $('#miModal')
        });
        processSelect.select2({
            dropdownParent: $('#miModal')
        });
        alarm.select2({
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
    });

    // Forzar el foco en el campo de Select2 al abrir el modal
    $('#miModal').on('shown.bs.modal', function () {
        console.log("Enfocando en el campo Select2");
        companySelect.focus();
    });

    // Función para mover errores a Select2
    function moveErrorsToSelect2() {
        $('.select2-error-message').remove();
        $('.has-error').removeClass('has-error');

        var companyError = $('.error-message:has(#id_company)').text().trim();
        var processError = $('.error-message:has(#id_process_type)').text().trim();

        if (companyError) {
            showError(companySelect, companyError);
        }
        if (processError) {
            showError(processSelect, processError);
        }
    }

    // Función para cargar los procesos
    function loadProcess(companyId, selectedProcessId = processSelect.val()) {
        var url = `/es/users/process/${companyId}/${userID}/`;

        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error("Network response was not ok");
                return response.json();
            })
            .then(data => {
                processSelect.empty();
                data.process.forEach(function(process) {
                    var optionElement = new Option(process.process_type, process.id);
                    processSelect.append(optionElement);
                });

                if (selectedProcessId && $(`#id_process_type option[value=${selectedProcessId}]`).length > 0) {
                    processSelect.val(selectedProcessId).trigger('change');
                }
            })
            .catch(error => {
                console.error("Error loading the process:", error);
            });
    }

    // Evento 'change' para el select de compañía
    companySelect.on('change', function() {
        var companyId = $(this).val();
        loadProcess(companyId);
    });

    // Inicializa los planes de datos en el load si hay un valor de compañía
    if (companySelect.val()) {
        companySelect.trigger('change');
    } else {
    processSelect.empty();
    }

    // Función para mostrar errores en Select2
    function showError(selectElement, message) {
        var container = selectElement.data('select2').$container;
        container.addClass('has-error');
        var errorElement = $('<span class="select2-error-message"></span>').text(message);
        container.append(errorElement);
    }

    // Remover errores cuando los elementos cambian
    companySelect.on('change', function() {
        var container = $(this).data('select2').$container;
        container.removeClass('has-error');
        container.find('.select2-error-message').remove();
    });

    processSelect.on('change', function() {
        var container = $(this).data('select2').$container;
        container.removeClass('has-error');
        container.find('.select2-error-message').remove();
    });

    // Mover errores a Select2 al inicio
    moveErrorsToSelect2();
});
