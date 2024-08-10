;(function(){
    let modalInitialized = false;
    let modal;

    const initModal = () => {
      const modalElement = document.getElementById('modal');
      if (!modalElement || modalInitialized) return;

      modal = new bootstrap.Modal(modalElement, {
        backdrop: 'static',
        keyboard: false
      });

      modalInitialized = true; // Marcar como inicializado
      console.log("Modal inicializado"); // Para depuración
    };

    const handleModalContentSwap = () => {
      const modalElement = document.getElementById('modal');
      if (!modalElement) return;

      const modalInstance = bootstrap.Modal.getInstance(modalElement);
      if (modalInstance) {
        modalInstance.show();
        console.log("Modal mostrado"); // Para depuración
      }
    };

    const clearModalContent = () => {
      const modalContentElement = document.getElementById('modal-content');
      if (modalContentElement) {
        modalContentElement.innerHTML = ''; // Limpiar el contenido del modal
      }
    };

    document.addEventListener('DOMContentLoaded', () => {
      initModal();

      htmx.on('htmx:beforeSwap', (e) => {
        console.log("Evento htmx:beforeSwap disparado"); // Para depuración
        if (e.detail.target.id === "modal-content") {
          clearModalContent(); // Limpiar contenido antes de reemplazar
        }
      });

      htmx.on('htmx:afterSwap', (e) => {
        console.log("Evento htmx:afterSwap disparado"); // Para depuración
        if (e.detail.target.id === "modal-content") {
          handleModalContentSwap();
        }
      });

      // Listener para el botón de cerrar
      document.addEventListener('click', function(event) {
          if (event.target.classList.contains('btn-close') || event.target.id === 'cerrarVenta') {
              const modalElement = document.getElementById('modal');
              const modalInstance = bootstrap.Modal.getInstance(modalElement);
              if (modalInstance) {
                  modalInstance.hide();
              }
          }
      });

      // Agregar la clase modal-open al body cuando el modal se muestra
      const modalElement = document.getElementById('modal');
      modalElement.addEventListener('show.bs.modal', function () {
        document.body.classList.add('modal-open');
      });

      // Remover la clase modal-open del body cuando el modal se oculta
      modalElement.addEventListener('hidden.bs.modal', function () {
        document.body.classList.remove('modal-open');
      });
    });
  })();
