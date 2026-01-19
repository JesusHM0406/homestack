// ====== HTML Elements ======
// ==== Modal Section ====
const actionBtns = document.querySelectorAll('.action-btn');
const mainModal = document.getElementById('main-modal');
const toggleBtns = document.querySelectorAll('.btn-toggle');
const submitBtn = document.getElementById('submitBtn');
const modalTitle = document.querySelector('.modal-title');
// == Categories Form Elements ==
const newCategoryInput = document.getElementById('new_category_input');
// == Transaction Form Elements ==
const categoryInp = document.getElementById('categoryInput');
const customSelect = document.getElementById('customSelect');
const selectTrigger = document.getElementById('selectTrigger');
const selectOptList = document.getElementById('selectOptList');
const selectOptions = document.querySelectorAll('.select-option');
const selectLabel = document.getElementById('selectOptSelected');
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

// IMPORTANT!: I NEED TO CLEAN THE INPUTS WHEN CLOSING THE MODAL OR SWITCHING BETWEEN INCOMES AND EXPENSES

// I can avoid the problem of the btn an title labels using CSS, but it requires more HTML elements


// Helper Functions
function updateModal() {
  const view = mainModal.dataset.view;
  const type = mainModal.dataset.type;

  const config = UI_LABELS[type];

  const isTransaction = view === 'transaction';
  
  if (isTransaction) {
    // Update title
    modalTitle.textContent = 'Añadir Transacción';

    // Update body
    // Nothing to update

    // Update footer
    submitBtn.textContent = config.btn;
    submitBtn.setAttribute('form', 'transaction-form');
  } else {
    // Update title
    modalTitle.textContent = 'Administrar Categorias';

    // Update body
    newCategoryInput.placeholder = config.placeholder;
    document.getElementById('add-category-label').textContent = config.label;
    document.getElementById('delete-category-label').textContent = config.label;

    // Update footer
    submitBtn.textContent = 'Aceptar';
    submitBtn.setAttribute('form', 'categories-form');
  }

  // Clear forms
  clearForm();
}

function clearForm() {
  document.getElementById('categories-form').reset()
  document.getElementById('transaction-form').reset()
  cleanSelect();
}

function cleanSelect() {
  selectLabel.textContent = 'Selecciona una categoria';
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

  selectLabel.textContent = opt.textContent;
  closeSelect();
}

// Event Listeners

actionBtns.forEach(btn => {
  btn.addEventListener('click', (e)=> {
    const view = e.currentTarget.dataset.modalAction;
    mainModal.dataset.view = view;
    mainModal.dataset.type = 'income'; // Default value
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

selectOptions.forEach(opt => {
  // IMPORTANT: WHEN CLICKING ON AN OPTION DELETE "text-secondary" CLASS FROM SELECT TRIGGER LABEL
  opt.addEventListener('click', handleOptClick);
});

analysisBtns.forEach(btn => {
  btn.addEventListener('click', (e)=> {
    const aType = e.currentTarget.dataset.analysis;
    categoryAnalysisContainer.dataset.typeAnalysis = aType || 'income';
  });
});