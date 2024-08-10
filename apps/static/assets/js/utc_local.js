//Restar hora local cuando es 0 la hora de la bd//
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
//Restar hora local cuando es 5 la hora de la bd y no se requiere segundos//
document.querySelectorAll('.utc-date-5s').forEach(element => {
    const dateStr = element.textContent.trim(); // Eliminar espacios en blanco alrededor del texto
    if (dateStr) {
        const utcDate = new Date(dateStr + ' UTC-5');
        element.textContent = utcDate.toLocaleString(undefined, {
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit', hour12: false
        });
    } else {
        // Si no se encuentra ninguna fecha, dejar el contenido de la etiqueta sin cambios
    }
});

//Restar hora local cuando es -5 la hora de la bd//
document.querySelectorAll('.utc-date-5').forEach(element => {
    const dateStr = element.textContent.trim(); // Eliminar espacios en blanco alrededor del texto
    if (dateStr) {
        const utcDate = new Date(dateStr + ' UTC-5');
        element.textContent = utcDate.toLocaleString(undefined, {
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
        });
    } else {
        // Si no se encuentra ninguna fecha, dejar el contenido de la etiqueta sin cambios
    }
});
