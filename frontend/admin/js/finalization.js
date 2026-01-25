// Helper function for category icons
function getCategoryIcon(cat){
    if(cat === 'Vegetables') return '🥬';
    if(cat === 'Non-Vegetarian') return '🍗';
    if(cat === 'Spices' || cat === 'Spices / Masala') return '🌶️';
    if(cat === 'Dairy') return '🥛';
    if(cat === 'Fruit') return '🍎';
    if(cat === 'Grain') return '🌾';
    if(cat === 'Herbs') return '🌿';
    if(cat === 'Beverages') return '🥤';
    if(cat === 'Oil and Fats') return '🫒';
    if(cat === 'Bakery & Sweets') return '🍰';
    return '🧂';
}

// Finalization functions
async function loadFinalizationOrders(){
    try{
        const pendingResponse = await apiCall('/admin/api/bookings?status=Pending');
        const confirmedResponse = await apiCall('/admin/api/bookings?status=Confirmed');
        const approvedResponse = await apiCall('/admin/api/bookings?status=APPROVED');

        if(pendingResponse.success && confirmedResponse.success && approvedResponse.success){
            const orders = [...pendingResponse.bookings, ...confirmedResponse.bookings, ...approvedResponse.bookings];

            orders.sort((a, b) => new Date(a.event_date) - new Date(b.event_date));

            const select = document.getElementById('finalizationOrderSelect');
            select.innerHTML = '<option value="">-- Select Order for Finalization --</option>';

            orders.forEach(order => {
                const orderId = order._id || order.id;
                const statusBadge = order.status === 'Pending' ? '🟡' : order.status === 'APPROVED' ? '🟢' : '🔵';
                select.innerHTML += `
                    <option value="${orderId}">
                        ${statusBadge} ${orderId.substring(0,8)} - ${order.customer_name}
                        (${order.event_date}) - ${order.status}
                    </option>`;
            });
        }
    }catch(e){
        console.error('Error loading finalization orders:', e);
        alert('Error loading orders: ' + e.message);
    }
}

async function loadFinalIngredients(){
    const bookingId = document.getElementById('finalizationOrderSelect').value;
    if(!bookingId){
        document.getElementById('finalizationContent').innerHTML = '';
        return;
    }

    currentBookingId = bookingId;

    try{
        const data = await apiCall(`/admin/api/ingredients/booking/${bookingId}`);
        if(data.success){
            currentIngredients = data.ingredients || [];
            renderFinalIngredients(bookingId, data);
        } else {
            currentIngredients = [];
            renderFinalIngredients(bookingId, {ingredients: [], approved_by_admin: false});
        }
    }catch(e){
        console.error('Error loading final ingredients:', e);
        currentIngredients = [];
        renderFinalIngredients(bookingId, {ingredients: [], approved_by_admin: false});
    }
}

async function generateFinalIngredients(){
    const bookingId = document.getElementById('finalizationOrderSelect').value;
    if(!bookingId){
        alert('Please select a booking');
        return;
    }

    try{
        const response = await apiCall(`/admin/api/ingredients/booking/${bookingId}/generate`, 'POST');
        if(response.success){
            alert('Final ingredients generated successfully!');
            loadFinalIngredients();
        }
    }catch(e){
        if(e.message.includes('already exist')){
            alert('Final ingredients already exist for this booking. Edit them below.');
            loadFinalIngredients();
        } else {
            alert('Error: ' + e.message);
        }
    }
}

