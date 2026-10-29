export function validateLogin({ email, password }, t) {
  const errors = {};
  if (!email.trim()) errors.email = t.emailRequired;
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) errors.email = t.invalidEmail;
  if (!password) errors.password = t.passwordRequired;
  return errors;
}

export function validateRegister({ full_name, email, password, role }, t) {
  const errors = {};
  if (!full_name.trim()) errors.full_name = t.nameRequired;
  if (!email.trim()) errors.email = t.emailRequired;
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) errors.email = t.invalidEmail;
  if (!password || password.length < 8) errors.password = t.passwordRequired;
  if (!role) errors.role = t.roleRequired;
  return errors;
}