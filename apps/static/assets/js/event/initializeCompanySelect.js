document.addEventListener("DOMContentLoaded", function() {
    var previousCompany = document.getElementById("id_company").dataset.previousCompany || "";
    var companySelect = document.getElementById("id_company");
    for (var i = 0; i < companySelect.options.length; i++) {
        if (companySelect.options[i].value === previousCompany) {
            companySelect.options[i].selected = true;
            break;
        }
    }
});
