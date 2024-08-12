document.getElementById('id_password1').addEventListener('input', function() {
  var toggleIconSpan = this.nextElementSibling;
  if (this.value.length > 0) {
    toggleIconSpan.style.display = 'inline-block';
  } else {
    toggleIconSpan.style.display = 'none';
  }
});

document.getElementById('id_password2').addEventListener('input', function() {
  var toggleIconSpan = this.nextElementSibling;
  if (this.value.length > 0) {
    toggleIconSpan.style.display = 'inline-block';
  } else {
    toggleIconSpan.style.display = 'none';
  }
});

function togglePasswordVisibility(passwordFieldId, toggleIconId) {
  var passwordField = document.getElementById(passwordFieldId);
  var toggleIcon = document.getElementById(toggleIconId);
  if (passwordField.type === "password") {
    passwordField.type = "text";
    toggleIcon.classList.remove("fa-eye");
    toggleIcon.classList.add("fa-eye-slash");
  } else {
    passwordField.type = "password";
    toggleIcon.classList.remove("fa-eye-slash");
    toggleIcon.classList.add("fa-eye");
  }
}
