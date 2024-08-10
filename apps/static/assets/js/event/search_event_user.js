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
    const url = `${languagePrefix}/events/user/event-user${queryParam}`;

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const rows = document.querySelector("#event-user-tbody");
            rows.innerHTML = ''; // Limpiar el contenido actual

            data.results.forEach(event_user => {
                const row = document.createElement("tr");
                const updateUrl = updateEventUrl.replace('0', `${event_user.id}`);
                const deleteUrl = deleteEventUrl.replace('0', `${event_user.id}`);
                let alarmCenter = event_user.central_alarm ? translations.yes : translations.no;
                let alarmUser = event_user.user_alarm ? translations.yes : translations.no;
                let alarmEmail = event_user.email_alarm ? translations.yes : translations.no;
                let alarmSound = event_user.alarm_sound ? translations.yes : translations.no;
                let priorityText = '';
                if (event_user.sound_priority === 'Low') {
                    priorityText = translations.low;
                } else if (event_user.sound_priority === 'Medium' ) {
                    priorityText = translations.medium;
                } else if (event_user.sound_priority === 'High' ) {
                    priorityText = translations.high;
                }

                let buttonsHtml = '';
                if (permiseChange === "True") { // Verifica el permiso de edición
                    buttonsHtml += `<button type="button" hx-get="${updateUrl}" class="btn btn-primary btn-sm" hx-target="#modal .modal-content" style="margin-right: 3px;"><i class="fa-solid fa-pencil"></i></button>`;
                }
                if (permiseDelete === "True") { // Verifica el permiso de eliminación
                    buttonsHtml += `<button type="button" hx-get="${deleteUrl}" class="btn btn-danger btn-sm ml-2"  hx-target="#modal .modal-content" style="margin-right: 3px;"><i class="fa-solid fa-trash"></i></button>`;
                }

                if (event_user.type_alarm_sound !== '') {
                buttonsHtml += `<button class="btn btn-primary btn-sm" onclick="toggleSound('${event_user.type_alarm_sound}', this)">
                        <i class="fas fa-play"></i>
                    </button>`;
                }

                function formatTime(timeString) {
                    if (!timeString) return '--';
                    const [hours, minutes] = timeString.split(':');
                    return `${hours}:${minutes}`;
                }

                row.innerHTML = `
                    <td>${buttonsHtml}</td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${event_user.alias}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${event_user.company}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-secondary mb-0">${alarmCenter}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-secondary mb-0">${alarmUser}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-secondary mb-0">${alarmEmail}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-secondary mb-0">${alarmSound}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-secondary mb-0">${priorityText}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">${event_user.get_type_alarm_sound_display}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <div style="inline-size: 30px; block-size: 20px; background-color: ${event_user.color}; margin: 0 auto;"></div>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">
                            ${event_user.start_time ? formatTime(event_user.start_time) : '--'}
                        </span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="font-weight-normal mb-0">
                            ${event_user.start_time ? formatTime(event_user.end_time) : '--'}
                        </span>
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
