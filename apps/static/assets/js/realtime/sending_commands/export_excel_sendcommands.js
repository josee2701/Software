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
    const url = `${languagePrefix}/realtime/commands/export-commands${queryParam}`;

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

        // Función para formatear fechas en UTC
        const formatDateUTC = (dateStr) => {
            const date = new Date(dateStr + ' UTC');
            return date.toLocaleString(undefined, {
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
            });
        };

        // Función para formatear fechas en UTC-5
        const formatDateUTC_5 = (dateStr) => {
            const date = new Date(dateStr + ' UTC-5');
            return date.toLocaleString(undefined, {
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
            });
        };

        // Agregar datos
        data.data.forEach(item => {
            wsData.push([
                item.command,
                item.codigo,
                item.model,
                item.license,
                item.status ? translations.true : translations.false,
                formatDateUTC_5(item.shipping_date),
                formatDateUTC(item.answer_date) // Convertir fecha en UTC
            ]);
        });

        const ws = XLSX.utils.aoa_to_sheet(wsData);
        const sheetName = translations.commandsSend || "Commands_Sent";
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