function renderFinalIngredients(bookingId, data){
    const container = document.getElementById('finalizationContent');
    const ingredients = data.ingredients || [];
    const approved = data.approved_by_admin;

    const categorizedIngredients = {
        'Vegetables': [],
        'Non-Vegetarian': [],
        'Spices / Masala': [],
        'Dairy': [],
        'Fruit': [],
        'Grain': [],
        'Herbs': [],
        'Beverages': [],
        'Oil and Fats': [],
        'Bakery & Sweets': [],
        'Other': []
    };

    ingredients.forEach((ing, index) => {
        let category = 'Other';
        const name = ing.name.toLowerCase();
        if (['onion', 'tomato', 'potato', 'vegetable', 'ginger', 'garlic', 'mint', 'coriander', 'curry leaves', 'tamarind', 'mixed vegetables', 'carrot', 'beans', 'peas'].some(v => name.includes(v))) {
            category = 'Vegetables';
        } else if (['chicken', 'mutton', 'fish', 'meat', 'egg'].some(nv => name.includes(nv))) {
            category = 'Non-Vegetarian';
        } else if (['spices', 'masala', 'cumin', 'red chili', 'turmeric', 'mustard', 'sambar', 'biryani', 'coriander', 'garam'].some(s => name.includes(s))) {
            category = 'Spices / Masala';
        } else if (['milk', 'cheese', 'yogurt', 'butter', 'cream', 'paneer'].some(d => name.includes(d))) {
            category = 'Dairy';
        } else if (['apple', 'banana', 'orange', 'fruit', 'mango', 'grapes'].some(f => name.includes(f))) {
            category = 'Fruit';
        } else if (['rice', 'wheat', 'flour', 'grain', 'oats', 'barley'].some(g => name.includes(g))) {
            category = 'Grain';
        } else if (['basil', 'oregano', 'thyme', 'rosemary', 'herb'].some(h => name.includes(h))) {
            category = 'Herbs';
        } else if (['tea', 'coffee', 'juice', 'beverage', 'soda'].some(b => name.includes(b))) {
            category = 'Beverages';
        } else if (['oil', 'ghee', 'fat', 'butter', 'lard'].some(o => name.includes(o))) {
            category = 'Oil and Fats';
        } else if (['sugar', 'cake', 'bread', 'cookie', 'sweet', 'bakery'].some(bs => name.includes(bs))) {
            category = 'Bakery & Sweets';
        }
        categorizedIngredients[category].push({...ing, originalIndex: index});
    });

    let html = `
        <div style="background: var(--bg-body); padding: 16px; border-radius: 8px; margin-bottom: 16px;">
            <h3 style="margin-bottom: 8px; font-size: 16px; font-weight: 600;">Booking: ${bookingId}</h3>
            <p style="margin-bottom: 6px; font-size: 13px;"><strong>Status:</strong> <span style="color: ${approved ? 'var(--success)' : 'var(--warning)'}; font-weight: 600;">${approved ? 'Approved' : 'Pending Approval'}</span></p>
            <p style="font-size: 13px;"><strong>Ingredients Count:</strong> ${ingredients.length}</p>
        </div>

        <div style="margin-bottom: 16px;">
            <h4 style="margin-bottom: 12px; font-size: 15px; font-weight: 600;">Step 1: Preview & Finalize Ingredients</h4>
            <div id="ingredientsList" style="max-height: 400px; overflow-y: auto; border: 1px solid var(--border); border-radius: 8px; padding: 12px; background: white;">
    `;

    if(ingredients.length === 0){
        html += '<p class="empty-state">No ingredients found. Click "Generate Final List" to create or add manually below.</p>';
        // Add manual ingredient input UI
        html += `
        <div class="manual-add-row" style="margin: 20px 0; padding: 16px; border: 1px dashed var(--border); border-radius: 8px; background: var(--bg-body);">
            <h5>Add Manual Ingredient</h5>
            <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                <input type="text" id="manualName" placeholder="Ingredient Name" style="flex: 1; min-width: 150px;">
                <input type="number" id="manualQuantity" placeholder="Quantity" step="0.01" style="width: 120px;">
                <select id="manualUnit" style="width: 100px;"></select>
                <script>populateUnitSelect(document.getElementById('manualUnit'));</script>
                <button onclick="addManualIngredient()" class="btn btn-primary" style="padding: 8px 16px;">Add</button>
            </div>
        </div>
        `;
    } else {
        for (const [category, catIngredients] of Object.entries(categorizedIngredients)) {
            if (catIngredients.length === 0) continue;

            const categoryIcon = getCategoryIcon(category);
            html += `<h5 style="margin: 20px 0 12px 0; color: var(--primary); border-bottom: 2px solid var(--border); padding-bottom: 8px; font-size: 16px;">${categoryIcon} ${category}</h5>`;

            catIngredients.forEach((ing) => {
                const checked = ing.checked !== false ? 'checked' : '';
                html += `
                    <div class="ingredient-row">
                        <input type="checkbox" ${checked} onchange="updateIngredientCheck(${ing.originalIndex}, this.checked)" style="width: 18px; height: 18px;">
                        <input type="text" value="${ing.name}" onchange="updateIngredientName(${ing.originalIndex}, this.value)">
                        <input type="number" value="${ing.quantity}" step="0.01" onchange="updateIngredientQuantity(${ing.originalIndex}, this.value)" style="width: 120px;">
                        <select onchange="updateIngredientUnit(${ing.originalIndex}, this.value)" style="width: 100px;" data-unit="${ing.unit}"></select>
                        <button onclick="removeIngredient(${ing.originalIndex})" style="padding: 10px 14px; background: var(--danger); color: white; border: none; border-radius: 8px; cursor: pointer; white-space: nowrap;">Remove</button>
                    </div>
                `;
            });
        }
    }

    html += `
        </div>
    </div>

    <div style="display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap;">
        <button class="btn btn-primary" onclick="addNewIngredientWithUI(this)"><i class="fas fa-plus"></i> Add Ingredient</button>
        <button class="btn btn-primary" onclick="saveFinalIngredientsWithUI(this)"><i class="fas fa-save"></i> Save Changes</button>
        <button class="btn btn-warning" onclick="editIngredientsAgainWithUI(this)"><i class="fas fa-edit"></i> Edit Again</button>
        ${!approved ? `<button class="btn btn-success" onclick="confirmAndSubmitWithUI(this)"><i class="fas fa-check-circle"></i> Confirm & Submit</button>` : ''}
        ${approved ? `<button class="btn btn-primary" onclick="downloadFinalPDFWithUI(this)"><i class="fas fa-download"></i> Download PDF</button>` : ''}
        ${approved ? `<button class="btn btn-info" onclick="sharePDFWithUI(this)"><i class="fas fa-share"></i> Share PDF</button>` : ''}
    </div>
    `;

    container.innerHTML = html;

    // Populate unit selects dynamically
    document.querySelectorAll('select[data-unit]').forEach(select => {
        const unit = select.getAttribute('data-unit');
        populateUnitSelect(select);
        if (unit) select.value = unit;
    });
}

