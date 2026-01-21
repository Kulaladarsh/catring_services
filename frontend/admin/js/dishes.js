// Ingredient management for dish form
let dishIngredients = [];

function addIngredientRow(){
    const container = document.getElementById('ingredientsContainer');
    const rowDiv = document.createElement('div');
    rowDiv.className = 'ingredient-row';

    rowDiv.innerHTML = `
        <input type="text" placeholder="Ingredient name" class="ing-name">
        <input type="number" placeholder="Qty for 10 persons" step="0.01" min="0" class="ing-qty">
        <select class="ing-unit">
            <option value="g">g</option>
            <option value="kg">kg</option>
            <option value="oz">oz</option>
            <option value="lb">lb</option>
            <option value="ml">ml</option>
            <option value="l">litre</option>
            <option value="cup">cup</option>
            <option value="tbsp">tbsp</option>
            <option value="tsp">tsp</option>
            <option value="pcs">pcs</option>
            <option value="packet">packet</option>
            <option value="bunch">bunch</option>
            <option value="dozen">dozen</option>
            <option value="slice">slice</option>
            <option value="can">can</option>
            <option value="bottle">bottle</option>
        </select>
        <select class="ing-category">
            <option value="Vegetables">Vegetables</option>
            <option value="Non-Vegetarian">Non-Vegetarian</option>
            <option value="Spices / Masala">Spices / Masala</option>
            <option value="Dairy">Dairy</option>
            <option value="Fruit">Fruit</option>
            <option value="Dry Fruits">Dry Fruits</option>
            <option value="Grain">Grain</option>
            <option value="Herbs">Herbs</option>
            <option value="Beverages">Beverages</option>
            <option value="Oil and Fats">Oil and Fats</option>
            <option value="Bakery & Sweets">Bakery & Sweets</option>
            <option value="Other">Other</option>
        </select>
        <button onclick="removeIngredientRow(this)" style="padding: 10px 14px; background: var(--danger); color: white; border: none; border-radius: 8px; cursor: pointer; white-space: nowrap;">Remove</button>
    `;

    container.appendChild(rowDiv);
}

function removeIngredientRow(button){
    button.parentElement.remove();
}

function clearAllIngredients(){
    if(confirm('Clear all ingredients?')){
        document.getElementById('ingredientsContainer').innerHTML = '';
        dishIngredients = [];
    }
}

function collectDishIngredients(){
    const rows = document.querySelectorAll('.ingredient-row');
    const ingredients = [];

    rows.forEach(row => {
        const name = row.querySelector('.ing-name').value.trim();
        const qty = parseFloat(row.querySelector('.ing-qty').value);
        const unit = row.querySelector('.ing-unit').value;
        const category = row.querySelector('.ing-category').value;

        if(name && qty > 0){
            ingredients.push({
                name: name,
                per_plate: qty,
                unit: unit,
                category: category
            });
        }
    });

    return ingredients;
}

async function addDish(){
    const name = sanitizeInput(document.getElementById('dishName').value);
    const category = document.getElementById('dishCategory').value;
    const price = parseFloat(document.getElementById('dishPrice').value);
    const imageUrl = sanitizeInput(document.getElementById('dishImageUrl').value);
    const description = sanitizeInput(document.getElementById('dishDescription').value);
    const available = document.getElementById('dishAvailable').checked;
    const ingredients = collectDishIngredients();

    if(!name || !price || price <= 0){
        alert('Please enter valid dish name and price');
        return;
    }

    try{
        const response = await apiCall('/admin/api/dishes', 'POST', {
            name, category, price, image_url: imageUrl, description, available, ingredients
        });

        if(response.message || response.success){
            alert('Dish added successfully!');
            document.getElementById('dishName').value = '';
            document.getElementById('dishPrice').value = '';
            document.getElementById('dishImageUrl').value = '';
            document.getElementById('dishDescription').value = '';
            document.getElementById('dishAvailable').checked = true;
            clearAllIngredients();
            loadDishes();
            // loadStats() - not needed on manage-dishes page
        }
    }catch(e){
        alert('Error adding dish: ' + e.message);
    }
}

async function deleteDish(dishId){
    if(!confirm('Are you sure you want to delete this dish?')) return;

    try{
        const response = await apiCall(`/admin/api/dishes/${dishId}`, 'DELETE');
        if(response.message || response.success){
            alert('Dish deleted successfully!');
            loadDishes();
            // loadStats() - not needed on manage-dishes page
        }
    }catch(e){
        alert('Error deleting dish: ' + e.message);
    }
}

