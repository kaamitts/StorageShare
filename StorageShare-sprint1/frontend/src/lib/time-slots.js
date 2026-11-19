function minutesOf(value) {
  const [hours, minutes] = String(value).slice(0, 5).split(":").map(Number);
  return hours * 60 + minutes;
}

function formatMinutes(value) {
  const normalized = ((value % 1440) + 1440) % 1440;
  const hours = String(Math.floor(normalized / 60)).padStart(2, "0");
  const minutes = String(normalized % 60).padStart(2, "0");
  return `${hours}:${minutes}`;
}

export function createTimeSlots(opensAt, closesAt, { is24Hours = false, step = 30 } = {}) {
  if (!opensAt || !closesAt || !Number.isInteger(step) || step < 1) return [];

  const start = minutesOf(opensAt);
  const close = minutesOf(closesAt);
  const allDay = is24Hours || start === close;
  const end = allDay ? start + 1440 : close <= start ? close + 1440 : close;
  const slots = [];

  for (let minute = start; allDay ? minute < end : minute <= end; minute += step) {
    slots.push(formatMinutes(minute));
  }
  return slots;
}
