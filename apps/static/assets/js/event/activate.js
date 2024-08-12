function activate(id_alarm_sound) {
    var ddl = document.getElementById("id_sound_priority");
    var ddl_2 = document.getElementById("id_type_alarm_sound");
    var ddl_3 = document.getElementById("id_start_time");
    var ddl_4 = document.getElementById("id_end_time");
    if (id_alarm_sound.checked) {
        ddl.disabled = false;
        ddl_2.disabled = false;
        ddl_3.disabled = false;
        ddl_4.disabled = false;
        document.getElementById("id_color").removeAttribute("disabled");
    } else {
        ddl.disabled = true;
        ddl.value = "";
        ddl_2.disabled = true;
        ddl_2.value = "";
        ddl_3.disabled = true;
        ddl_3.value = "";
        ddl_4.disabled = true;
        ddl_4.value = "";
        document.getElementById("id_color").setAttribute("disabled", "disabled");
    }
}


function update_fields() {
    var alarm = document.getElementById("id_alarm_sound");
    var ddl = document.getElementById("id_sound_priority");
    var ddl_2 = document.getElementById("id_type_alarm_sound");
    var ddl_3 = document.getElementById("id_start_time");
    var ddl_4 = document.getElementById("id_end_time");
    if (alarm.checked) {
        ddl.disabled = false;
        ddl_2.disabled = false;
        ddl_3.disabled = false;
        ddl_4.disabled = false;
        document.getElementById("id_color").removeAttribute("disabled");
    } else {
        ddl.disabled = true;
        ddl_2.disabled = true;
        ddl_3.disabled = true;
        ddl_4.disabled = true;
        document.getElementById("id_color").setAttribute("disabled", "disabled");
    }
}

update_fields()
