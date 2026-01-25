async function loadOrders(){
    const loading = document.getElementById('ordersLoading');
    const errorDiv = document.getElementById('ordersError');

    loading.style.display = 'block';
    errorDiv.style.display = 'none';

    try{
        const response = await apiCall('/admin/api/bookings');
        loading.style.display = 'none';

        if(response.success && Array.isArray(response.bookings)){
            allOrders = response.bookings;
            filteredOrders = [...allOrders];
            renderOrdersTable(filteredOrders);
        } else {
            throw new Error('Invalid response format');
        }
    }catch(e){
        loading.style.display = 'none';
        errorDiv.textContent = 'Error loading orders: ' + e.message;
        errorDiv.style.display = 'block';
        console.error('Error loading orders:', e);
    }
}

function renderOrdersTable(orders){
    const tableBody = document.getElementById('ordersTableBody');

    if(!tableBody) return;

    tableBody.innerHTML = '';

    if(orders.length === 0){
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = '<td colspan="7" class="empty-state">No orders found</td>';
        tableBody.appendChild(emptyRow);
        return;
    }

    orders.forEach(order => {
        const orderId = order._id || order.id;
        const statusClass = `status-${order.status.toLowerCase()}`;

        let actionButtons = `
            <button class="action-btn action-view" onclick="viewOrderDetails('${orderId}')" title="View Details" type="button">
                <i class="fas fa-eye"></i>
            </button>
        `;

        if (order.status === 'Pending') {
            actionButtons += `
                <button class="action-btn action-ingredients" onclick="manageIngredients('${orderId}')" title="Manage Ingredients" type="button">
                    <i class="fas fa-list-check"></i>
                </button>
            `;
        } else if (order.status === 'APPROVED') {
            actionButtons += `
                <button class="action-btn action-pdf" onclick="downloadOrderPDF('${orderId}')" title="Download PDF" type="button">
                    <i class="fas fa-download"></i>
                </button>
                <button class="action-btn action-ingredients" onclick="manageIngredients('${orderId}')" title="Edit Ingredients" type="button">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="action-btn" style="background: var(--success); color: white;" onclick="markOrderCompleted('${orderId}')" title="Mark Completed" type="button">
                    <i class="fas fa-check"></i>
                </button>
            `;
        } else if (order.status === 'Completed') {
            actionButtons += `
                <button class="action-btn action-pdf" onclick="downloadOrderPDF('${orderId}')" title="Download PDF" type="button">
                    <i class="fas fa-download"></i>
                </button>
                <button class="action-btn" style="background: var(--danger); color: white;" onclick="deleteOrder('${orderId}', this)" title="Delete Order" type="button">
                    <i class="fas fa-trash"></i>
                </button>
            `;
        } else if (order.status === 'Cancelled') {
            actionButtons += `
                <button class="action-btn" style="background: var(--danger); color: white;" onclick="deleteOrder('${orderId}', this)" title="Delete Order" type="button">
                    <i class="fas fa-trash"></i>
                </button>
            `;
        }

        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="order-id">${orderId.substring(0, 8)}...</td>
            <td>${order.customer_name}</td>
            <td>${order.event_date}</td>
            <td>${order.guests}</td>
            <td class="order-amount">₹${order.pricing?.total || 0}</td>
            <td><span class="status-badge ${statusClass}">${order.status}</span></td>
            <td style="display: flex; gap: 6px; flex-wrap: wrap;">
                ${actionButtons}
            </td>
        `;

        tableBody.appendChild(row);
    });
}

function applyFilters(){
    const fromDate = document.getElementById('filterFromDate').value;
    const toDate = document.getElementById('filterToDate').value;
    const timeSlot = document.getElementById('filterTimeSlot').value;
    const status = document.getElementById('filterStatus').value;

    filteredOrders = allOrders.filter(order => {
        if(fromDate && order.event_date < fromDate) return false;
        if(toDate && order.event_date > toDate) return false;
        if(timeSlot && order.time_slot !== timeSlot) return false;
        if(status && order.status !== status) return false;
        return true;
    });

    renderOrdersTable(filteredOrders);
}

function clearFilters(){
    document.getElementById('filterFromDate').value = '';
    document.getElementById('filterToDate').value = '';
    document.getElementById('filterTimeSlot').value = '';
    document.getElementById('filterStatus').value = '';
    filteredOrders = [...allOrders];
    renderOrdersTable(filteredOrders);
}

async function viewOrderDetails(orderId){
    try{
        const response = await apiCall(`/admin/api/bookings/${orderId}`);
        if(response.success){
            const order = response.booking;
            const details = `Order ID: ${orderId}
Customer: ${order.customer_name}
Phone: ${order.mobile}
Email: ${order.email}
Event Date: ${order.event_date}
Time Slot: ${order.time_slot}
Guests: ${order.guests}
Location: ${order.event_location}
Service Type: ${order.service_type}
Food Preference: ${order.food_preference}
Status: ${order.status}
Total Amount: ₹${order.pricing?.total || 0}

Dishes:
${order.dishes?.map(d => `- ${d.dish_name} (${d.quantity})`).join('\n') || 'No dishes'}

Pricing Breakdown:
Subtotal: ₹${order.pricing?.subtotal || 0}
Service Charge (10%): ₹${order.pricing?.service_charge || 0}
GST (5%): ₹${order.pricing?.gst || 0}
Total: ₹${order.pricing?.total || 0}`;
            alert(details);
        }
    }catch(e){
        alert('Error loading order details: ' + e.message);
    }
}

async function manageIngredients(orderId){
    // Redirect to finalization.html with booking_id parameter
    window.location.href = `finalization.html?booking_id=${orderId}`;
}

async function downloadOrderPDF(orderId){
    window.open(`/admin/api/ingredients/booking/${orderId}/pdf`, '_blank');
}

async function markOrderCompleted(orderId){
    if(!confirm('Are you sure you want to mark this order as completed?')){
        return;
    }

    try{
        const response = await apiCall(`/admin/api/bookings/${orderId}/status`, 'PATCH', { status: 'Completed' });
        if(response.success){
            alert('✅ Order marked as completed successfully');
            loadOrders();
        }
    }catch(e){
        alert('❌ Error updating order status: ' + e.message);
    }
}

async function deleteOrder(orderId, buttonElement){
    if(!confirm('⚠️ Are you sure you want to PERMANENTLY delete this order?\n\nThis action cannot be undone.')){
        return;
    }

    try{
        const response = await apiCall(`/admin/api/bookings/${orderId}`, 'DELETE');

        if(response.success){
            alert('✅ Order deleted successfully');

            if(buttonElement){
                const row = buttonElement.closest('tr');
                if(row){
                    row.remove();
                }
            }

            // loadStats() - not needed on view-orders page
        }
    }catch(e){
        alert('❌ Error deleting order: ' + e.message);
    }
}

// Wrapper functions for loading animations
async function clearFiltersWithUI(btn) {
    setButtonLoading(btn, true);
    try {
        await clearFilters();
    } finally {
        setButtonLoading(btn, false);
    }
}
