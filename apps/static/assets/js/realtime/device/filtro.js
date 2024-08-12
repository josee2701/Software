// Espera hasta que el DOM esté completamente cargado
$(document).ready(function() {
    // Referencias a los elementos select por sus IDs
    var manufactureSelect = $('#id_manufacture');
    var familySelect = $('#id_familymodel');
    var companySelect = $('#id_company');
    var simcardSelect = $('#id_simcard');
    var deviceIMEI = $('#id_imei').val(); // Obtiene el IMEI del dispositivo en modo edición

    var isManufactureLoaded = false; // Bandera para rastrear si la función ya se ha ejecutado

    // Inicializa Select2 en los selectores mencionados
    function initializeSelect2() {
        console.log("Inicializando Select2");
        manufactureSelect.select2({
            dropdownParent: $('#miModal')
        });
        familySelect.select2({
            dropdownParent: $('#miModal')
        });
        companySelect.select2({
            dropdownParent: $('#miModal')
        });
        simcardSelect.select2({
            dropdownParent: $('#miModal')
        });

        $('.select2-container').addClass('form-control');
        $('.select2-container').css('width', '');
        console.log("Select2 inicializado");
    }

    // Llama a la función para inicializar Select2
    initializeSelect2();

    // Evento cuando el modal se muestra
    $('#miModal').on('shown.bs.modal', function () {
        console.log("Modal mostrado");
        initializeSelect2(); // Re-inicializa Select2 para asegurar su funcionalidad dentro del modal
        manufactureSelect.select2('open'); // Abre el selector manufactureSelect
        manufactureSelect.select2('close'); // Cierra el selector manufactureSelect
        manufactureSelect.focus(); // Enfoca el selector manufactureSelect
    });

    // Actualiza los modelos de familia basados en el ID del fabricante
    function updateFamilyModels(manufactureId, selectedFamilyModelId = null) {
        if (!manufactureId) {
            familySelect.empty().prop('disabled', true);
            return;
        }

        var endpoint = `/es/realtime/devices/api/family_model/${manufactureId}/`;

        fetch(endpoint)
            .then(response => {
                if (!response.ok) throw new Error("Network response was not ok");
                return response.json();
            })
            .then(data => {
                familySelect.empty(); // Limpia el selector de familia
                data.forEach(function(family) {
                    familySelect.append(new Option(family.model_name, family.id)); // Añade opciones basadas en los datos recibidos
                });
                familySelect.prop('disabled', false); // Habilita el selector de familia
                if (selectedFamilyModelId) {
                    familySelect.val(selectedFamilyModelId).trigger('change'); // Selecciona el modelo de familia preseleccionado
                } else {
                    familySelect.trigger('change');
                }
            })
            .catch(error => {
                console.error("Error al obtener los modelos:", error);
            });
    }

    // Carga las tarjetas SIM disponibles basadas en el ID de la compañía
    function loadSimcards(companyId, imei) {
        if (!companyId) {
            simcardSelect.empty().prop('disabled', true);
            return;
        }

        var endpoint = `/es/realtime/devices/api/available-simcards/${companyId}/`;

        fetch(endpoint)
            .then(response => {
                if (!response.ok) throw new Error("Network response was not ok");
                return response.json();
            })
            .then(data => {
                simcardSelect.empty(); // Limpia el selector de SIM
                var foundCurrent = false;

                data.forEach(function(simcard) {
                    if (imei && !foundCurrent && $('#current_simcard_id').val() == simcard.id) {
                        simcardSelect.append(new Option(simcard.phone_number, simcard.id, false, true)); // Añade y selecciona la SIM actual
                        foundCurrent = true;
                    } else {
                        simcardSelect.append(new Option(simcard.phone_number, simcard.id)); // Añade la SIM sin seleccionar
                    }
                });

                simcardSelect.prop('disabled', false); // Habilita el selector de SIM

                if (!foundCurrent && data.length > 0 && !$('#id_simcard').val()) {
                    var firstOptionValue = simcardSelect.find('option:first').val();
                    simcardSelect.val(firstOptionValue).trigger('change'); // Selecciona la primera opción si no hay ninguna seleccionada
                }
            })
            .catch(error => {
                console.error("Error loading the simcards:", error);
            });
    }

    // Carga el fabricante basado en el ID del modelo de familia
    function loadManufactureForFamilyModel(familyModelId) {
        if (!familyModelId || isManufactureLoaded) {
            return; // Salir si no hay familyModelId o ya se ha ejecutado una vez
        }

        isManufactureLoaded = true; // Marcar como ejecutado

        var endpoint = `/es/realtime/devices/api/manufacture/${familyModelId}/`;

        fetch(endpoint)
            .then(response => {
                if (!response.ok) throw new Error("Network response was not ok");
                return response.json();
            })
            .then(data => {
                if (data.manufacture_id) {
                    manufactureSelect.val(data.manufacture_id).trigger('change'); // Selecciona el fabricante basado en los datos recibidos
                }
                manufactureSelect.prop('disabled', false); // Habilita el selector de fabricante
            })
            .catch(error => {
                console.error("Error al obtener el fabricante:", error);
            });
    }

    // Evento cuando se cambia el selector de familia
    familySelect.change(function() {
        var familyModelId = $(this).val();
        loadManufactureForFamilyModel(familyModelId);
    });

    // Evento cuando se cambia el selector de fabricante
    manufactureSelect.change(function() {
        var manufactureId = $(this).val();
        updateFamilyModels(manufactureId, familySelect.val());
    });

    // Evento cuando se cambia el selector de compañía
    companySelect.change(function() {
        var companyId = $(this).val();
        loadSimcards(companyId, deviceIMEI);
    });

    // Deshabilita los selectores de familia y SIM inicialmente
    familySelect.prop('disabled', true);
    simcardSelect.prop('disabled', true);

    // Carga inicial de datos si ya hay un modelo de familia seleccionado
    var initialFamilyModelId = familySelect.val();
    if (initialFamilyModelId) {
        loadManufactureForFamilyModel(initialFamilyModelId);
    }

    // Carga inicial de datos si ya hay un fabricante seleccionado
    var initialManufactureId = manufactureSelect.val();
    if (initialManufactureId) {
        updateFamilyModels(initialManufactureId, initialFamilyModelId);
    }

    // Carga inicial de SIM si hay una compañía seleccionada pero no hay IMEI
    if ($('#id_company').val() && !deviceIMEI) {
        var companyId = $('#id_company').val();
        loadSimcards(companyId, null);
    } else if ($('#id_company').val() && deviceIMEI) {
        simcardSelect.prop('disabled', false);
    }
});
