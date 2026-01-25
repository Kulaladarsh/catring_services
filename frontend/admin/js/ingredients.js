// Ingredient Planning
function generateIngredientList(){
    const guests = parseInt(document.getElementById('guestCount').value);
    if(!guests || guests < 1){
        alert('Please enter a valid number of guests');
        return;
    }

    currentPlanningIngredients = {};
    allIngredients.forEach(ing => {
        const calculatedQty = ing.base_qty * guests;
        const item = {
            name: ing.name,
            quantity: calculatedQty,
            unit: ing.unit,
            checked: true
        };
        if(!currentPlanningIngredients[ing.category]){
            currentPlanningIngredients[ing.category] = [];
        }
        currentPlanningIngredients[ing.category].push(item);
    });

    renderIngredientsPlanning();
}

function getCategoryIcon(cat){
    if(cat === 'Vegetables') return '🥬';
    if(cat === 'Non-Vegetarian') return '🍗';
    if(cat === 'Spices') return '🌶️';
    if(cat === 'Dairy') return '🥛';
    if(cat === 'Fruit') return '🍎';
    if(cat === 'Grain') return '🌾';
    if(cat === 'Herbs') return '🌿';
    if(cat === 'Beverages') return '🥤';
    if(cat === 'Oil and Fats') return '🫒';
    if(cat === 'Bakery & Sweets') return '🍰';
    return '🧂';
}

function renderIngredientsPlanning(){
    const container = document.getElementById('ingredientsPlanning');
    let html = '';

    for(const [cat, ingredients] of Object.entries(currentPlanningIngredients)){
        const categoryIcon = getCategoryIcon(cat);
        const ingredientCount = ingredients.length;

        html += `
            <div class="category-section" id="category-${cat.replace(/\s+/g, '-').toLowerCase()}">
                <div class="category-header" onclick="toggleCategory('${cat}')">
                    <div class="category-info">
                        <div class="category-icon">${categoryIcon}</div>
                        <div class="category-details">
                            <h3>${cat}</h3>
                            <div class="category-count">${ingredientCount} item${ingredientCount !== 1 ? 's' : ''}</div>
                        </div>
                    </div>
                    <div class="category-toggle">
                        <i class="fas fa-chevron-down"></i>
                    </div>
                </div>
                <div class="category-content">
                    <div class="ingredients-grid">
        `;

        ingredients.forEach((ing, index) => {
            const checked = ing.checked !== false ? 'checked' : '';
            html += `
                <div class="ingredient-card">
                    <div class="ingredient-header">
                        <input type="checkbox" class="ingredient-checkbox" ${checked} onchange="updatePlanningIngredientCheck('${cat}', ${index}, this.checked)">
                        <h4 class="ingredient-name">${ing.name}</h4>
                    </div>
                    <div class="ingredient-form">
                        <input type="number" class="ingredient-input ingredient-quantity" value="${ing.quantity}" step="0.01" onchange="updatePlanningIngredientQuantity('${cat}', ${index}, this.value)" placeholder="Quantity">
                        <input type="text" class="ingredient-input ingredient-unit" value="${ing.unit}" onchange="updatePlanningIngredientUnit('${cat}', ${index}, this.value)" placeholder="Unit">
                    </div>
                    <div class="ingredient-actions">
                        <button class="ingredient-btn remove" onclick="removePlanningIngredient('${cat}', ${index})">
                            <i class="fas fa-trash"></i>
                            Remove
                        </button>
                    </div>
                </div>
            `;
        });

        html += `
                    </div>
                </div>
            </div>
        `;
    }

    html += `
        <button class="add-ingredient-btn" onclick="addNewPlanningIngredient()">
            <i class="fas fa-plus"></i>
            <span>Add New Ingredient</span>
        </button>
    `;

    container.innerHTML = html;
}

function toggleCategory(category) {
    const categorySection = document.getElementById(`category-${category.replace(/\s+/g, '-').toLowerCase()}`);
    if (categorySection) {
        categorySection.classList.toggle('collapsed');
    }
}

function updatePlanningIngredientCheck(cat, index, checked){
    if(currentPlanningIngredients[cat] && currentPlanningIngredients[cat][index]){
        currentPlanningIngredients[cat][index].checked = checked;
    }
}

function updatePlanningIngredientName(cat, index, name){
    if(currentPlanningIngredients[cat] && currentPlanningIngredients[cat][index]){
        currentPlanningIngredients[cat][index].name = name;
    }
}

function updatePlanningIngredientQuantity(cat, index, quantity){
    if(currentPlanningIngredients[cat] && currentPlanningIngredients[cat][index]){
        currentPlanningIngredients[cat][index].quantity = parseFloat(quantity) || 0;
    }
}

function updatePlanningIngredientUnit(cat, index, unit){
    if(currentPlanningIngredients[cat] && currentPlanningIngredients[cat][index]){
        currentPlanningIngredients[cat][index].unit = unit;
    }
}

function removePlanningIngredient(cat, index){
    if(confirm('Remove this ingredient?') && currentPlanningIngredients[cat]){
        currentPlanningIngredients[cat].splice(index, 1);
        renderIngredientsPlanning();
    }
}

function addNewPlanningIngredient(){
    const name = prompt('Ingredient name:');
    if(!name) return;
    const category = prompt('Category (Vegetables, Non-Vegetarian, Spices, Other):') || 'Other';
    const qty = parseFloat(prompt('Quantity:')) || 0;
    const unit = prompt('Unit:') || 'g';

    if(!currentPlanningIngredients[category]){
        currentPlanningIngredients[category] = [];
    }
    currentPlanningIngredients[category].push({
        name, quantity: qty, unit, checked: true
    });
    renderIngredientsPlanning();
}

// Wrapper functions for loading animations
async function generateIngredientListWithUI(btn) {
    setButtonLoading(btn, true);
    try {
        await generateIngredientList();
    } finally {
        setButtonLoading(btn, false);
    }
}

async function addNewPlanningIngredientWithUI(btn) {
    setButtonLoading(btn, true);
    try {
        await addNewPlanningIngredient();
    } finally {
        setButtonLoading(btn, false);
    }
}
