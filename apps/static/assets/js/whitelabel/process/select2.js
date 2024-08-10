$(document).ready(function () {

    function initializeSelect2() {
        console.log("Inicializando Select2");
        $('#id_company').select2({
            dropdownParent: $('#miModal')
        });
        // Añadir la clase form-control al contenedor correcto
        $('.select2-container').addClass('form-control');
        // Eliminar el estilo de ancho en línea
        $('.select2-container').css('width', '');
    }
    // Inicializar Select2 cuando el documento esté listo
    initializeSelect2();
    // Inicializar Select2 cada vez que el modal se muestra
    $('#miModal').on('shown.bs.modal', function () {
        initializeSelect2();
        $('#id_company').select2('open'); // Abrir el dropdown de Select2
    });
    // Forzar el foco en el campo de Select2 al abrir el modal
    $('#miModal').on('shown.bs.modal', function () {
        $('#id_company').focus();
    });
});
