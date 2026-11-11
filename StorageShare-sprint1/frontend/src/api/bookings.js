import { api } from './client';

export function createBooking({ storagePointId, dropOffAt, pickUpAt, bagsCount }, signal) {
  return api('/bookings/', {
    method: 'POST',
    signal,
    body: {
      storage_point: storagePointId,
      drop_off_at: dropOffAt,
      pick_up_at: pickUpAt,
      bags_count: bagsCount,
    },
  });
}

export function payBooking(bookingId, signal) {
  return api(`/bookings/${encodeURIComponent(bookingId)}/pay/`, {
    method: 'POST',
    signal,
  });
}