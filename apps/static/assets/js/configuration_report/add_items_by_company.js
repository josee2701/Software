document.addEventListener('DOMContentLoaded', function() {
    const companySelect = document.getElementById('companySelect');
    const editButton = document.getElementById('editButton');
    const widgetsContainer = document.getElementById('widgetsContainer');
    const reportsContainer = document.getElementById('reportsContainer');
    const alerts = document.querySelectorAll('.alert');

    companySelect.addEventListener('change', function() {
        const companyId = this.value;
        const languagePrefix = getLanguagePrefix();

        function getLanguagePrefix() {
            const path = window.location.pathname;
            const languageCode = path.split('/')[1];
            const supportedLanguages = ['en', 'es', 'es-co', 'es-mx', 'es-es'];
            const isLanguageSupported = supportedLanguages.includes(languageCode);
            return isLanguageSupported ? `/${languageCode}` : '';
          }

        if (companyId) {
            editButton.href = `${languagePrefix}/realtime/configuration-report/update/${companyId}`;
            editButton.removeAttribute('disabled');

            fetch(`${languagePrefix}/realtime/get-instance-data/?company_id=${companyId}`)
                .then(response => response.json())
                .then(data => {
                    const infoWidgets = Array.isArray(data.info_widgets) ? data.info_widgets : JSON.parse(data.info_widgets || '[]');
                    const infoReports = Array.isArray(data.info_reports) ? data.info_reports : JSON.parse(data.info_reports || '[]');

                    widgetsContainer.innerHTML = ''; // Siempre limpia el contenedor antes de agregar nuevos elementos
                    if (infoWidgets.length > 0) { // Solo añade widgets si la lista no está vacía
                        infoWidgets.forEach(widgetLabel => {
                            const widgetElement = document.createElement('div');
                            widgetElement.textContent = widgetLabel;
                            widgetsContainer.appendChild(widgetElement);
                        });
                    }

                    reportsContainer.innerHTML = ''; // Siempre limpia el contenedor antes de agregar nuevos elementos
                    if (infoReports.length > 0) { // Solo añade reportes si la lista no está vacía
                        infoReports.forEach(reportLabel => {
                            const reportElement = document.createElement('div');
                            reportElement.textContent = reportLabel;
                            reportsContainer.appendChild(reportElement);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        } else {
            editButton.setAttribute('disabled', 'disabled');
            editButton.href = '#';
            widgetsContainer.innerHTML = '';
            reportsContainer.innerHTML = '';
        }

        // Ocultar mensajes cuando se selecciona otra compañía
        alerts.forEach(alert => {
            alert.style.display = 'none';
        });
    });
    // Agregar evento al botón de editar
    editButton.addEventListener('click', function(event) {
        if (!companySelect.value) {
            event.preventDefault(); // Evitar que el enlace se siga si no se ha seleccionado una compañía
            alert(translations.confirmMessage); // Mostrar mensaje de aviso
        }
    });

    function filterCompanies(searchInputId, selectId) {
        var searchInput = document.getElementById(searchInputId);
        var select = document.getElementById(selectId);
        var selectOptions = select.getElementsByTagName('option');

        searchInput.addEventListener("keyup", function (event) {
            var query = event.target.value.toLowerCase();

            // Desplegar la lista de opciones al empezar a escribir en el campo de búsqueda
            select.size = 5;

            for (var i = 0; i < selectOptions.length; i++) {
                var option = selectOptions[i];
                var companyName = option.textContent.toLowerCase();

                if (companyName.indexOf(query) === -1) {
                    option.style.display = "none"; // Ocultar opciones no coincidentes
                } else {
                    option.style.display = ""; // Mostrar opciones coincidentes
                }
            }
        });

        // Reducir el tamaño de la lista cuando el campo de búsqueda pierda el foco
        searchInput.addEventListener("focusout", function () {
            // Esto asegura que la lista se cierre solo si no se está seleccionando una opción
            if (!select.matches(':hover')) {
                select.size = 1;
            }
        });

        // Limpiar el campo de búsqueda y cerrar la lista al seleccionar una opción
        select.addEventListener("change", function () {
            searchInput.value = ""; // Limpiar el campo de búsqueda
            select.size = 1; // Cerrar la lista desplegable
        });

    }
    // Llamar a la función para filtrar las opciones del campo de selección de compañías
    filterCompanies("search-company", "companySelect");
});
