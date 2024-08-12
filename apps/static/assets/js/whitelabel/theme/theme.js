document.addEventListener('DOMContentLoaded', function () {
    const allowedFormats = ["png", "jpg", "jpeg"];
    const maxSizeMB = 4; // Tamaño máximo en megabytes
    const maxSizeBytes = maxSizeMB * 1024 * 1024; // Convertir a bytes
    const overlay = document.getElementById('overlay');
    const form = document.getElementById('settings-form');
    
    // Mostrar el overlay al enviar el formulario
    form.addEventListener('submit', function () {
        overlay.classList.remove('d-none');
        overlay.style.display = 'flex';
    });
    function handleImagePreview(inputId, previewId, cropButtonId) {
        const input = document.getElementById(inputId);
        const preview = document.getElementById(previewId);
        const cropButton = document.getElementById(cropButtonId);
        let cropper;

        input.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (file) {
                const fileExtension = file.name.split(".").pop().toLowerCase();
                if (!allowedFormats.includes(fileExtension)) {
                    alert(translations.isNotAllowed);
                    input.value = ''; // Limpiar el campo de entrada
                    preview.style.display = 'none';
                    return;
                }
                if (file.size > maxSizeBytes) {
                    alert(translations.alertImageExceedSize);
                    input.value = ''; // Limpiar el campo de entrada
                    preview.style.display = 'none';
                    return;
                }
                const reader = new FileReader();
                reader.onload = function (event) {
                    preview.src = event.target.result;
                    preview.style.display = 'block';
                    if (cropper) {
                        cropper.destroy();
                    }
                    if (inputId === 'id_sidebar_image') {
                        cropper = new Cropper(preview, {
                            aspectRatio: 1 / 3,
                            viewMode: 2,
                            autoCropArea: 1,
                        });
                    }
                };
                reader.readAsDataURL(file);
            } else {
                preview.style.display = 'none';
            }
        });

        if (cropButton) {
            cropButton.addEventListener('click', function () {
                if (cropper) {
                    const canvas = cropper.getCroppedCanvas();
                    canvas.toBlob(function (blob) {
                        const fileInputElement = document.createElement('input');
                        fileInputElement.setAttribute('type', 'hidden');
                        fileInputElement.setAttribute('name', inputId + '_cropped');
                        const dataTransfer = new DataTransfer();
                        dataTransfer.items.add(new File([blob], 'cropped_' + input.files[0].name));
                        fileInputElement.files = dataTransfer.files;
                        input.closest('form').appendChild(fileInputElement);

                        // Reemplaza el archivo original con el recortado
                        input.files = dataTransfer.files;
                    });
                }
            });
        }
    }

    handleImagePreview('id_sidebar_image', 'preview-sidebar_image', 'crop-button-sidebar_image');
    handleImagePreview('id_lock_screen_image', 'preview-lock_screen_image', null);
});
