/* RuralCare AI JavaScript Client Logic */

document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss alert messages after 5 seconds
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) {
        bsAlert.close();
      }
    }, 5000);
  });

  // Client-side Registration Form Validation
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', (e) => {
      const password = document.getElementById('password')?.value;
      const confirmPassword = document.getElementById('confirm_password')?.value;
      const pwdMatchError = document.getElementById('pwdMatchError');

      if (password !== confirmPassword) {
        e.preventDefault();
        if (pwdMatchError) {
          pwdMatchError.classList.remove('d-none');
          pwdMatchError.textContent = "Passwords do not match!";
        } else {
          alert("Passwords do not match!");
        }
      } else if (pwdMatchError) {
        pwdMatchError.classList.add('d-none');
      }
    });
  }

  // Password Visibility Toggle
  const togglePasswordBtns = document.querySelectorAll('.toggle-password-btn');
  togglePasswordBtns.forEach(btn => {
    btn.addEventListener('click', function () {
      const targetId = this.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (input) {
        const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
        input.setAttribute('type', type);
        const icon = this.querySelector('i');
        if (icon) {
          icon.classList.toggle('bi-eye');
          icon.classList.toggle('bi-eye-slash');
        }
      }
    });
  });
});
