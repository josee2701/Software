// Obtener referencia a la casilla de verificación de "Alarm"
var alarm_checkbox = document.getElementById("id_alarm_sound");

// Obtener referencias a las casillas de verificación que queremos deshabilitar
var central_notification_checkbox = document.getElementById("id_central_alarm");
var user_notification_checkbox = document.getElementById("id_user_alarm");
var email_notification_checkbox = document.getElementById("id_email_alarm");

// Función para activar/desactivar las casillas de verificación
function toggleCheckboxes(isAlarmChecked) {
    central_notification_checkbox.disabled = !isAlarmChecked;
    user_notification_checkbox.disabled = !isAlarmChecked;
    email_notification_checkbox.disabled = !isAlarmChecked;

    // Si la casilla de "Alarm" no está marcada, desmarcar las otras casillas
    if (!isAlarmChecked) {
        central_notification_checkbox.checked = false;
        user_notification_checkbox.checked = false;
        email_notification_checkbox.checked = false;
    }
}

// Agregar evento "change" a la casilla de verificación de "Alarm"
alarm_checkbox.addEventListener("change", function() {
    toggleCheckboxes(this.checked);
});

// Llamar a la función inicialmente para configurar el estado inicial de las casillas
toggleCheckboxes(alarm_checkbox.checked);

// Agrego sonidos a eventos 
function getSelectedSoundUrl() {
    var selectElement = document.getElementById("id_type_alarm_sound");
    return selectElement.options[selectElement.selectedIndex].value;
}

function activate(id_alarm_sound) {
    var ddl = document.getElementById("id_sound_priority");
    ddl.disabled = !id_alarm_sound.checked;
    var ddl_2 = document.getElementById("id_type_alarm_sound");
    ddl_2.disabled = !id_alarm_sound.checked;
    document.getElementById("id_start_time").disabled = !id_alarm_sound.checked;
    document.getElementById("id_end_time").disabled = !id_alarm_sound.checked;
    document.getElementById("id_color").disabled = !id_alarm_sound.checked;
    document.getElementById("id_alarm_sound_file").disabled = !id_alarm_sound.checked; // Agregar esta línea

    // Mostrar el campo de selección de archivo de sonido cuando se marque la casilla de alarma
    var alarm_sound_file_div = document.getElementById("id_alarm_sound_file");
    alarm_sound_file_div.style.display = id_alarm_sound.checked ? "block" : "none";

    if (!ddl.disabled) {
        ddl.focus();
    } else {
        var field_1 = document.getElementById("id_sound_priority");
        var field_2 = document.getElementById("id_type_alarm_sound");
        var field_3 = document.getElementById("id_end_time");
        var field_4 = document.getElementById("id_start_time");
        field_1.value = "";
        field_2.value = "";
        field_3.value = "";
        field_4.value = "";
    }
}
