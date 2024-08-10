document.addEventListener("DOMContentLoaded", function() {
    const timezoneOffset = new Date().getTimezoneOffset();
    const timezoneField = document.createElement('input');
    timezoneField.setAttribute('type', 'hidden');
    timezoneField.setAttribute('name', 'timezone_offset');
    timezoneField.setAttribute('value', timezoneOffset);
    document.getElementById('search-form').appendChild(timezoneField);
});