function updateIngredientCheck(index, checked){
    if(currentIngredients[index]) {
        currentIngredients[index].checked = checked;
    }
}

function updateIngredientName(index, name){
    if(currentIngredients[index]) {
        currentIngredients[index].name = name;
    }
}

function updateIngredientQuantity(index, quantity){
    if(currentIngredients[index]) {
        currentIngredients[index].quantity = parseFloat(quantity) || 0;
    }
}

function updateIngredientUnit(index, unit){
    if(currentIngredients[index]) {
        currentIngredients[index].unit = unit;
    }
}

function removeIngredient(index){
    if(confirm('Remove this ingredient?')) {
        currentIngredients.splice(index, 1);
        renderFinalIngredients(currentBookingId, {ingredients: currentIngredients, approved_by_admin: false});
    }
}

function addNewIngredient(){
    currentIngredients.push({
        name: 'New Ingredient',
        quantity: 0,
        unit: 'g',
        checked: true
    });
    renderFinalIngredients(currentBookingId, {ingredients: currentIngredients, approved_by_admin: false});
}

function addManualIngredient(){
    const name = document.getElementById('manualName').value.trim();
    const quantity = parseFloat(document.getElementById('manualQuantity').value) || 0;
    const unit = document.getElementById('manualUnit').value;

    if(!name){
        alert('Please enter an ingredient name');
        return;
    }

    currentIngredients.push({
        name: name,
        quantity: quantity,
        unit: unit,
        checked: true
    });

    // Clear inputs
    document.getElementById('manualName').value = '';
    document.getElementById('manualQuantity').value = '';

    // Re-render the full UI to show the new ingredient
    renderFinalIngredients(currentBookingId, {ingredients: currentIngredients, approved_by_admin: false});
}

function renderIngredientsList(){
    const listContainer = document.getElementById('ingredientsList');
    if(!listContainer) return;

    let html = '';

    if(currentIngredients.length === 0){
        html = '<p class="empty-state">No ingredients found</p>';
    } else {
        currentIngredients.forEach((ing, index) => {
            const checked = ing.checked !== false ? 'checked' : '';
            html += `
                <div class="ingredient-row">
                    <input type="checkbox" ${checked} onchange="updateIngredientCheck(${index}, this.checked)" style="width: 18px; height: 18px;">
                    <input type="text" value="${ing.name}" onchange="updateIngredientName(${index}, this.value)">
                    <input type="number" value="${ing.quantity}" step="0.01" onchange="updateIngredientQuantity(${index}, this.value)" style="width: 120px;">
                    <input type="text" value="${ing.unit}" onchange="updateIngredientUnit(${index}, this.value)" style="width: 80px;">
                    <button onclick="removeIngredient(${index})" style="padding: 10px 14px; background: var(--danger); color: white; border: none; border-radius: 8px; cursor: pointer;">Remove</button>
                </div>
            `;
        });
    }

    listContainer.innerHTML = html;
}

async function saveFinalIngredients(){
    if(!currentBookingId){
        alert('Please select a booking');
        return;
    }

    try{
        const response = await apiCall(`/admin/api/ingredients/booking/${currentBookingId}`, 'PUT', {
            ingredients: currentIngredients
        });
        if(response.success){
            alert('Final ingredients saved successfully!');
            loadFinalIngredients();
        }
    }catch(e){
        alert('Error: ' + e.message);
    }
}

