let audioPlayer = null;

function toggleSound(soundUrl, button, event) {
    event.preventDefault(); // Evita que se envíe el formulario al hacer clic en el botón
    if (audioPlayer && !audioPlayer.paused) {
        audioPlayer.pause();
        button.innerHTML = '<i class="fas fa-play "></i>';
    } else {
        if(audioPlayer) {
            audioPlayer.pause();
        }
        audioPlayer = new Audio(soundUrl);
        audioPlayer.play();
        button.innerHTML = '<i class="fas fa-pause "></i>';
    }
}

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