/**
 * ============================================
 * ENHANCED PDF SHARING FUNCTIONALITY
 * File: js/pdf-share-enhanced.js
 * ============================================
 * 
 * Features:
 * 1. Auto-send PDF to Gmail
 * 2. Success alert
 * 3. WhatsApp confirmation dialog
 * 4. Silent orders table refresh
 * 5. Comprehensive error handling
 */

/**
 * Main PDF Sharing Function
 * Replaces the existing sharePDF() function in finalization.js
 * 
 * @param {HTMLButtonElement} buttonElement - The clicked button (optional)
 */
async function sharePDFEnhanced(buttonElement = null) {
    // Validate booking ID
    if (!currentBookingId) {
        showCustomAlert('error', 'Please select a booking first');
        return;
    }

    // Store original button state
    let originalHTML = '';
    if (buttonElement) {
        originalHTML = buttonElement.innerHTML;
        buttonElement.disabled = true;
        buttonElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    }

    try {
        // ===========================================
        // STEP 1: Send PDF to predefined Gmail address
        // ===========================================
        console.log('📧 Step 1: Sending PDF to admin Gmail...');
        
        const emailResponse = await fetch(
            `/admin/api/ingredients/booking/${currentBookingId}/send-pdf-email`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin' // Include session cookies
            }
        );

        const emailResult = await emailResponse.json();

        // Check for email sending errors
        if (!emailResponse.ok || !emailResult.success) {
            throw new Error(emailResult.error || 'Failed to send email');
        }

        // ===========================================
        // STEP 2: Show success alert for Gmail
        // ===========================================
        console.log('✅ Step 2: Email sent successfully');
        showCustomAlert('success', 'Sent successfully via Gmail');

        // ===========================================
        // STEP 3: Refresh orders table silently (no alert)
        // ===========================================
        console.log('🔄 Step 3: Refreshing orders table...');
        await refreshOrdersTableSilently();

        // ===========================================
        // STEP 4: Show WhatsApp confirmation dialog
        // ===========================================
        console.log('💬 Step 4: Showing WhatsApp confirmation...');
        const wantsWhatsApp = await showWhatsAppConfirmationDialog();

        if (wantsWhatsApp) {
            // ===========================================
            // STEP 5: Open WhatsApp for manual sharing
            // ===========================================
            console.log('📱 Step 5: Opening WhatsApp...');
            await openWhatsAppWithPDFLink(currentBookingId);
        } else {
            console.log('ℹ️ User declined WhatsApp sharing');
        }

    } catch (error) {
        // ===========================================
        // ERROR HANDLING
        // ===========================================
        console.error('❌ PDF sharing error:', error);
        
        // Show user-friendly error message
        showCustomAlert('error', 'Failed to send email. Please try again.');
        
    } finally {
        // ===========================================
        // RESTORE BUTTON STATE
        // ===========================================
        if (buttonElement) {
            buttonElement.disabled = false;
            buttonElement.innerHTML = originalHTML;
        }
    }
}

/**
 * Custom Alert Function
 * Shows styled alerts without using native browser alert()
 * 
 * @param {string} type - 'success' or 'error'
 * @param {string} message - Message to display
 */
function showCustomAlert(type, message) {
    // Remove any existing alerts
    const existingAlerts = document.querySelectorAll('.custom-alert');
    existingAlerts.forEach(alert => alert.remove());

    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = 'custom-alert';
    
    // Style based on type
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
    
    // Add to page
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        alertDiv.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => alertDiv.remove(), 300);
    }, 4000);
}

/**
 * WhatsApp Confirmation Dialog
 * Shows a styled modal asking if user wants to share via WhatsApp
 * 
 * @returns {Promise<boolean>} - True if user clicks Yes, False if No
 */
