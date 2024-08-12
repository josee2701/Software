$(document).ready(function() {
    const workspaceSelect = $('#id_workspace');
    const reportSelect = $('#id_report');

    // Inicializar Select2 en los selects
    workspaceSelect.select2();
    reportSelect.select2();

    // Añadir la clase form-control al contenedor correcto
    $('.select2-container').addClass('form-control');

    // Eliminar el estilo de ancho en línea
    $('.select2-container').css('width', '');
  
    // Solicitud a la API para obtener los workspaces
    fetch('/es/powerbi/groups/')
      .then(response => response.json())
      .then(data => {
        console.log('Workspaces:', data); // Depuración
        workspaceSelect.empty();
        workspaceSelect.append('<option value="">--------------</option>');
        data.value.forEach(item => {  // Ajustado para acceder al atributo `value`
          workspaceSelect.append(`<option value="${item.id}">${item.name}</option>`);
        });
      })
      .catch(error => console.error('Error al obtener workspaces:', error));
  
    // Manejo del cambio de workspace para obtener los reports
    workspaceSelect.on('change', function() {
      const workspaceId = $(this).val();
      if (workspaceId) {
        fetch(`/es/powerbi/groups/${workspaceId}/reports/`)
          .then(response => response.json())
          .then(data => {
            console.log('Reports:', data); // Depuración
            reportSelect.empty();
            reportSelect.append('<option value="">------------------</option>');
            data.value.forEach(item => {  // Ajustado para acceder al atributo `value`
              reportSelect.append(`<option value="${item.id}">${item.name}</option>`);
            });
          })
          .catch(error => console.error('Error al obtener reports:', error));
      } else {
        reportSelect.empty();
        reportSelect.append('<option value="">{% trans "Select Report" %}</option>');
        reportSelect.select2();  // Asegúrate de mantener select2 inicializado
      }
    });
  });
  