async function updateDishAvailability(dishId, available){
    try{
        await apiCall(`/admin/api/dishes/${dishId}`, 'PUT', { available });
        loadStats();
    }catch(e){
        console.error('Error updating dish availability:', e);
        alert('Error updating dish availability');
    }
}

async function loadDishes(){
    const now = Date.now();
    if(dishesCache && (now - dishesCache.timestamp) < cacheExpiry){
        const dishes = dishesCache.data;
        renderDishes(dishes);
        const categories = [...new Set(dishes.map(d => d.category).filter(Boolean))];
        const filterSelect = document.getElementById('filterCategory');
        filterSelect.innerHTML = '<option value="">All</option>';
        categories.forEach(cat => {
            filterSelect.innerHTML += `<option value="${cat}">${cat}</option>`;
        });
        return;
    }

    try{
        const dishes = await apiCall('/admin/api/dishes');
        if(Array.isArray(dishes)){
            dishesCache = { data: dishes, timestamp: now };
            renderDishes(dishes);
            const categories = [...new Set(dishes.map(d => d.category).filter(Boolean))];
            const filterSelect = document.getElementById('filterCategory');
            filterSelect.innerHTML = '<option value="">All</option>';
            categories.forEach(cat => {
                filterSelect.innerHTML += `<option value="${cat}">${cat}</option>`;
            });
        }
    }catch(e){
        console.error('Error loading dishes:', e);
    }
}

function renderDishes(dishes){
    const grid = document.getElementById('dishesGrid');
    grid.innerHTML = "";

    if (!dishes || dishes.length === 0) {
        grid.innerHTML = '<p style="text-align: center; color: var(--text-muted); grid-column: 1/-1; padding: 40px;">No dishes found</p>';
        return;
    }

    dishes.forEach(d => {
        const dishId = d._id || d.id;
        const available = d.is_active !== false && d.available !== false;
        grid.innerHTML += `
            <div class="dish-card">
                <img class="dish-img" src="${d.image_url || 'https://via.placeholder.com/300x200?text=No+Image'}" alt="${d.name}">
                <div class="dish-info">
                    <div class="dish-cat">${d.category || 'General'}</div>
                    <h3 style="margin-bottom:10px">${d.name}</h3>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top: 12px;">
                        <span class="dish-price">₹${d.price}</span>
                        <div style="display:flex; gap:12px; align-items:center">
                            <input type="checkbox" ${available?'checked':''} onchange="updateDishAvailability('${dishId}', this.checked)" style="width: 18px; height: 18px; cursor: pointer;">
                            <i class="fas fa-trash" onclick="deleteDish('${dishId}')" style="color:var(--danger); cursor:pointer; font-size: 16px;"></i>
                        </div>
                    </div>
                </div>
            </div>`;
    });
}

function filterDishes(){
    const search = document.getElementById('filterSearch').value.toLowerCase();
    const category = document.getElementById('filterCategory').value;
    const cards = document.querySelectorAll('.dish-card');

    cards.forEach(card => {
        const name = card.querySelector('h3').textContent.toLowerCase();
        const cat = card.querySelector('.dish-cat').textContent;
        const matchesSearch = name.includes(search);
        const matchesCategory = !category || cat === category;
        card.style.display = matchesSearch && matchesCategory ? 'block' : 'none';
    });
}

async function loadCategories() {
    const res = await fetch('/api/dishes/categories');
    const categories = await res.json();

    const select = document.getElementById('dishCategory');
    const filter = document.getElementById('filterCategory');

    select.innerHTML = '';
    filter.innerHTML = '<option value="">All</option>';

    categories.forEach(cat => {
        select.innerHTML += `<option value="${cat.name}">${cat.name}</option>`;
        filter.innerHTML += `<option value="${cat.name}">${cat.name}</option>`;
    });
}

async function addCategory() {
    const name = document.getElementById('newCategory').value;
    if (!name) return alert("Enter category");

    await fetch('/api/dishes/categories', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name})
    });

    document.getElementById('newCategory').value = '';
    loadCategories();
}

// Wrapper functions for loading animations
async function addDishWithUI(btn) {
    setButtonLoading(btn, true);
    try {
        await addDish();
    } finally {
        setButtonLoading(btn, false);
    }
}

async function addCategoryWithUI(btn) {
    setButtonLoading(btn, true);
    try {
        await addCategory();
    } finally {
        setButtonLoading(btn, false);
    }
}
