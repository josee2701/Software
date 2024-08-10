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
    const url = `${languagePrefix}/realtime/commands/send-commands${queryParam}`;

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const rows = document.querySelector("#send-command-tbody");
            rows.innerHTML = ''; // Limpiar el contenido actual
            data.results.forEach((send_command, index) => {
                const row = document.createElement("tr");
                let statusText = '';
                if (send_command.status === false) {
                    statusText = translations.false;
                } else if (send_command.status === true ) {
                    statusText = translations.true;
                }

                row.innerHTML = `
                    <td class="align-middle text-center text-sm">
                        ${index + 1}
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${send_command.command}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${send_command.codigo}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${send_command.model}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${send_command.license}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-secondary mb-0">${statusText}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0 utc-date-5">${send_command.shipping_date}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0 utc-date">${send_command.answer_date}</span>
                    </td>

                `;

                rows.appendChild(row);

            });
            document.querySelectorAll('.utc-date').forEach(element => {
                const dateStr = element.textContent.trim(); // Eliminar espacios en blanco alrededor del texto
                if (dateStr) {
                    const utcDate = new Date(dateStr + ' UTC');
                    element.textContent = utcDate.toLocaleString(undefined, {
                        year: 'numeric', month: '2-digit', day: '2-digit',
                        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
                    });
                } else {
                    // Si no se encuentra ninguna fecha, dejar el contenido de la etiqueta sin cambios
                }
            });

            document.querySelectorAll('.utc-date-5').forEach(element => {
                const dateStr5 = element.textContent.trim(); // Eliminar espacios en blanco alrededor del texto
                if (dateStr5) {
                    const utcDate5 = new Date(dateStr5 + ' UTC-5');
                    element.textContent = utcDate5.toLocaleString(undefined, {
                        year: 'numeric', month: '2-digit', day: '2-digit',
                        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
                    });
                } else {
                    // Si no se encuentra ninguna fecha, dejar el contenido de la etiqueta sin cambios
                }
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
