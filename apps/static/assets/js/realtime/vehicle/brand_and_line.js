$(document).ready(function() {
    var brandSelect = $('#id_brand');
    var lineSelect = $('#id_line');
    var vehicleTypeSelect = $('#id_vehicle_type');
    var assetTypeCheckbox = $('#id_asset_type');
    var fuelType = $('#id_fuel_type');

    var initialBrandOptions = brandSelect.html();
    var initialLineOptions = lineSelect.html();
    var initialVehicleTypeOptions = vehicleTypeSelect.html();
    var initialBrandValue = brandSelect.data('initial');
    var initialLineValue = lineSelect.data('initial');
    var initialVehicleTypeValue = vehicleTypeSelect.data('initial');
    var wasAssetTypeCheckedInitially = assetTypeCheckbox.prop('checked');

    // Función para inicializar Select2
    function initializeSelect2() {
        console.log("Inicializando Select2");
        brandSelect.select2({
            dropdownParent: $('#miModal')
        });
        lineSelect.select2({
            dropdownParent: $('#miModal')
        });
        vehicleTypeSelect.select2({
            dropdownParent: $('#miModal')
        });
        fuelType.select2({
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
    });

    // Función para manejar el cambio del tipo de vehículo
    function handleVehicleTypeChange() {
        var vehicleTypeId = vehicleTypeSelect.val();
        if (!vehicleTypeId) {
            brandSelect.empty();
            lineSelect.empty();
            return;
        }

        $.ajax({
            url: "/es/realtime/vehicles/get_brands/",
            data: { 'vehicle_type_id': vehicleTypeId },
            dataType: 'json',
            success: function(data) {
                var brands = data.brands;
                brandSelect.empty();
                lineSelect.empty();
                $.each(brands, function(index, brand) {
                    brandSelect.append($('<option>', {
                        value: brand.brand_id,
                        text: brand.brand
                    }));
                });

                // Establecer el valor inicial o seleccionar el primer brand por defecto
                if (initialBrandValue) {
                    brandSelect.val(initialBrandValue).change();
                } else if (brands.length > 0) {
                    brandSelect.val(brands[0].brand_id).change();
                }
            },
            error: function() {
                alert('Error al obtener las marcas');
            }
        });
    }

    // Función para manejar el cambio de marca
    function handleBrandChange() {
        var brandId = brandSelect.val();
        if (!brandId) {
            lineSelect.empty();
            return;
        }

        $.ajax({
            url: "/es/realtime/vehicles/get_lines/",
            data: { 'brand_id': brandId },
            dataType: 'json',
            success: function(data) {
                var lines = data.lines;
                lineSelect.empty();
                $.each(lines, function(index, line) {
                    lineSelect.append($('<option>', {
                        value: line.line_id,
                        text: line.line
                    }));
                });

                // Establecer el valor inicial si existe
                if (initialLineValue) {
                    lineSelect.val(initialLineValue);
                }
            },
            error: function() {
                alert('Error al obtener las líneas');
            }
        });
    }

    // Función para manejar el cambio del checkbox de asset_type
    function handleAssetTypeChange() {
        if (!assetTypeCheckbox.prop('checked')) {
            if (!wasAssetTypeCheckedInitially) {
                // Vaciar los campos de selección y destruir Select2
                brandSelect.select2('destroy').empty();
                lineSelect.select2('destroy').empty();
                vehicleTypeSelect.select2('destroy').empty();

                // Cambiar los selectores a campos de texto
                brandSelect.replaceWith('<input type="text" id="id_brand" name="brand" class="form-control form-control-lg" value="' + (initialBrandValue || '') + '">');
                lineSelect.replaceWith('<input type="text" id="id_line" name="line" class="form-control form-control-lg" value="' + (initialLineValue || '') + '">');
                vehicleTypeSelect.replaceWith('<input type="text" id="id_vehicle_type" name="vehicle_type" class="form-control form-control-lg" value="' + (initialVehicleTypeValue || '') + '">');
            } else {
                // Vaciar los campos de selección y destruir Select2
                brandSelect.select2('destroy').empty();
                lineSelect.select2('destroy').empty();
                vehicleTypeSelect.select2('destroy').empty();

                brandSelect.replaceWith('<input type="text" id="id_brand" name="brand" class="form-control form-control-lg">');
                lineSelect.replaceWith('<input type="text" id="id_line" name="line" class="form-control form-control-lg">');
                vehicleTypeSelect.replaceWith('<input type="text" id="id_vehicle_type" name="vehicle_type" class="form-control form-control-lg">');
            }

            // Actualizar las variables de los selectores a los nuevos inputs de texto
            brandSelect = $('#id_brand');
            lineSelect = $('#id_line');
            vehicleTypeSelect = $('#id_vehicle_type');
        } else {
            // Volver a agregar los selectores y recargar las opciones de vehicle_type
            $('#id_brand').replaceWith('<select id="id_brand" name="brand" class="form-control form-control-lg">' + initialBrandOptions + '</select>');
            $('#id_line').replaceWith('<select id="id_line" name="line" class="form-control form-control-lg">' + initialLineOptions + '</select>');
            $('#id_vehicle_type').replaceWith('<select id="id_vehicle_type" name="vehicle_type" class="form-control form-control-lg">' + initialVehicleTypeOptions + '</select>');

            // Reasignar las variables de los selectores después de reemplazarlos
            brandSelect = $('#id_brand');
            lineSelect = $('#id_line');
            vehicleTypeSelect = $('#id_vehicle_type');

            // Volver a inicializar Select2
            initializeSelect2();

            // Volver a asociar los eventos change a los nuevos selectores
            vehicleTypeSelect.change(handleVehicleTypeChange);
            brandSelect.change(handleBrandChange);

            // Establecer los valores iniciales si existen
            if (initialVehicleTypeValue) {
                vehicleTypeSelect.val(initialVehicleTypeValue).trigger('change');
            } else {
                handleVehicleTypeChange();
            }
        }
    }

    // Inicializar el formulario
    function initializeForm() {
        if (initialVehicleTypeValue) {
            vehicleTypeSelect.val(initialVehicleTypeValue);
            handleVehicleTypeChange();
        } else {
            // Si no hay un valor inicial, seleccionar el primer elemento automáticamente
            var firstOptionValue = vehicleTypeSelect.find('option:first').val();
            vehicleTypeSelect.val(firstOptionValue).trigger('change');
        }
    }

    // Función para inicializar el estado correcto al cargar la página
    function init() {
        if (!assetTypeCheckbox.prop('checked')) {
            handleAssetTypeChange();
        } else {
            initializeForm();
        }
    }

    // Asociar eventos inicialmente
    vehicleTypeSelect.change(handleVehicleTypeChange);
    brandSelect.change(handleBrandChange);
    assetTypeCheckbox.change(handleAssetTypeChange);

    // Inicializar el formulario
    init();
});
