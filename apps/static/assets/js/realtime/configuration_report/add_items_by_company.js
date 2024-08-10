var translations = {
    confirmMessage: "{% trans 'Please select a company.' %}",
};

$(document).ready(function() {
    const companySelect = $('#company-select');
    const editButton = $('#edit-button');
    const widgetsContainer = $('#widgets-container');
    const reportsContainer = $('#reports-container');
    const alerts = $('.alert');

    companySelect.select2();

    companySelect.on('change', function() {
        const companyId = $(this).val();
        const languagePrefix = getLanguagePrefix();

        function getLanguagePrefix() {
            const path = window.location.pathname;
            const languageCode = path.split('/')[1];
            const supportedLanguages = ['en', 'es', 'es-co', 'es-mx', 'es-es'];
            const isLanguageSupported = supportedLanguages.includes(languageCode);
            return isLanguageSupported ? `/${languageCode}` : '';
        }

        if (companyId) {
            editButton.attr('href', `${languagePrefix}/realtime/configuration-report/update/${companyId}`);
            editButton.removeAttr('disabled');

            fetch(`${languagePrefix}/realtime/get-instance-data/?company_id=${companyId}`)
                .then(response => response.json())
                .then(data => {
                    const infoWidgets = Array.isArray(data.info_widgets) ? data.info_widgets : JSON.parse(data.info_widgets || '[]');
                    const infoReports = Array.isArray(data.info_reports) ? data.info_reports : JSON.parse(data.info_reports || '[]');

                    widgetsContainer.empty();
                    if (infoWidgets.length > 0) {
                        infoWidgets.forEach(widgetLabel => {
                            widgetsContainer.append(`<div class="item">${widgetLabel}</div>`);
                        });
                    }

                    reportsContainer.empty();
                    if (infoReports.length > 0) {
                        infoReports.forEach(reportLabel => {
                            reportsContainer.append(`<div class="item">${reportLabel}</div>`);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        } else {
            editButton.attr('disabled', 'disabled');
            editButton.attr('href', '#');
            widgetsContainer.empty();
            reportsContainer.empty();
        }

        alerts.each(function() {
            $(this).hide();
        });
    });

    editButton.on('click', function(event) {
        if (!companySelect.val()) {
            event.preventDefault();
            alert(translations.confirmMessage);
        }
    });
});
