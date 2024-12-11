function toggle_password() {

  const passwordInput = document.getElementById('password');
  const toggleIcon = document.getElementById('toggle_password');

  if (passwordInput.type === 'password') {

    passwordInput.type = 'text';
    toggleIcon.src = 'static/images/invisible.png';
    toggleIcon.alt = 'Hide Password';
    toggleIcon.title = 'Hide Password';

  } else {

    passwordInput.type = 'password';
    toggleIcon.src = 'static/images/visible.png';
    toggleIcon.alt = 'Show Password';
    toggleIcon.title = 'Show Password';

  }

}
