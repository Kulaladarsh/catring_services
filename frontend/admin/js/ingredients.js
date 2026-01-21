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
        html += `<h3 style="margin: 24px 0 12px; color: var(--primary);">${getCategoryIcon(cat)} ${cat}</h3>
                 <div class="ingredient-list" style="margin-bottom: 24px; border: 1px solid var(--border); border-radius: 10px; padding: 16px; background: white;">`;
        ingredients.forEach((ing, index) => {
            const checked = ing.checked !== false ? 'checked' : '';
            html += `
                <div class="ingredient-row">
                    <input type="checkbox" ${checked} onchange="updatePlanningIngredientCheck('${cat}', ${index}, this.checked)" style="width: 18px; height: 18px;">
                    <input type="text" value="${ing.name}" onchange="updatePlanningIngredientName('${cat}', ${index}, this.value)">
                    <input type="number" value="${ing.quantity}" step="0.01" onchange="updatePlanningIngredientQuantity('${cat}', ${index}, this.value)">
                    <input type="text" value="${ing.unit}" onchange="updatePlanningIngredientUnit('${cat}', ${index}, this.value)" style="width: 80px;">
                    <button onclick="removePlanningIngredient('${cat}', ${index})" style="padding: 10px 14px; background: var(--danger); color: white; border: none; border-radius: 8px; cursor: pointer;">Remove</button>
                </div>
            `;
        });
        html += '</div>';
    }

    html += '<button class="btn btn-primary" onclick="addNewPlanningIngredient()"><i class="fas fa-plus"></i> Add New Ingredient</button>';
    container.innerHTML = html;
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
