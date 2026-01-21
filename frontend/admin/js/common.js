// Mobile Sidebar Toggle
function toggleMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const body = document.body;

    sidebar.classList.toggle('mobile-open');

    // Prevent body scroll when sidebar is open on mobile
    if (window.innerWidth <= 768) {
        if (sidebar.classList.contains('mobile-open')) {
            body.style.overflow = 'hidden';
            body.style.position = 'fixed';
            body.style.width = '100%';
        } else {
            body.style.overflow = '';
            body.style.position = '';
            body.style.width = '';
        }
    }
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.querySelector('.sidebar-toggle');

    if (window.innerWidth <= 768 &&
        sidebar.classList.contains('mobile-open') &&
        !sidebar.contains(event.target) &&
        !toggle.contains(event.target)) {
        sidebar.classList.remove('mobile-open');
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.body.style.width = '';
    }
});

// Enhanced mobile touch handling
document.addEventListener('touchstart', function(event) {
    // Handle touch events for better mobile interaction
    if (event.touches.length > 1) {
        event.preventDefault(); // Prevent zoom on multi-touch
    }
}, { passive: false });

// Prevent zoom on input focus for iOS
document.addEventListener('focusin', function(event) {
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.tagName === 'SELECT') {
        // Add viewport meta tag dynamically if not present
        let viewport = document.querySelector('meta[name=viewport]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
            document.head.appendChild(viewport);
        }
    }
});

document.addEventListener('focusout', function(event) {
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.tagName === 'SELECT') {
        // Reset viewport after input blur
        setTimeout(() => {
            let viewport = document.querySelector('meta[name=viewport]');
            if (viewport) {
                viewport.content = 'width=device-width, initial-scale=1.0';
            }
        }, 300);
    }
});

// Global constants for units and categories
const AVAILABLE_UNITS = [
    {value: 'g', label: 'g'},
    {value: 'kg', label: 'kg'},
    {value: 'oz', label: 'oz'},
    {value: 'lb', label: 'lb'},
    {value: 'mg', label: 'mg'},
    {value: 'ml', label: 'ml'},
    {value: 'l', label: 'litre'},
    {value: 'cup', label: 'cup'},
    {value: 'tbsp', label: 'tbsp'},
    {value: 'tsp', label: 'tsp'},
    {value: 'pcs', label: 'pcs'},
    {value: 'packet', label: 'packet'},
    {value: 'bunch', label: 'bunch'},
    {value: 'dozen', label: 'dozen'},
    {value: 'slice', label: 'slice'},
    {value: 'can', label: 'can'},
    {value: 'bottle', label: 'bottle'}
];

const AVAILABLE_CATEGORIES = [
    {value: 'Vegetables', label: 'Vegetables'},
    {value: 'Non-Vegetarian', label: 'Non-Vegetarian'},
    {value: 'Spices / Masala', label: 'Spices / Masala'},
    {value: 'Dairy', label: 'Dairy'},
    {value: 'Fruit', label: 'Fruit'},
    {value: 'Dry Fruits', label: 'Dry Fruits'},
    {value: 'Grain', label: 'Grain'},
    {value: 'Herbs', label: 'Herbs'},
    {value: 'Beverages', label: 'Beverages'},
    {value: 'Oil and Fats', label: 'Oil and Fats'},
    {value: 'Bakery & Sweets', label: 'Bakery & Sweets'},
    {value: 'Other', label: 'Other'}
];

// Function to populate unit select
function populateUnitSelect(selectElement) {
    selectElement.innerHTML = '';
    AVAILABLE_UNITS.forEach(unit => {
        const option = document.createElement('option');
        option.value = unit.value;
        option.textContent = unit.label;
        selectElement.appendChild(option);
    });
}

// Function to populate category select
function populateCategorySelect(selectElement) {
    selectElement.innerHTML = '';
    AVAILABLE_CATEGORIES.forEach(category => {
        const option = document.createElement('option');
        option.value = category.value;
        option.textContent = category.label;
        selectElement.appendChild(option);
    });
}

