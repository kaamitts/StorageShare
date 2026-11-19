export const BOOKING_TIME_ZONE = 'Asia/Almaty';

function datePartsInZone(date, timeZone) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone,
    year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(date);
  return Object.fromEntries(parts
    .filter(part => part.type !== 'literal')
    .map(part => [part.type, part.value]));
}

/** Convert the wall date/time selected for a point into an unambiguous API timestamp. */
export function zonedDateTimeToISOString(date, time, timeZone = BOOKING_TIME_ZONE) {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(`${date}T${time}`);
  if (!match) return null;

  const [, year, month, day, hour, minute] = match.map(Number);
  const wallTime = Date.UTC(year, month - 1, day, hour, minute);
  const check = new Date(wallTime);
  if (check.getUTCFullYear() !== year || check.getUTCMonth() !== month - 1
      || check.getUTCDate() !== day || check.getUTCHours() !== hour
      || check.getUTCMinutes() !== minute) return null;

  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone,
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  });
  let instant = wallTime;
  // Correct the UTC guess using the zone's represented wall time. Repeat to handle
  // offset transitions without relying on the browser's own time zone.
  for (let attempt = 0; attempt < 3; attempt += 1) {
    const parts = Object.fromEntries(formatter.formatToParts(new Date(instant))
      .filter(part => part.type !== 'literal')
      .map(part => [part.type, Number(part.value)]));
    const representedWallTime = Date.UTC(
      parts.year, parts.month - 1, parts.day, parts.hour, parts.minute,
    );
    const adjustment = wallTime - representedWallTime;
    instant += adjustment;
    if (adjustment === 0) return new Date(instant).toISOString();
  }

  // A wall time skipped by a time-zone transition has no exact instant.
  const result = new Date(instant);
  const parts = formatter.formatToParts(result);
  const represented = Object.fromEntries(parts
    .filter(part => part.type !== 'literal')
    .map(part => [part.type, Number(part.value)]));
  if (represented.year !== year || represented.month !== month || represented.day !== day
      || represented.hour !== hour || represented.minute !== minute) return null;
  return result.toISOString();
}

export function dateInTimeZone(date = new Date(), timeZone = BOOKING_TIME_ZONE) {
  const { year, month, day } = datePartsInZone(date, timeZone);
  return `${year}-${month}-${day}`;
}
