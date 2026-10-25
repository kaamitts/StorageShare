export function validateLogin({ email, password }) {
  const errors = {};
  if (!email.trim()) errors.email = 'Email is required';
  if (!password) errors.password = 'Password is required';
  return errors;
}

export function validateRegister({ full_name, email, password, role }) {
  const errors = {};
  if (!full_name.trim()) errors.full_name = 'Full name is required';
  if (!email.trim()) errors.email = 'Email is required';
  if (!password || password.length < 8) errors.password = 'Min. 8 characters';
  if (!role) errors.role = 'Choose a role';
  return errors;
}