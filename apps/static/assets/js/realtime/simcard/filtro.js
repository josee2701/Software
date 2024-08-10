$(document).ready(function() {
  // Guarda el plan de datos seleccionado inicialmente
  var initialDataPlanId = $('#id_data_plan').val();

  // Función para cargar los planes de datos
  function loadDataPlans(companyId, selectedDataPlanId = initialDataPlanId) {
      var url = `/es/realtime/simcards/api/data-plans/${companyId}/`;

      fetch(url)
          .then(response => {
              if (!response.ok) throw new Error("Network response was not ok");
              return response.json();
          })
          .then(data => {
              var dataPlanSelect = $('#id_data_plan');
              dataPlanSelect.empty().append('<option value="">---------</option>');

              // Agrega los nuevos planes de datos al select
              data.forEach(function(plan) {
                  var optionElement = new Option(plan.name,plan.operator, plan.id);
                  dataPlanSelect.append(optionElement);
              });

              // Establece el plan de datos previamente seleccionado si está en las nuevas opciones
              if (selectedDataPlanId && $(`#id_data_plan option[value=${selectedDataPlanId}]`).length > 0) {
                  dataPlanSelect.val(selectedDataPlanId);
              }
          })
          .catch(error => {
              console.error("Error loading the data plans:", error);
          });
  }

  // Evento 'change' para el select de compañía
  $('#id_company').change(function() {
      var companyId = $(this).val();
      loadDataPlans(companyId); // No pasamos el selectedDataPlanId aquí porque queremos reutilizar el valor inicial si es necesario
  });

  // Inicializa los planes de datos en el load si hay un valor de compañía
  if ($('#id_company').val()) {
      $('#id_company').trigger('change');
  } else {
      $('#id_data_plan').empty().append('<option value="">---------</option>');
  }
});
