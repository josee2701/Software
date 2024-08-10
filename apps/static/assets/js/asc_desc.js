function sortTable(columnIndex) {
    var table, rows, switching, i, x, y, shouldSwitch, dir, switchCount = 0;
    table = document.querySelector(".table-responsive .table");
    switching = true;
    dir = "asc";

    while (switching) {
        switching = false;
        rows = table.rows;

        for (i = 1; i < (rows.length - 1); i++) {
            shouldSwitch = false;
            x = rows[i].getElementsByTagName("TD")[columnIndex];
            y = rows[i + 1].getElementsByTagName("TD")[columnIndex];

            if (dir == "asc") {
                if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                    shouldSwitch = true;
                    break;
                }
            } else if (dir == "desc") {
                if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                    shouldSwitch = true;
                    break;
                }
            }
        }

        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchCount++;
        } else {
            if (switchCount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
            }
        }
    }
}
$(document).ready(function() {
    $('.sort-link').click(function() {
        // Restablecer todas las flechas a estado inactivo
        $('.sort-arrow').removeClass('active');

        // Obtener la flecha correspondiente a la dirección actual
        var arrow = $(this).find('.sort-arrow');
        arrow.addClass('active'); // Activar la flecha correspondiente
    });
});