function showWhatsAppConfirmationDialog() {
    return new Promise((resolve) => {
        // Create overlay
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10001;
            animation: fadeIn 0.2s ease-out;
        `;

        // Create dialog
        const dialog = document.createElement('div');
        dialog.style.cssText = `
            background: white;
            padding: 32px;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 450px;
            width: 90%;
            text-align: center;
            animation: scaleIn 0.3s ease-out;
        `;

        dialog.innerHTML = `
            <div style="font-size: 64px; margin-bottom: 16px;">
                <i class="fab fa-whatsapp" style="color: #25D366;"></i>
            </div>
            <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 22px; font-weight: 600;">
                Send via WhatsApp?
            </h3>
            <p style="color: #6b7280; margin: 0 0 28px 0; font-size: 15px; line-height: 1.6;">
                Do you want to send this PDF through WhatsApp?<br>
                <small style="color: #9ca3af;">You'll be able to share it manually</small>
            </p>
            <div style="display: flex; gap: 12px; justify-content: center;">
                <button id="whatsappNo" style="
                    background: #f3f4f6;
                    color: #374151;
                    padding: 12px 28px;
                    border: none;
                    border-radius: 10px;
                    cursor: pointer;
                    font-size: 15px;
                    font-weight: 600;
                    transition: all 0.2s;
                    min-width: 100px;
                ">
                    No, Thanks
                </button>
                <button id="whatsappYes" style="
                    background: #25D366;
                    color: white;
                    padding: 12px 28px;
                    border: none;
                    border-radius: 10px;
                    cursor: pointer;
                    font-size: 15px;
                    font-weight: 600;
                    transition: all 0.2s;
                    min-width: 100px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    justify-content: center;
                ">
                    <i class="fab fa-whatsapp"></i> Yes, Send
                </button>
            </div>
        `;

        overlay.appendChild(dialog);
        document.body.appendChild(overlay);

        // Add hover effects via event listeners
        const yesBtn = dialog.querySelector('#whatsappYes');
        const noBtn = dialog.querySelector('#whatsappNo');

        yesBtn.addEventListener('mouseenter', () => {
            yesBtn.style.background = '#20ba5a';
            yesBtn.style.transform = 'translateY(-2px)';
            yesBtn.style.boxShadow = '0 4px 12px rgba(37, 211, 102, 0.3)';
        });
        yesBtn.addEventListener('mouseleave', () => {
            yesBtn.style.background = '#25D366';
            yesBtn.style.transform = 'translateY(0)';
            yesBtn.style.boxShadow = 'none';
        });

        noBtn.addEventListener('mouseenter', () => {
            noBtn.style.background = '#e5e7eb';
        });
        noBtn.addEventListener('mouseleave', () => {
            noBtn.style.background = '#f3f4f6';
        });

        // Handle responses
        const closeDialog = (response) => {
            overlay.style.animation = 'fadeOut 0.2s ease-in';
            setTimeout(() => {
                overlay.remove();
                resolve(response);
            }, 200);
        };

        yesBtn.onclick = () => closeDialog(true);
        noBtn.onclick = () => closeDialog(false);
        
        // Close on overlay click
        overlay.onclick = (e) => {
            if (e.target === overlay) closeDialog(false);
        };
    });
}

/**
 * Opens WhatsApp with pre-filled message and PDF link
 * 
 * @param {string} bookingId - The booking ID
 */
async function openWhatsAppWithPDFLink(bookingId) {
    try {
        // Fetch booking details to get customer phone number
        const response = await fetch(`/admin/api/bookings/${bookingId}`);
        const data = await response.json();

        if (!data.success || !data.booking) {
            throw new Error('Failed to fetch booking details');
        }

        const booking = data.booking;
        const phoneNumber = booking.mobile || '';
        
        // Create PDF URL
        const pdfUrl = `${window.location.origin}/admin/api/ingredients/booking/${bookingId}/pdf`;
        
        // Format WhatsApp message
        const message = encodeURIComponent(
            `Hello ${booking.customer_name},\n\n` +
            `Your order ingredients list is ready!\n\n` +
            `📋 Booking ID: ${bookingId.substring(0, 8)}...\n` +
            `📅 Event Date: ${booking.event_date}\n` +
            `⏰ Time Slot: ${booking.time_slot}\n` +
            `👥 Guests: ${booking.guests}\n\n` +
            `📄 Download your PDF here:\n${pdfUrl}\n\n` +
            `Thank you for choosing Chetan Catering Services!\n` +
            `For any queries, please contact us.`
        );

        // Open WhatsApp (web or app)
        const whatsappUrl = phoneNumber 
            ? `https://wa.me/${phoneNumber.replace(/\D/g, '')}?text=${message}`
            : `https://wa.me/?text=${message}`;

        // Open in new tab
        window.open(whatsappUrl, '_blank');
        
        console.log('✅ WhatsApp opened successfully');

    } catch (error) {
        console.error('❌ WhatsApp opening error:', error);
        showCustomAlert('error', 'Failed to open WhatsApp. Please try manually.');
    }
}

/**
 * Silently refreshes the orders table without showing alerts
 * Calls the existing loadOrders() function if available
 */
async function refreshOrdersTableSilently() {
    try {
        // Check if loadOrders function exists (from orders.js)
        if (typeof loadOrders === 'function') {
            await loadOrders();
            console.log('✅ Orders table refreshed successfully');
        } else {
            console.warn('⚠️ loadOrders function not found');
        }
    } catch (error) {
        // Fail silently - don't show error to user
        console.error('❌ Orders table refresh error:', error);
    }
}

/**
 * Add CSS animations
 */
(function addAnimations() {
    if (document.getElementById('pdfShareAnimations')) return;
    
    const style = document.createElement('style');
    style.id = 'pdfShareAnimations';
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
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
            from {
                transform: scale(0.9);
                opacity: 0;
            }
            to {
                transform: scale(1);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
})();

/**
 * Update the existing sharePDF function in finalization.js
 * Replace the old sharePDF() with this wrapper
 */
async function sharePDF() {
    await sharePDFEnhanced(event?.target);
}

/**
 * Alternative: Update sharePDFWithUI to use new function
 */
async function sharePDFWithUI(btn) {
    await sharePDFEnhanced(btn);
}

// Export for global use
window.sharePDFEnhanced = sharePDFEnhanced;
window.showCustomAlert = showCustomAlert;
