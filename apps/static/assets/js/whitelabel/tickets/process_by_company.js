// Función para manejar el evento de cambio en el select de compañías
function handleCompanyChange(event) {
    if (event) {
        event.stopPropagation(); // Detener la propagación del evento
        event.preventDefault(); // Prevenir el comportamiento predeterminado del formulario
    }

    const companyId = this.value;

    const formData = new FormData();
    formData.append('provider_company', companyId);

    fetch(fetchUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar dinámicamente la lista de procesos asignados
            const processSelect = document.getElementById('process-type');
            const assignToSelect = document.getElementById('assign-to');

            // Guardar el valor seleccionado previamente
            const previousSelectedValue = processSelect.value;

            processSelect.innerHTML = ''; // Limpiar el contenido actual
            if (event) {
                assignToSelect.innerHTML = '';
            }

            data.processes.forEach(process => {
                const option = document.createElement('option');
                option.value = process.id;
                option.textContent = process.process_type;
                processSelect.appendChild(option);
            });
            // Seleccionar el valor previamente seleccionado si existe en la nueva lista
            const newSelectedValue = data.processes.find(process => process.id == previousSelectedValue);
            if (newSelectedValue) {
                processSelect.value = previousSelectedValue;
            } else if (data.processes.length > 0) {
                // Si no existe el valor previamente seleccionado, seleccionar el primer proceso
                processSelect.value = data.processes[0].id;
            }
            const changeEvent = new Event('change');
            processSelect.dispatchEvent(changeEvent);
        } else {
            console.error('Failed to select company');
        }
    })
    .catch(error => {
        console.error(error);
    });

    return false; // Evitar el envío del formulario
}

// Función para manejar el evento de cambio en el select de procesos
function handleProcessChange(event) {
    event.stopPropagation(); // Detener la propagación del evento
    event.preventDefault(); // Prevenir el comportamiento predeterminado del formulario

    const processId = this.value;

    const formData = new FormData();
    formData.append('process_type', processId);

    fetch(fetchUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Guardar el valor seleccionado previamente
            const assignToSelect = document.getElementById('assign-to');
            const previousAssignToSelectedValue = assignToSelect.value;

            // Actualizar dinámicamente la lista de usuarios asignados
            assignToSelect.innerHTML = ''; // Limpiar el contenido actual

            data.users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = user.username;
                assignToSelect.appendChild(option);
            });

            // Seleccionar el valor previamente seleccionado si existe en la nueva lista de usuarios
            const newAssignToSelectedValue = data.users.find(user => user.id == previousAssignToSelectedValue);
            if (newAssignToSelectedValue) {
                assignToSelect.value = previousAssignToSelectedValue;
            } else {
                // Si no existe el valor previamente seleccionado, seleccionar la opción en blanco
                assignToSelect.value = '';
            }

            const changeEvent = new Event('change');
            assignToSelect.dispatchEvent(changeEvent);
        } else {
            throw new Error('Failed to select process');
        }
    })
    .catch(error => {
        console.error(error);
    });

    return false; // Evitar el envío del formulario
}

// Agregar el evento de cambio al select de compañías
document.getElementById('provider-company').addEventListener('change', handleCompanyChange);

// Validar y ejecutar la lógica si ya hay una compañía seleccionada
(function() {
    const companySelect = document.getElementById('provider-company');
    if (companySelect.value) {
        handleCompanyChange.call(companySelect);
    }
})();

// Agregar el evento de cambio al select de procesos
document.getElementById('process-type').addEventListener('change', handleProcessChange);
