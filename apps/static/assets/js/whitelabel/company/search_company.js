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
    const url = `${languagePrefix}/whitelabel/company/company-user${queryParam}`;

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const rows = document.querySelector("#company-tbody");
            rows.innerHTML = ''; // Limpiar el contenido actual

            data.results.forEach(company => {
                const row = document.createElement("tr");
                row.setAttribute("id", company.id);
                const updateUrl = updateDistributorUrl.replace('0', `${company.id}`);
                const updateCustomerurl = updateCustomerUrl.replace('0', `${company.id}`);
                const deleteUrl = deleteCompanyUrl.replace('0', `${company.id}`);
                const mapUrl = updateMapsUrl.replace('0', `${company.id}`);

                let buttonsHtml = '';
                if (permiseChange === "True") { // Verifica el permiso de edición
                    if (company.provider_id === null) {
                        buttonsHtml += `<button type="button" class="btn btn-primary btn-sm" hx-get="${updateUrl}" hx-target="#modal .modal-content" style="margin-right: 3px;"><i class="fa-solid fa-pencil"></i></button>`;
                    } else {
                        buttonsHtml += `<button type="button" class="btn btn-primary btn-sm" hx-get="${updateCustomerurl}" hx-target="#modal .modal-content" style="margin-right: 3px;"><i class="fa-solid fa-pencil"></i></button>`;
                    }
                }
                if (permiseDelete === "True" && company.id !== 1) { // Verifica el permiso de eliminación
                    buttonsHtml += `<button type="button" class="btn btn-danger btn-sm ml-2" hx-get="${deleteUrl}" hx-target="#modal .modal-content" style="margin-right: 3px;"><i class="fa-solid fa-trash"></i></button>`;
                }
                if (permiseDelete === "True" && company.id === 1) { // Verifica el permiso de eliminación
                    buttonsHtml += `<button type="button" class="btn btn-danger btn-sm ml-2" hx-get="${deleteUrl}" hx-target="#modal .modal-content" style="visibility: hidden; width: 39px; height: 30px; display: inline-block;"></button>`;
                }
                if (permiseChange === "True" && company.show_map_button) {
                    buttonsHtml += `<button type="button" class="btn btn-primary btn-sm" hx-get="${mapUrl}" hx-target="#modal .modal-content"><i class="fa-solid fa-map"></i></button>`;
                }
                else {
                    buttonsHtml += `<button type="button" class="btn btn-primary btn-sm" style="visibility: hidden; width: 39px; height: 30px; display: inline-block;" hx-get="${mapUrl}" hx-target="#modal .modal-content"></i></button>`;
                }

                let typeText = '';
                if (!company.provider_id) {
                    typeText = translations.distributor;
                } else {
                    typeText = translations.finalClient;
                }
                let status = company.actived ? translations.true : translations.false;
                let rowContent = `
                    <td style="text-align: center">
                      <div class="row">
                        <div>
                          ${buttonsHtml}
                        </div>
                      </div>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-secondary mb-0">${company.nit}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-secondary mb-0">${company.company_name}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-secondary mb-0">${company.legal_representative}</span>
                    </td>
                `;

                // Condiciona la visibilidad de la columna 'type' según el valor de company_user
                if (company_user === '1') {
                    rowContent += `<td class="align-middle text-center text-sm p-2">${typeText}</td>`;
                }                
                rowContent += `<td class="align-middle text-center text-sm p-2">${status}</td>`;
                row.innerHTML = rowContent;
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
