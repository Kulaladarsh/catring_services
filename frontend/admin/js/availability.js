// Availability Calendar
async function loadCalendar() {
    // Guard: Only load if availability tab is visible
    const availabilityTab = document.getElementById('availability');
    if (!availabilityTab || availabilityTab.classList.contains('active') === false) {
        return;
    }

    const now = Date.now();
    if(calendarCache && (now - calendarCache.timestamp) < cacheExpiry){
        calendarData = calendarCache.data;
        renderCalendar();
        updateStats();
        return;
    }

    try {
        const response = await fetch('/api/bookings/availability-calendar');
        if (response.status === 404) {
            // Graceful fallback for 404
            document.getElementById('loading').textContent = 'Availability calendar is currently unavailable. Please check back later.';
            document.getElementById('calendarGrid').innerHTML = '<div style="grid-column:1/-1;" class="empty-state">Calendar data not available at this time.</div>';
            return;
        }

        const data = await response.json();

        if (data.success) {
            calendarCache = { data: data.calendar, timestamp: now };
            calendarData = data.calendar;
            renderCalendar();
            updateStats();
        } else {
            document.getElementById('loading').textContent = 'Failed to load calendar data';
        }
    } catch (error) {
        console.error('Error loading calendar:', error);
        document.getElementById('loading').textContent = 'Error loading data. Please refresh.';
    }
}

function renderCalendar() {
    const grid = document.getElementById('calendarGrid');
    const loading = document.getElementById('loading');

    loading.style.display = 'none';
    grid.innerHTML = '';

    const filteredData = calendarData.filter(day => {
        if (currentFilter === 'all') return true;
        return day.status === currentFilter.replace('-', '_');
    });

    if (filteredData.length === 0) {
        grid.innerHTML = '<div style="grid-column:1/-1;" class="empty-state">No dates match the selected filter.</div>';
        return;
    }

    filteredData.forEach(day => {
        const date = new Date(day.date);
        const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
        const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

        let statusClass = '';
        if (day.status === 'fully_booked') statusClass = 'fully-booked';
        else if (day.status === 'partially_available') statusClass = 'partially';
        else if (day.status === 'available') statusClass = 'available';

        const card = document.createElement('div');
        card.className = `date-card ${statusClass}`;

        let slotsHTML = '';
        const allSlots = ['Morning', 'Afternoon', 'Night'];

        allSlots.forEach(slot => {
            const isAvailable = day.available_slots.includes(slot);
            const slotClass = isAvailable ? 'available' : 'booked';
            const slotText = isAvailable ? `✓ ${slot}` : `✗ ${slot}`;
            slotsHTML += `<div class="slot ${slotClass}">${slotText}</div>`;
        });

        card.innerHTML = `
            <div class="date-header">${dateStr}</div>
            <div class="date-day">${dayName}</div>
            <div class="slots">
                ${slotsHTML}
            </div>
        `;

        grid.appendChild(card);
    });
}

function updateStats() {
    const availableCount = calendarData.filter(d => d.status === 'available').length;
    const partialCount = calendarData.filter(d => d.status === 'partially_available').length;
    const fullyBookedCount = calendarData.filter(d => d.status === 'fully_booked').length;

    document.getElementById('availableCount').textContent = availableCount;
    document.getElementById('partialCount').textContent = partialCount;
    document.getElementById('fullyBookedCount').textContent = fullyBookedCount;
}

function filterCalendar(filter, btn) {
    currentFilter = filter;

    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    renderCalendar();
}
