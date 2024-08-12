document.addEventListener('DOMContentLoaded', function() {
    var opacityRange = document.getElementById('id_opacity_range');
    var opacityInput = document.getElementById('id_opacity');
    var previewBox = document.getElementById('color_picker_sidebar');
    var sidebarColorInput = document.querySelector('[name="sidebar_color"]');

    // Convertir hexadecimal a decimal
    function hexToDecimal(hex) {
        return parseInt(hex, 16);
    }

    // Convertir color hexadecimal a rgba
    function hexToRgbA(hex, alpha) {
        var r, g, b;
        if (/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)) {
            hex = hex.substring(1);
            if (hex.length === 3) {
                hex = hex.split('').map(function (hex) { return hex + hex; }).join('');
            }
            r = parseInt(hex.substring(0, 2), 16);
            g = parseInt(hex.substring(2, 4), 16);
            b = parseInt(hex.substring(4, 6), 16);
            return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
        }
        throw new Error('Formato de color hexadecimal inválido.');
    }

    // Actualiza el valor de opacidad y vista previa
    function updateOpacity() {
        var opacityValue = opacityRange.value;
        opacityInput.value = parseInt(opacityValue).toString(16).padStart(2, '0'); // Actualizar el valor de opacidad en hexadecimal en el input oculto
        updatePreview();
    }

    // Actualiza la vista previa con el color de la barra lateral y la opacidad
    function updatePreview() {
        var opacityValue = parseInt(opacityInput.value, 16) / 255; // Convertir a decimal para rgba
        var sidebarColor = sidebarColorInput.value;
        var rgbaColor = hexToRgbA(sidebarColor, opacityValue);
        previewBox.style.backgroundColor = rgbaColor;
    }

    // Inicializar con el valor actual
    var initialOpacityHex = opacityInput.value;
    var initialOpacityDecimal = hexToDecimal(initialOpacityHex);
    opacityRange.value = initialOpacityDecimal;
    updatePreview();

    opacityRange.addEventListener('input', updateOpacity);
});
