document.addEventListener('DOMContentLoaded', function () {
    // Encuentra los elementos en el DOM por ID.
    const monitorCheckbox = document.getElementById('id_monitor');
    const companiesToMonitor = document.getElementById('companiesToMonitor');
    const vehiclesToMonitor = document.getElementById('vehiclesToMonitor');
    const groupVehicles = document.getElementById('groupVehicles');

    // Define la función que alterna la visibilidad de los elementos.
    function toggleVisibility() {
        console.log('toggleVisibility fue llamada'); // Mensaje para depuración.
        if (monitorCheckbox && monitorCheckbox.checked) {
            // Si el checkbox está marcado, muestra los campos.
            if (companiesToMonitor) companiesToMonitor.style.display = 'block';
            if (vehiclesToMonitor) vehiclesToMonitor.style.display = 'block';
            if (groupVehicles) groupVehicles.style.display = 'block';
        } else {
            // Si el checkbox no está marcado, oculta los campos.
            if (companiesToMonitor) companiesToMonitor.style.display = 'none';
            if (vehiclesToMonitor) vehiclesToMonitor.style.display = 'none';
            if (groupVehicles) groupVehicles.style.display = 'none';
        }
    }

    // Comprueba si los elementos están presentes en el DOM.
    if (!monitorCheckbox) {
        console.error('Elemento monitorCheckbox no encontrado en el DOM.');
    }
    if (!companiesToMonitor) {
        console.error('Elemento companiesToMonitor no encontrado en el DOM.');
    }
    if (!vehiclesToMonitor) {
        console.error('Elemento vehiclesToMonitor no encontrado en el DOM.');
    }
    if (!groupVehicles) {
        console.error('Elemento groupVehicles no encontrado en el DOM.');
    }

    // Añade el evento 'change' al checkbox de monitoreo si este existe.
    if (monitorCheckbox) {
        monitorCheckbox.addEventListener('change', toggleVisibility);
    }

    // Establece la visibilidad inicial después de una pequeña espera.
    setTimeout(toggleVisibility, 100);
});
