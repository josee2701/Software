function getLanguagePrefix() {
    const path = window.location.pathname;
    const languageCode = path.split('/')[1];
    const supportedLanguages = ['en', 'es', 'es-co', 'es-mx', 'es-es'];
    const isLanguageSupported = supportedLanguages.includes(languageCode);
    return isLanguageSupported ? `/${languageCode}` : '';
}

// JavaScript para manejar la búsqueda
const input = document.getElementById("search-input");

input.addEventListener("keyup", (e) => {
    const value = e.target.value.toLowerCase();
    const languagePrefix = getLanguagePrefix();
    const queryParam = value ? `?query=${value}` : '';
    const url = `${languagePrefix}/realtime/geozones/geofence-user${queryParam}`;

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const rows = document.querySelector("#geofence-tbody");
            rows.innerHTML = ''; // Limpiar el contenido actual

            data.results.forEach(geofence => {
                const row = document.createElement("tr");
                // const updateUrl = updateGeofenceUrl.replace('0', `${geofence.id}`);
                // const deleteUrl = deleteGeofenceUrl.replace('0', `${geofence.id}`);
                let geofenceType = '';
                if (geofence.type_event === 'Exit') {
                    geofenceType = translations.exit;
                } else if (geofence.type_event === 'Entry' ) {
                    geofenceType = translations.entry;
                } else if (geofence.type_event === 'Entry and Exit' ) {
                    geofenceType = translations.entryAndExit;
                }
                let shapeType = '';
                if (geofence.shape_type === '') {
                    shapeType = translations.marker;
                } else if (geofence.shape_type === 1 ) {
                    shapeType = translations.circle;
                } else if (geofence.shape_type === 2 ) {
                    shapeType = translations.polygon;
                }

                // let buttonsHtml = '';
                // if (permiseChange === "True") { // Verifica el permiso de edición
                //     buttonsHtml += `<button type="button" hx-get="${updateUrl}" class="btn btn-primary" hx-target="#modal .modal-content" style="margin-right: 3px;"><i class="fa-solid fa-pencil"></i></button>`;
                // }
                // if (permiseDelete === "True") { // Verifica el permiso de eliminación
                //     buttonsHtml += `<button type="button" hx-get="${deleteUrl}" class="btn btn-danger" hx-target="#modal .modal-content" style="margin-right: 3px;"><i class="fa-solid fa-trash"></i></button>`;
                // }

                row.innerHTML = `

                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${geofence.company}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${geofence.name}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-secondary mb-0">${geofenceType}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-secondary mb-0">${shapeType}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${geofence.latitude}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${geofence.longitude}</span>
                    </td>

                `;

                rows.appendChild(row);
            });

            // Actualizar paginación
            const paginationContainer = document.querySelector("#pagination-container");
            paginationContainer.innerHTML = ''; // Limpiar el contenido actual

            const ulPagination = document.createElement("ul");
            ulPagination.classList.add("pagination");

            if (data.page.has_previous) {
                ulPagination.innerHTML += `
                    <li class="page-item">
                        <a class="page-link" href="#" onclick="setPageAndSubmit(1); return false;">${translations.home}</a>
                    </li>
                    <li class="page-item">
                        <a class="page-link" href="#" onclick="setPageAndSubmit(${data.page.number - 1}); return false;">&laquo;</a>
                    </li>
                `;
            }

            if (data.page.number > 4) {
                ulPagination.innerHTML += `
                    <li class="page-item"><span class="page-link">...</span></li>
                `;
            }

            for (let i = 1; i <= data.page.num_pages; i++) {
                if (i > data.page.number - 4 && i < data.page.number + 4) {
                    ulPagination.innerHTML += `
                        <li class="page-item ${i === data.page.number ? 'active' : ''}">
                            <a class="page-link" href="#" onclick="setPageAndSubmit(${i}); return false;">${i}</a>
                        </li>
                    `;
                }
            }

            if (data.page.number < data.page.num_pages - 3) {
                ulPagination.innerHTML += `
                    <li class="page-item"><span class="page-link">...</span></li>
                `;
            }

            if (data.page.has_next) {
                ulPagination.innerHTML += `
                    <li class="page-item">
                        <a class="page-link" href="#" onclick="setPageAndSubmit(${data.page.number + 1}); return false;">&raquo;</a>
                    </li>
                    <li class="page-item">
                        <a class="page-link" href="#" onclick="setPageAndSubmit(${data.page.num_pages}); return false;">${translations.end}</a>
                    </li>
                `;
            }

            paginationContainer.appendChild(ulPagination);

            // Actualizar información de la paginación
            const paginationInfo = document.querySelector(".pagination-info");
            paginationInfo.textContent = `${translations.displaying} ${data.page.start_index} ${translations.to} ${data.page.end_index} ${translations.of} ${data.page.total_items} items.`;

            // Asegúrate de inicializar HTMX nuevamente en los nuevos elementos
            htmx.process(rows);
        })
        .catch(error => console.error('Error:', error));
});
