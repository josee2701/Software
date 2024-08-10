// Actualizar paginate_by y enviar formulario solo si el valor cambió
document.getElementById('paginate-by').addEventListener('change', function() {
    var newPaginateByValue = this.value;
    var paginateByHiddenInput = document.getElementById('input-paginate-by');

    if (newPaginateByValue !== paginateByHiddenInput.value) {
        paginateByHiddenInput.value = newPaginateByValue;
        document.getElementById('search-form').submit();
    }
});

function updatePaginateBy() {
    var paginateBySelect = document.getElementById('paginate-by');
    document.getElementById('input-paginate-by').value = paginateBySelect.value;
}

function updatePageValue() {
    var pageLinks = document.querySelectorAll('.page-link');
    var pageInput = document.getElementById('input-page-by');
    pageLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            var selectedPage = this.getAttribute('data-page');
            pageInput.value = selectedPage;
            document.getElementById('search-form').submit();
        });
    });
}

updatePageValue();