async function editIngredientsAgain(){
    if(!currentBookingId){
        alert('Please select a booking first');
        return;
    }

    try{
        const data = await apiCall(`/admin/api/ingredients/booking/${currentBookingId}`);
        if(data.success){
            currentIngredients = data.ingredients || [];
            renderFinalIngredients(currentBookingId, data);
            alert('Ingredients reloaded for editing. Make your changes and click "Save Changes" when done.');
        } else {
            alert('No saved ingredients found for this booking.');
        }
    }catch(e){
        console.error('Error reloading ingredients:', e);
        alert('Error reloading ingredients: ' + e.message);
    }
}

async function confirmAndSubmit(){
    if(!currentBookingId){
        alert('Please select a booking');
        return;
    }

    if(!confirm('Are you sure you want to confirm and submit these final ingredients? This will approve them and update the order status to "APPROVED".')){
        return;
    }

    try{
        const response = await apiCall(`/admin/api/ingredients/booking/${currentBookingId}/approve`, 'POST');
        if(response.success){
            alert('Final ingredients confirmed and submitted successfully! Order status updated to "APPROVED".');
            loadFinalIngredients();
        }
    }catch(e){
        alert('Error: ' + e.message);
    }
}

async function downloadFinalPDF(){
    if(!currentBookingId){
        alert('Please select a booking');
        return;
    }

    window.open(`/admin/api/ingredients/booking/${currentBookingId}/pdf`, '_blank');
}

/**
 * Enhanced PDF Sharing Function (UPDATED)
 * Replaces the old sharePDF() function
 */
async function sharePDF() {
    // Validate booking ID
    if (!currentBookingId) {
        showCustomAlert('error', 'Please select a booking first');
        return;
    }

    try {
        // ===========================================
        // STEP 1: Send PDF to Gmail automatically
        // ===========================================
        console.log('📧 Sending PDF to admin Gmail...');

        const emailResponse = await fetch(
            `/admin/api/ingredients/booking/${currentBookingId}/send-pdf-email`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin'
            }
        );

        const emailResult = await emailResponse.json();

        if (!emailResponse.ok || !emailResult.success) {
            throw new Error(emailResult.error || 'Failed to send email');
        }

        // ===========================================
        // STEP 2: Show success alert
        // ===========================================
        showCustomAlert('success', 'Sent successfully via Gmail');

        // ===========================================
        // STEP 3: Refresh orders table silently
        // ===========================================
        if (typeof loadOrders === 'function') {
            await loadOrders();
        }

        // ===========================================
        // STEP 4: Show WhatsApp confirmation
        // ===========================================
        const wantsWhatsApp = await showWhatsAppConfirmation();

        if (wantsWhatsApp) {
            // ===========================================
            // STEP 5: Open WhatsApp
            // ===========================================
            await openWhatsAppForSharing(currentBookingId);
        }

    } catch (error) {
        console.error('PDF sharing error:', error);
        showCustomAlert('error', 'Failed to send email. Please try again.');
    }
}

// ============================================
// HELPER FUNCTIONS (ADD THESE)
// ============================================

/**
 * Custom Alert Function
 */
