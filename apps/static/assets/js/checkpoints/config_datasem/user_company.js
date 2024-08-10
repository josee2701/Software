$(document).ready(function () {
    var companySelect = $('#id_company');
    var userSelect = $('#id_user');

    // Inicializar Select2 en los selects
    companySelect.select2();
    userSelect.select2();

    // Añadir la clase form-control al contenedor correcto
    $('.select2-container').addClass('form-control');

    // Eliminar el estilo de ancho en línea
    $('.select2-container').css('width', '');

    // Añadir un event listener para cuando se cambie la compañía
    companySelect.on("change", function () {
        const companyId = $(this).val(); // Obtén el ID de la compañía seleccionada

        if (companyId) {
            // Llamar a la API con el ID de la compañía seleccionada
            fetch(`/es/checkpoints/powerbi/user_company/${companyId}/`)
                .then(response => response.json())
                .then(data => {
                    console.log(data);  // Depuración: Verifica la estructura de la respuesta

                    if (data && Array.isArray(data.user)) {
                        // Limpiar las opciones existentes
                        userSelect.empty();

                        // Añadir las nuevas opciones
                        userSelect.append('<option value="">{% trans "Select User" %}</option>'); // Añadir una opción por defecto
                        data.user.forEach(user => {
                            userSelect.append(new Option(`${user.first_name} ${user.last_name}`, user.id));
                        });

                        console.error("Error: `user` no está definido o no es un array.");
                    }
                })
                .catch(error => console.error("Error fetching users:", error));
        } else {
            userSelect.empty();
            userSelect.append('<option value="">{% trans "Select User" %}</option>');
            userSelect.select2(); // Asegúrate de mantener select2 inicializado
        }
    });
});