// Global state
let currentIngredients = [];
let currentBookingId = null;
let allOrders = [];
let filteredOrders = [];
let calendarData = [];
let currentFilter = 'all';
let currentPlanningIngredients = {};

// Performance caching
let statsCache = null;
let dishesCache = null;
let ordersCache = null;
let calendarCache = null;
let cacheExpiry = 5 * 60 * 1000; // 5 minutes

// Ingredient database for planning
const allIngredients = [
    {name: "Onions", category: "Vegetables", base_qty: 100, unit: "grams"},
    {name: "Tomatoes", category: "Vegetables", base_qty: 50, unit: "grams"},
    {name: "Potatoes", category: "Vegetables", base_qty: 80, unit: "grams"},
    {name: "Mixed Vegetables", category: "Vegetables", base_qty: 100, unit: "grams"},
    {name: "Ginger-Garlic Paste", category: "Vegetables", base_qty: 10, unit: "grams"},
    {name: "Mint & Coriander", category: "Vegetables", base_qty: 10, unit: "grams"},
    {name: "Coriander Leaves", category: "Vegetables", base_qty: 5, unit: "grams"},
    {name: "Curry Leaves", category: "Vegetables", base_qty: 1, unit: "grams"},
    {name: "Tamarind", category: "Vegetables", base_qty: 10, unit: "grams"},
    {name: "Chicken", category: "Non-Vegetarian", base_qty: 250, unit: "grams"},
    {name: "Mutton", category: "Non-Vegetarian", base_qty: 250, unit: "grams"},
    {name: "Spices (Mix)", category: "Spices", base_qty: 5, unit: "grams"},
    {name: "Biryani Spices", category: "Spices", base_qty: 8, unit: "grams"},
    {name: "Curry Spices", category: "Spices", base_qty: 10, unit: "grams"},
    {name: "Cumin Seeds", category: "Spices", base_qty: 2, unit: "grams"},
    {name: "Red Chili Powder", category: "Spices", base_qty: 30, unit: "grams"},
    {name: "Turmeric Powder", category: "Spices", base_qty: 2, unit: "grams"},
    {name: "Mustard Seeds", category: "Spices", base_qty: 2, unit: "grams"},
    {name: "Sambar Powder", category: "Spices", base_qty: 5, unit: "grams"},
    {name: "Basmati Rice", category: "Other", base_qty: 150, unit: "grams"},
    {name: "Toor Dal", category: "Other", base_qty: 80, unit: "grams"},
    {name: "Dosa Batter", category: "Other", base_qty: 100, unit: "ml"},
    {name: "Idli Batter", category: "Other", base_qty: 100, unit: "ml"},
    {name: "Ghee", category: "Other", base_qty: 15, unit: "ml"},
    {name: "Oil", category: "Other", base_qty: 20, unit: "ml"},
    {name: "Butter", category: "Other", base_qty: 20, unit: "g"},
    {name: "Cream", category: "Other", base_qty: 30, unit: "ml"},
    {name: "Yogurt", category: "Other", base_qty: 50, unit: "grams"},
    {name: "Paneer", category: "Other", base_qty: 100, unit: "grams"}
];

// API Call Helper
async function apiCall(endpoint, method='GET', data=null){
    const config={method, headers:{'Content-Type':'application/json'}};
    if(data) config.body=JSON.stringify(data);
    try {
        const response = await fetch(endpoint, config);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        return response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

function navigateTo(page) {
    window.location.href = '/admin/' + page;
}

// Frontend sanitization function
function sanitizeInput(input) {
    if (typeof input !== 'string') return input;
    return input.trim().replace(/<[^>]*>/g, '').replace(/javascript:/gi, '').replace(/script/gi, '');
}

function logout(){
    if(confirm('Are you sure you want to logout?')){
        window.location.href = '/admin/logout';
    }
}

// Button loading utility
function setButtonLoading(btn, loading) {
    if (loading) {
        btn.classList.add('loading');
    } else {
        btn.classList.remove('loading');
    }
}

// Handle window resize
window.addEventListener('resize', function() {
    if (window.innerWidth > 768) {
        document.getElementById('sidebar').classList.remove('mobile-open');
    }
});
