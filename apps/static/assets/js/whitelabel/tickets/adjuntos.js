function initializeAttachmentHandler() {
    const attachmentInput = document.getElementById("id_file");
    const maxSizeMB = 7; // Tamaño máximo en megabytes
    const allowedFormats = ["cfg", "csv", "doc", "docx", "eml", "exe", "jpeg", "jpg", "mp4", "msg", "pdf", "png", "rar", "txt", "xim", "xls", "xlsx", "xml", "zip"];

    attachmentInput.addEventListener("change", handleFileSelect);

    function handleFileSelect(event) {
        const files = event.target.files;
        const previewContainer = document.getElementById("attachment-preview");
        previewContainer.innerHTML = ""; // Limpiar la vista previa antes de agregar nuevos archivos

        let totalSizeMB = 0; // Variable para acumular el tamaño total de los archivos

        for (const file of files) {
            const fileName = file.name;
            const fileSizeMB = file.size / (1024 * 1024); // Convertir a MB

            // Acumular el tamaño total de los archivos seleccionados
            totalSizeMB += fileSizeMB;

            // Verificar si el archivo no está admitido o excede el tamaño máximo permitido
            const fileExtension = fileName.split(".").pop().toLowerCase();
            if (!allowedFormats.includes(fileExtension) || totalSizeMB > maxSizeMB) {
                // Mostrar el mensaje de alerta correspondiente
                if (!allowedFormats.includes(fileExtension)) {
                    alert( translations.file + " " + fileName + " " + translations.isNotAllowed + " " + allowedFormats.join(", "));
                } else if (totalSizeMB > maxSizeMB) {
                    alert(translations.alertFilesExceedsSize + " " + maxSizeMB + " MB.");
                } else {
                    alert(translations.file + fileName + translations.alertFileExceedSize + " " + maxSizeMB + " MB.");
                }
                event.target.value = ""; // Limpiar el campo de entrada
                previewContainer.innerHTML = ""; // Limpiar la vista previa de archivos adjuntos
                return;
            }

            const listItem = document.createElement("div");
            listItem.textContent = fileName + " (" + fileSizeMB.toFixed(2) + " MB)";
            previewContainer.appendChild(listItem);
        }
    }
}

// Llamar a la función de inicialización después de cargar la página
initializeAttachmentHandler();
