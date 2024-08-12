$(document).ready(function() {
    var processSelect = $('#id_process_type');
    var prioritySelect = $('#id_priority');
    var distributorRadio = $('#id_distributor');
    var internsRadio = $('#id_interns');

    // Función para inicializar Select2
    function initializeSelect2() {
        console.log("Inicializando Select2");
        processSelect.select2({
            dropdownParent: $('#miModal')
        });
        prioritySelect.select2({
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
        processSelect.select2('open'); // Abrir el dropdown de Select2
    });

    // Función para mover errores a Select2
    function moveErrorsToSelect2() {
        $('.select2-error-message').remove();
        $('.has-error').removeClass('has-error');

        var processError = $('.error-message:has(#id_process_type)').text().trim();
        if (processError) {
            showError(processSelect, processError);
        }
    }

    // Función para mostrar errores en Select2
    function showError(selectElement, message) {
        var container = selectElement.data('select2').$container;
        container.addClass('has-error');
        var errorElement = $('<span class="select2-error-message"></span>').text(message);
        container.append(errorElement);
    }

    // Función para cargar los procesos
    function loadProcess() {
        var selectedProcessId = $('input[name="process_type"]:checked').val();
        var url = `/es/whitelabel/process/${selectedProcessId}`;

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


            })
            .catch(error => {
                console.error("Error loading the process:", error);
            });
    }

    // Evento 'change' para los radios
    $('input[name="process_type"]').on('change', function() {
        loadProcess();
    });

    // Inicializa los procesos al cargar la página
    loadProcess();

    // Remover errores cuando los elementos cambian
    processSelect.on('change', function() {
        var container = $(this).data('select2').$container;
        container.removeClass('has-error');
        container.find('.select2-error-message').remove();
    });

    // Mover errores a Select2 al inicio
    moveErrorsToSelect2();
});
