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
    const url = `${languagePrefix}/whitelabel/tickets/tickets-user${queryParam}`;

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const rows = document.querySelector("#ticket-tbody");
            rows.innerHTML = ''; // Limpiar el contenido actual

            data.results.forEach(ticket => {
                const row = document.createElement("tr");

                const viewTicketUrl = ticketViewUrlTemplate.replace('/0/', `/${ticket.id}/`);
                let priorityText = '';
                if (ticket.priority === 'Low') {
                    priorityText = translations.low;
                } else if (ticket.priority === 'Medium') {
                    priorityText = translations.medium;
                } else if (ticket.priority === 'High') {
                    priorityText = translations.high;
                }

                row.innerHTML = `
                    <td class="text-center p-2">
                        <button type="button" hx-get="${viewTicketUrl}" hx-trigger="click" hx-target="#modal .modal-content" class="btn btn-primary btn-sm">
                            <i class="fa-solid fa-eye"></i>
                        </button>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${ticket.id}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${ticket.created_by}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${ticket.subject}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-secondary mb-0">${priorityText}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${ticket.process_type}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        ${ticket.assign_to !== 'Unassigned' ? `<span class="text-secondary mb-0">${ticket.assign_to}</span>` : `<span class="text-secondary mb-0">${translations.unassigned}</span>`}
                    </td>
                    <td class="align-middle text-center text-sm">
                        ${ticket.status === "Open" ? `<span class="text-secondary mb-0">${translations.open}</span>` : `<span class="text-secondary mb-0">${translations.closed}</span>`}
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${ticket.company}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0 utc-date-5s">${ticket.created_at}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0 utc-date-5s">${ticket.last_comment}</span>
                    </td>
                `;

                rows.appendChild(row);
            });

            document.querySelectorAll('.utc-date-5s').forEach(element => {
                const dateStr = element.textContent.trim(); // Eliminar espacios en blanco alrededor del texto
                if (dateStr) {
                    const utcDate5 = new Date(dateStr + ' UTC-5');
                    element.textContent = utcDate5.toLocaleString(undefined, {
                        year: 'numeric', month: '2-digit', day: '2-digit',
                        hour: '2-digit', minute: '2-digit', hour12: false
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