function showCustomAlert(type, message) {
    const existingAlerts = document.querySelectorAll('.custom-alert');
    existingAlerts.forEach(alert => alert.remove());

    const alertDiv = document.createElement('div');
    alertDiv.className = 'custom-alert';

    const bgColor = type === 'success' ? '#10b981' : '#ef4444';
    const icon = type === 'success'
        ? '<i class="fas fa-check-circle"></i>'
        : '<i class="fas fa-exclamation-triangle"></i>';

    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${bgColor};
        color: white;
        padding: 16px 24px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 15px;
        font-weight: 500;
        max-width: 400px;
        animation: slideInRight 0.3s ease-out;
    `;

    alertDiv.innerHTML = `${icon} <span>${message}</span>`;
    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => alertDiv.remove(), 300);
    }, 4000);
}

/**
 * WhatsApp Confirmation Dialog
 */
function showWhatsAppConfirmation() {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.6); display: flex; align-items: center;
            justify-content: center; z-index: 10001; animation: fadeIn 0.2s;
        `;

        const dialog = document.createElement('div');
        dialog.style.cssText = `
            background: white; padding: 32px; border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 450px;
            width: 90%; text-align: center; animation: scaleIn 0.3s;
        `;

        dialog.innerHTML = `
            <div style="font-size: 64px; margin-bottom: 16px;">
                <i class="fab fa-whatsapp" style="color: #25D366;"></i>
            </div>
            <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 22px;">
                Send via WhatsApp?
            </h3>
            <p style="color: #6b7280; margin: 0 0 28px 0; font-size: 15px;">
                Do you want to send this PDF through WhatsApp?
            </p>
            <div style="display: flex; gap: 12px; justify-content: center;">
                <button id="whatsappNo" style="
                    background: #f3f4f6; color: #374151; padding: 12px 28px;
                    border: none; border-radius: 10px; cursor: pointer;
                    font-size: 15px; font-weight: 600; min-width: 100px;
                ">No, Thanks</button>
                <button id="whatsappYes" style="
                    background: #25D366; color: white; padding: 12px 28px;
                    border: none; border-radius: 10px; cursor: pointer;
                    font-size: 15px; font-weight: 600; min-width: 100px;
                "><i class="fab fa-whatsapp"></i> Yes, Send</button>
            </div>
        `;

        overlay.appendChild(dialog);
        document.body.appendChild(overlay);

        const closeDialog = (response) => {
            overlay.style.animation = 'fadeOut 0.2s';
            setTimeout(() => {
                overlay.remove();
                resolve(response);
            }, 200);
        };

        dialog.querySelector('#whatsappYes').onclick = () => closeDialog(true);
        dialog.querySelector('#whatsappNo').onclick = () => closeDialog(false);
        overlay.onclick = (e) => { if (e.target === overlay) closeDialog(false); };
    });
}

/**
 * Opens WhatsApp with PDF link
 */
async function openWhatsAppForSharing(bookingId) {
    try {
        const response = await fetch(`/admin/api/bookings/${bookingId}`);
        const data = await response.json();

        if (!data.success || !data.booking) {
            throw new Error('Failed to fetch booking details');
        }

        const booking = data.booking;
        const phoneNumber = booking.mobile || '';
        const pdfUrl = `${window.location.origin}/admin/api/ingredients/booking/${bookingId}/pdf`;

        const message = encodeURIComponent(
            `Hello ${booking.customer_name},\n\n` +
            `Your order ingredients list is ready!\n\n` +
            `📋 Booking ID: ${bookingId.substring(0, 8)}\n` +
            `📅 Event Date: ${booking.event_date}\n` +
            `👥 Guests: ${booking.guests}\n\n` +
            `📄 Download PDF: ${pdfUrl}\n\n` +
            `Thank you for choosing Chetan Catering Services!`
        );

        const whatsappUrl = phoneNumber
            ? `https://wa.me/${phoneNumber.replace(/\D/g, '')}?text=${message}`
            : `https://wa.me/?text=${message}`;

        window.open(whatsappUrl, '_blank');

    } catch (error) {
        console.error('WhatsApp error:', error);
        showCustomAlert('error', 'Failed to open WhatsApp');
    }
}

// ============================================
// ADD CSS ANIMATIONS (ADD THIS ONCE)
// ============================================

(function addStyles() {
    if (document.getElementById('pdfShareStyles')) return;

    const style = document.createElement('style');
    style.id = 'pdfShareStyles';
    style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
        @keyframes scaleIn {
            from { transform: scale(0.9); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
})();

// Wrapper functions for loading animations
async function saveFinalIngredientsWithUI(btn) {
    setButtonLoading(btn, true);
    try {
        await saveFinalIngredients();
    } finally {
        setButtonLoading(btn, false);
    }
}

async function confirmAndSubmitWithUI(btn) {
    setButtonLoading(btn, true);
    try {
        await confirmAndSubmit();
    } finally {
        setButtonLoading(btn, false);
    }
}

async function downloadFinalPDFWithUI(btn) {
    setButtonLoading(btn, true);
    try {
        await downloadFinalPDF();
    } finally {
        setButtonLoading(btn, false);
    }
}

/**
 * Wrapper with loading state (UPDATED)
 */
async function sharePDFWithUI(btn) {
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

    try {
        await sharePDF();
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
    }
}

async function editIngredientsAgainWithUI(btn) {
    setButtonLoading(btn, true);
    try {
        await editIngredientsAgain();
    } finally {
        setButtonLoading(btn, false);
    }
}

async function addNewIngredientWithUI(btn) {
    setButtonLoading(btn, true);
    try {
        await addNewIngredient();
    } finally {
        setButtonLoading(btn, false);
    }
}

async function generateFinalIngredientsWithUI(btn) {
    setButtonLoading(btn, true);
    try {
        await generateFinalIngredients();
    } finally {
        setButtonLoading(btn, false);
    }
}
