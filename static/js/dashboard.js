// ====== HTML Elements ======
// ==== Modal Section ====
const actionBtns = document.querySelectorAll('.action-btn');
const mainModal = document.getElementById('main-modal');
const toggleBtns = document.querySelectorAll('.btn-toggle');
const submitBtn = document.getElementById('submitBtn');
const modalTitle = document.querySelector('.modal-title');
// == Categories Form Elements ==
const categoriesForm = document.getElementById('categories-form');
const categoriesTypeInpt = document.getElementById('categoriesType');
const newCategoryInput = document.getElementById('new_category_input');
const addNewCategoryBtn = document.getElementById('addNewCategoryBtn');
const addedCategoriesInpt = document.getElementById('addedCategories');
const deletedCategoriesInpt = document.getElementById('deletedCategories');
const deleteCategoryBtns = document.querySelectorAll('.delete-category-btn');
const dateInpt = document.getElementById('date');
let addedCategories = [];
let deletedCategories = [];
const categoryFormItems = document.querySelectorAll('.category-form-item');
// == Transaction Form Elements ==
const transactionForm = document.getElementById('transaction-form');
const transactionTypeInpt = document.getElementById('transactionType');
const categoryInp = document.getElementById('categoryInput');
const customSelect = document.getElementById('customSelect');
const selectTrigger = document.getElementById('selectTrigger');
const selectOptList = document.getElementById('selectOptList');
const selectOptions = document.querySelectorAll('.select-option');
const selectLabel = document.getElementById('selectOptSelected');
const conceptInpt = document.getElementById('concept');
const amountInpt = document.getElementById('amount');
// == Analysis Section Elments
const analysisBtns = document.querySelectorAll('.analysis-btn');
const categoryAnalysisContainer = document.getElementById('categoryAnalysis');


// ====== LABELS DICTIONARY ======
const UI_LABELS = {
  income: {
    btn: 'Agregar Ingreso',
    placeholder: 'Ej: Alquileres, Comisiones, etc.',
    label: 'Ingreso'
  },
  expense: {
    btn: 'Agregar Gasto',
    placeholder: 'Ej: Comida, Renta, etc.',
    label: 'Gasto'
  }
};

// ====== HELPER FUNCTIONS ======
function updateModal() {
  const view = mainModal.dataset.view;
  const type = mainModal.dataset.type;

  const config = UI_LABELS[type];

  const isTransaction = view === 'transaction';
  
  if (isTransaction) {
    // Update title
    modalTitle.textContent = 'Añadir Transacción';

    // Update body
    transactionTypeInpt.value = type;

    // Update footer
    submitBtn.textContent = config.btn;
    selectLabel.classList.add('text-secondary');
    submitBtn.setAttribute('form', 'transaction-form');
  } else {
    // Update title
    modalTitle.textContent = 'Administrar Categorias';

    // Update body
    addedCategories = [];
    newCategoryInput.placeholder = config.placeholder;
    document.getElementById('add-category-label').textContent = config.label;
    document.getElementById('delete-category-label').textContent = config.label;
    categoriesTypeInpt.value = type;

    // Update footer
    submitBtn.textContent = 'Aceptar';
    submitBtn.setAttribute('form', 'categories-form');
  }

  // Clear forms
  clearForms();
}

function clearForms() {
  document.getElementById('categories-form').reset()
  document.getElementById('transaction-form').reset()
  cleanSelect();
}

function cleanSelect() {
  selectLabel.textContent = 'Selecciona una categoría';
  selectOptions.forEach(opt => {
    opt.ariaSelected = 'false';
  });
  categoryInp.value = '';
}

function handleSelectList(e) {
  if (!selectOptList.contains(e.target)) {
    closeSelect();
  }
}

function closeSelect() {
  customSelect.ariaExpanded = 'false';
  window.removeEventListener('click', handleSelectList);
}

function toggleSelect(e) {
  e.stopPropagation();

  const isOpen = customSelect.ariaExpanded === 'true';

  if (isOpen) {
    closeSelect();
  } else {
    customSelect.ariaExpanded = 'true';
    window.addEventListener('click', handleSelectList);
  }
}

function handleOptClick(e) {
  selectOptions.forEach(opt => {
    opt.ariaSelected = 'false';
  })

  const opt = e.currentTarget;

  opt.ariaSelected = 'true';

  categoryInp.value = opt.dataset.idv;

  selectLabel.classList.remove('text-secondary');
  selectLabel.textContent = opt.textContent;
  closeSelect();
}

