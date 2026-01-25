from backend.db import orders_collection

# Get completed bookings and check their IP fields
completed = list(orders_collection.find({'status': 'Completed'}))
print(f'Found {len(completed)} completed bookings')

for i, booking in enumerate(completed, 1):
    print(f'\nBooking {i}:')
    print(f'  ID: {booking.get("_id")}')
    print(f'  user_ip: {booking.get("user_ip")}')
    print(f'  ip_address: {booking.get("ip_address")}')
    print(f'  event_date: {booking.get("event_date")}')
