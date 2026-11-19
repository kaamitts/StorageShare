import { zonedDateTimeToISOString } from './zoned-time.js';

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

function withinHours(value, opensAt, closesAt, isDropOff, is24Hours) {
  if (is24Hours || !opensAt || !closesAt) return true;
  const moment = String(value).slice(11, 16);
  const opening = String(opensAt).slice(0, 5);
  const closing = String(closesAt).slice(0, 5);
  if (opening === closing) return true;
  if (moment === closing) return !isDropOff;
  if (opening < closing) return moment >= opening && moment < closing;
  return moment >= opening || moment < closing;
}

export function validateBooking({
  dropOffAt, pickUpAt, bagsCount, opensAt, closesAt, is24Hours = false,
}) {
  const errors = {};
  const toInstant = value => {
    if (!value) return null;
    const [date, time] = value.split('T');
    const iso = zonedDateTimeToISOString(date, time);
    return iso ? new Date(iso) : null;
  };
  const drop = toInstant(dropOffAt);
  const pick = toInstant(pickUpAt);
  const dropValid = drop && !Number.isNaN(drop.getTime());
  const pickValid = pick && !Number.isNaN(pick.getTime());

  if (!dropValid) errors.drop_off_at = 'dropOffRequired';
  else if (drop <= new Date()) errors.drop_off_at = 'dropOffInFuture';
  else if (!withinHours(dropOffAt, opensAt, closesAt, true, is24Hours)) errors.drop_off_at = 'outsideHours';

  if (!pickValid) errors.pick_up_at = 'pickUpRequired';
  else if (dropValid && pick <= drop) errors.pick_up_at = 'pickUpAfterDropOff';
  else if (!withinHours(pickUpAt, opensAt, closesAt, false, is24Hours)) errors.pick_up_at = 'outsideHours';

  const bags = Number(bagsCount);
  if (!Number.isInteger(bags) || bags < 1 || bags > 32767) errors.bags_count = 'bagsInvalid';

  return errors;
}

export function validateStoragePoint(form) {
  const errors = {};
  if (!form.name.trim()) errors.name = 'pointNameRequired';
  if (!form.address.trim()) errors.address = 'addressRequired';
  if (!form.district) errors.district = 'districtRequired';

  const price = Number(form.price_per_bag_per_hour);
  if (form.price_per_bag_per_hour === '' || !Number.isFinite(price) || price < 0) {
    errors.price_per_bag_per_hour = 'priceInvalid';
  }

  const capacity = Number(form.capacity_bags);
  if (!Number.isInteger(capacity) || capacity < 1) errors.capacity_bags = 'capacityInvalid';

  if (!form.is_24_hours) {
    if (!form.opens_at) errors.opens_at = 'opensRequired';
    if (!form.closes_at) errors.closes_at = 'closesRequired';
    else if (form.opens_at && form.closes_at === form.opens_at) errors.closes_at = 'equalHoursUse24';
  }

  return errors;
}

