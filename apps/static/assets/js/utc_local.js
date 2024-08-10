//Restar hora local.//
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
