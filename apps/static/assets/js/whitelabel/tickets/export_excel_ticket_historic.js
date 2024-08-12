// Declarar una bandera para verificar si la descarga está en curso
let isDownloading = false;

document.getElementById('exportExcelBtn').addEventListener('click', async (event) => {
    if (isDownloading) {
        // Si la descarga ya está en curso, salir de la función para evitar duplicados
        return;
    }

    // Activar la bandera para indicar que la descarga está en curso
    isDownloading = true;

    // Desactivar el botón para evitar múltiples clics
    const exportBtn = event.target;
    exportBtn.disabled = true;

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
    const url = `${languagePrefix}/whitelabel/tickets/export-tickets-historic${queryParam}`;

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
        const formatDateLocal = (dateStr) => {
            // Crear un objeto Date asumiendo que dateStr está en UTC
            const date = new Date(dateStr);
        
            // Ajustar a la zona horaria de UTC-5 (que es 300 minutos detrás de UTC)
            const utcOffset = -5 * 60; // UTC-5 en minutos
            const localOffset = date.getTimezoneOffset(); // Diferencia de la zona horaria local en minutos
            const totalOffset = utcOffset + localOffset; // Compensación total
        
            // Ajustar la fecha al agregar la compensación total en milisegundos
            const adjustedDate = new Date(date.getTime() + totalOffset * 60000);
        
            // Formatear la fecha ajustada a la hora local
            return adjustedDate.toLocaleString(undefined, {
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
            });
        };
        
        // Agregar datos
        data.data.forEach(item => {
            let priorityText = '';
            let statusText = '';
            if (item.priority === 'Low') {
                priorityText = translations.low;
            } else if (item.priority === 'Medium') {
                priorityText = translations.medium;
            } else if (item.priority === 'High') {
                priorityText = translations.high;
            }
            if (item.status === 'Open') {
                statusText = translations.open;
            } else if (item.status === 'Closed') {
                statusText = translations.closed;
            }
            if (item.assign_to === 'Unassigned') {
                item.assign_to = translations.unassigned;
            }
            if (item.company === 'Distributor') {
                item.company = translations.distributor;
            }
            
            wsData.push([
                item.id,
                item.created_by,
                item.subject,
                priorityText,
                item.process_type,
                item.assign_to,
                statusText,
                item.company,
                formatDateLocal(item.created_at),
                formatDateLocal(item.last_comment),
                item.duration,
            ]);
        });

        const ws = XLSX.utils.aoa_to_sheet(wsData);
        const sheetName = translations.ticketHistoric || "Cases_Historic";
        const fileName = sheetName + '.xlsx';
        XLSX.utils.book_append_sheet(wb, ws, sheetName);
        XLSX.writeFile(wb, fileName);

        // Ocultar el modal de progreso después de la descarga
        progressBar.style.width = '100%';
        progressBar.textContent = '100%';
        setTimeout(() => {
            downloadModal.hide();
            // Reactivar el botón después de la descarga
            exportBtn.disabled = false;
            // Restablecer la bandera
            isDownloading = false;
        }, 500); // Esperar medio segundo para mostrar el 100%
    } catch (error) {
        console.error('Error:', error);

        // Ocultar el modal de progreso en caso de error
        progressBar.style.width = '100%';
        progressBar.textContent = '100%';
        setTimeout(() => {
            downloadModal.hide();
            // Reactivar el botón en caso de error
            exportBtn.disabled = false;
            // Restablecer la bandera
            isDownloading = false;
        }, 500); // Esperar medio segundo para mostrar el 100%
    }
});

function setPageAndSubmit(page) {
    document.getElementById('page-input').value = page;
    document.getElementById('pagination-form').submit();
}