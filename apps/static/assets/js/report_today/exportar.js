document.getElementById('exportExcelBtn').addEventListener('click', function() {
    exportReport('xlsx');
});
document.getElementById('exportCsvBtn').addEventListener('click', function() {
    exportReport('csv');
});
document.getElementById('exportPdfBtn').addEventListener('click', function() {
    exportReport('pdf');
});

async function exportReport(format) {
    var formData = new FormData(document.getElementById('search-form'));
    formData.append('format', format);

    // Obtener el token CSRF directamente del formulario
    var csrfToken = formData.get('csrfmiddlewaretoken');

    // Mostrar el modal de progreso
    var downloadModal = new bootstrap.Modal(document.getElementById('downloadModal'), {
        backdrop: 'static',
        keyboard: false
    });
    downloadModal.show();

    var progressBar = document.getElementById('downloadProgressBar');

    // Inicializar la barra de progreso
    progressBar.style.width = '0%';
    progressBar.setAttribute('aria-valuenow', 0);
    progressBar.textContent = '0%';

    // Simular aumento de la barra de progreso
    let progressInterval = setInterval(() => {
        let currentProgress = parseInt(progressBar.getAttribute('aria-valuenow'));
        if (currentProgress < 100) {
            let newProgress = currentProgress + 10;
            progressBar.style.width = `${newProgress}%`;
            progressBar.setAttribute('aria-valuenow', newProgress);
            progressBar.textContent = `${newProgress}%`;
        } else {
            clearInterval(progressInterval);
        }
    }, 920); // Actualizar cada 500ms

    try {
        let response = await fetch('/es/checkpoints/reports/avldat', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            },
        });

        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }

        const blob = await response.blob();

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `report.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);

        // Asegurarse de que la barra de progreso llegue al 100% al final
        progressBar.style.width = '100%';
        progressBar.setAttribute('aria-valuenow', 100);
        progressBar.textContent = '100%';
        clearInterval(progressInterval);
    } catch (error) {
        console.error('Error al exportar el archivo:', error);
    } finally {
        // Ocultar el modal de progreso después de un breve retraso para asegurar la finalización
        setTimeout(() => {
            downloadModal.hide();
            progressBar.style.width = '0%';
            progressBar.setAttribute('aria-valuenow', 0);
            progressBar.textContent = '0%';
        }, 2000); // Retraso de 1 segundo antes de ocultar el modal
    }
}
