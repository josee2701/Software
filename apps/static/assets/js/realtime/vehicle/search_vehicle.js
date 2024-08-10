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
    const url = `${languagePrefix}/realtime/vehicles/vehicles-user${queryParam}`;

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const rows = document.querySelector("#vehicle-tbody");
            rows.innerHTML = ''; // Limpiar el contenido actual

            data.results.forEach(vehicle => {
                const row = document.createElement("tr");
                const updateUrl = updateVehicleUrl.replace('0', `${vehicle.id}`);
                const deleteUrl = deleteVehicleUrl.replace('0', `${vehicle.id}`);
                let statusText = '';
                if (vehicle.is_active === false) {
                    statusText = translations.false;
                } else if (vehicle.is_active === true ) {
                    statusText = translations.true;
                }

                let buttonsHtml = '';
                if (permiseChange === "True") { // Verifica el permiso de edición
                    buttonsHtml += `<button type="button" hx-get="${updateUrl}" class="btn btn-primary btn-sm" hx-target="#modal .modal-content" style="margin-right: 3px;"><i class="fa-solid fa-pencil"></i></button>`;
                }
                if (permiseDelete === "True") { // Verifica el permiso de eliminación
                    buttonsHtml += `<button type="button" hx-get="${deleteUrl}" class="btn btn-danger btn-sm ml-2" hx-target="#modal .modal-content"><i class="fa-solid fa-trash"></i></button>`;
                }

                row.innerHTML = `
                    <td class="text-center p-2">${buttonsHtml}</td>
                    <td class="align-middle text-center text-sm">
                        <img style="inline-size: 33px; block-size: 33px;" class="myImage" src="${vehicle.icon}" alt="icon">
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${vehicle.company}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${vehicle.license}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${vehicle.n_interno}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${vehicle.device}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${vehicle.vehicle_type}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-secondary text font-weight-normal mb-0">${vehicle.installation_date}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-secondary mb-0">${statusText}</span>
                    </td>
                `;

                console.log("Appending row:", row);
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
