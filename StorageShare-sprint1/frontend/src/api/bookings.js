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

export function cancelPendingBooking(bookingId, signal) {
  return api(`/bookings/${encodeURIComponent(bookingId)}/cancel/`, {
    method: 'POST',
    signal,
  });
}

export function getBookingHistory(signal) {
  return api('/bookings/history/', { signal });
}

export function getPendingBooking(signal) {
  return api('/bookings/pending/', { signal });
}

export function getPartnerBookings(signal) {
  return api('/partner/bookings/', { signal });
}
export function getBookingByToken(token, signal) {
  return api(`/bookings/by-token/${encodeURIComponent(token)}/`, { signal });
}

export function checkInBooking(token, signal) {
  return api(`/bookings/by-token/${encodeURIComponent(token)}/check-in/`, { method: 'POST', signal });
}

export function checkOutBooking(token, signal) {
  return api(`/bookings/by-token/${encodeURIComponent(token)}/check-out/`, { method: 'POST', signal });
}