// Categories section

function addNewCategory(name) {
  if (name.trim() === '' || typeof name !== 'string') {
    // Just for the moment
    alert('Por favor ingresa un nombre válido para la nueva categoría.');
    return;
  }

  if (addedCategories.includes(name)) {
    alert('Ya agregaste una categoría con el mismo nombre');
    return
  }

  addedCategories.push(name);
  newCategoryInput.value = '';
}

function deleteCategory(id) {
  const parsedId = parseInt(id);
  if (!parsedId || isNaN(parsedId) || deletedCategories.includes(parsedId)) {
    alert('Ocurrió un error, intenta de nuevo');
    return;
  }

  document.querySelector(`[data-category-id="${id}"]`).closest('.category-form-item').setAttribute('data-hidden', 'true');
  deletedCategories.push(parsedId);
}

// FORM VALIDATION SECTION
function handleCategoriesForm(e) {
  e.preventDefault();

  const type = categoriesTypeInpt.value;

  if (type.trim() === '' ){
    alert("Datos inválidos. Reiniciando formulario...")
    categoriesForm.reset();
    return;
  }

  if (addedCategories.length > 0 || deletedCategories.length > 0) {
    addedCategoriesInpt.value = JSON.stringify(addedCategories);
    deletedCategoriesInpt.value = JSON.stringify(deletedCategories);
    categoriesForm.submit();
  } else {
    alert('No se han realizado cambios en las categorias');
  }
}

function handleTransactionForm(e) {
  e.preventDefault();

  const type = transactionTypeInpt.value;
  const cateId = parseInt(categoryInp.value);
  const desc = conceptInpt.value;
  const amount = parseFloat(amountInpt.value);
  const date = new Date(dateInpt.value);

  if (type.trim() === '') {
    alert('El tipo de transacción es obligatoria');
    mainModal.dataset.type = 'income';
    transactionTypeInpt.value = 'income';
    cleanSelect();
    return;
  }

  if (conceptInpt.getAttribute('type') !== 'text') {
    alert('Datos inválidos. Reiniciando formulario...');
    conceptInpt.setAttribute('type', 'text');
    return;
  }

  if (desc.trim() === '') {
    alert('Descripción vacía');
    return;
  }

  if (isNaN(cateId) || cateId <= 0) {
    alert('Seleccione una categoría válida');
    return;
  }

  if (isNaN(amount) || amount < 0.50) {
    alert('El monto debe de ser un número superior o igual a 0.50');
    return;
  }

  if (!date || date.toString() === 'Invalid Date' || dateInpt.getAttribute('type') != 'date') {
    alert('Fecha inválida');
    dateInpt.setAttribute('type', 'date');
    return;
  }

  transactionForm.submit();
}

// ====== EVENT LISTENERS ======

mainModal.addEventListener('hidden.bs.modal', ()=> {
  clearForms();
  deletedCategories = [];
  categoryFormItems.forEach(elem => {
    elem.removeAttribute('data-hidden');
  })
});

actionBtns.forEach(btn => {
  btn.addEventListener('click', (e)=> {
    const view = e.currentTarget.dataset.modalAction;
    mainModal.dataset.view = view;
    mainModal.dataset.type = 'income'; // Default value
    mainModal.iner
    updateModal();
  });
});

toggleBtns.forEach(btn => {
  btn.addEventListener('click', (e)=> {
    const type = e.currentTarget.dataset.mtype;
    mainModal.dataset.type = type;
    updateModal();
  });
});

selectTrigger.addEventListener('click', toggleSelect);

customSelect.addEventListener('keydown', (e)=>{
  if (e.key === 'Enter' || e.key === ' ') {
    toggleSelect(e)
  }
})

selectOptions.forEach(opt => {
  opt.addEventListener('click', handleOptClick);
});

analysisBtns.forEach(btn => {
  btn.addEventListener('click', (e)=> {
    const aType = e.currentTarget.dataset.analysis;
    categoryAnalysisContainer.dataset.typeAnalysis = aType || 'income';
  });
});

addNewCategoryBtn.addEventListener('click', ()=> {
  const cateName = newCategoryInput.value;
  addNewCategory(cateName);
});

deleteCategoryBtns.forEach(btn => {
  btn.addEventListener('click', (e)=> {
    const categoryId = e.currentTarget.dataset.categoryId;
    deleteCategory(categoryId);
  });
});

categoriesForm.addEventListener('submit', handleCategoriesForm);
transactionForm.addEventListener('submit', handleTransactionForm);