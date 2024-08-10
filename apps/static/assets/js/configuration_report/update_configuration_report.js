// Función para mostrar un mensaje de confirmación antes de enviar el formulario
function confirmSave() {
    // Mostrar el mensaje de confirmación
    if (confirm(translations.confirmMessage)) {
        // Si el usuario confirma, enviar el formulario
        return true;
    } else {
        // Si el usuario cancela, no enviar el formulario
        return false;
    }
}

// Función para filtrar elementos de acuerdo al texto de búsqueda
function filterItems(containerId, searchInputId) {
    let container = document.getElementById(containerId);
    let searchInput = document.getElementById(searchInputId);
    let items = container.getElementsByClassName('draggable-item');
    let searchText = searchInput.value.trim().toLowerCase();

    for (let item of items) {
        let label = item.getElementsByTagName('label')[1].innerText.trim().toLowerCase(); // Asegúrate de seleccionar el label correcto
        if (searchText === '' || label.includes(searchText)) {
            item.style.display = "";
        } else {
            item.style.display = "none";
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Vincula los eventos de entrada para el filtrado
    document.getElementById('widgetSearch').addEventListener('input', function() {
        filterItems('widgetsContainer', 'widgetSearch');
    });

    document.getElementById('reportSearch').addEventListener('input', function() {
        filterItems('reportsContainer', 'reportSearch');
    });
    // Función para inicializar la capacidad de arrastrar y soltar
    function initializeDragAndDrop(container) {
        let draggables = container.querySelectorAll('.draggable-item');

        // Agregar el atributo draggable a cada elemento
        draggables.forEach(draggable => {
            draggable.draggable = true;
        });

        // Agregar eventos de arrastrar y soltar
        container.addEventListener('dragstart', (event) => {
            event.target.classList.add('dragging');
        });

        container.addEventListener('dragend', (event) => {
            event.target.classList.remove('dragging');
        });

        container.addEventListener('dragover', (event) => {
            event.preventDefault();
            const draggable = document.querySelector('.dragging');
            if (draggable && draggable.parentElement === container) {
                const afterElement = getDragAfterElement(container, event.clientY);
                if (afterElement == null) {
                    container.appendChild(draggable);
                } else {
                    container.insertBefore(draggable, afterElement);
                }
            }
        });
    }

    function getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.draggable-item:not(.dragging)')];

        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    // Inicializar la capacidad de arrastrar y soltar en los contenedores de widgets y reportes
    initializeDragAndDrop(document.getElementById('widgetsContainer'));
    initializeDragAndDrop(document.getElementById('reportsContainer'));

    // Funcionalidad para ordenar automáticamente los checkboxes al seleccionarlos o deseleccionarlos
    document.querySelectorAll('input[type="checkbox"]').forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                // Mover el checkbox marcado al final
                if (this.name === 'widgets') {
                    let checkedWidgets = Array.from(widgetsContainer.querySelectorAll('input[type="checkbox"]:checked'));
                    if (checkedWidgets.length > 1) {
                        widgetsContainer.insertBefore(this.parentElement, checkedWidgets[checkedWidgets.length - 2].parentElement.nextElementSibling);
                    } else {
                        widgetsContainer.prepend(this.parentElement);
                    }
                } else if (this.name === 'reports') {
                    let checkedReports = Array.from(reportsContainer.querySelectorAll('input[type="checkbox"]:checked'));
                    if (checkedReports.length > 1) {
                        reportsContainer.insertBefore(this.parentElement, checkedReports[checkedReports.length - 2].parentElement.nextElementSibling);
                    } else {
                        reportsContainer.prepend(this.parentElement);
                    }
                }
            } else {
                // Mover el checkbox no marcado al principio
                if (this.name === 'widgets') {
                    widgetsContainer.append(this.parentElement);
                } else if (this.name === 'reports') {
                    reportsContainer.append(this.parentElement);
                }
            }
        });
    });
});
