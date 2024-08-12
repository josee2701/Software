document.getElementById('exportExcelBtn').addEventListener('click', async () => {
    // Mostrar el modal de progreso con opciones para no cerrar al hacer clic fuera
    const downloadModal = new bootstrap.Modal(document.getElementById('downloadModal'), {
        backdrop: 'static',
        keyboard: true
    });
    downloadModal.show();

    // Simular progreso de descarga (opcional)
    const progressBar = document.getElementById('downloadProgressBar');
    progressBar.style.width = '0%';
    progressBar.textContent = '0%';

    let progress = 0;
    const interval = setInterval(() => {
        progress += 10;
        progressBar.style.width = `${progress}%`;
        progressBar.textContent = `${progress}%`;
        if (progress >= 100) {
            clearInterval(interval);
        }
    }, 100);

    // Esperar un poco para que el modal se muestre
    await new Promise(resolve => setTimeout(resolve, 100));

    const languagePrefix = getLanguagePrefix();
    const query = document.getElementById("search-input").value.trim();
    const queryParam = query ? `?query=${encodeURIComponent(query)}` : '';
    const url = `${languagePrefix}/events/user/export-eventsusers${queryParam}`;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();

        // Crear y descargar el archivo Excel
        const wb = XLSX.utils.book_new();
        const wsData = [];

        // Agregar encabezados
        wsData.push(data.headers);

        // Agregar datos
        data.data.forEach(item => {
            priorityText = '';
            if (item.sound_priority === 'Low') {
                priorityText = translations.low;
            } else if (item.sound_priority === 'Medium' ) {
                priorityText = translations.medium;
            } else if (item.sound_priority === 'High' ) {
                priorityText = translations.high;
            }
            wsData.push([
                item.alias,
                item.company,
                item.central_alarm ? translations.yes : translations.no,
                item.user_alarm ? translations.yes : translations.no,
                item.email_alarm ? translations.yes : translations.no,
                item.alarm_sound ? translations.yes : translations.no,
                priorityText,
                item.get_type_alarm_sound_display,
                item.color,
                item.start_time,
                item.end_time,
            ]);
        });

        const ws = XLSX.utils.aoa_to_sheet(wsData);
        const sheetName = translations.eventsUser || "Events_Users";
        const fileName = sheetName + '.xlsx';
        XLSX.utils.book_append_sheet(wb, ws, sheetName);
        XLSX.writeFile(wb, fileName);

        // Ocultar el modal de progreso después de la descarga
        progressBar.style.width = '100%';
        progressBar.textContent = '100%';
        setTimeout(() => {
            downloadModal.hide();
        }, 500); // Esperar medio segundo para mostrar el 100%
    } catch (error) {
        console.error('Error:', error);

        // Ocultar el modal de progreso en caso de error
        progressBar.style.width = '100%';
        progressBar.textContent = '100%';
        setTimeout(() => {
            downloadModal.hide();
        }, 500); // Esperar medio segundo para mostrar el 100%
    }
});

function setPageAndSubmit(page) {
    document.getElementById('page-input').value = page;
    document.getElementById('pagination-form').submit();
}