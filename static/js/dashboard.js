// ====== HTML Elements ======
const actionBtns = document.querySelectorAll('.action-btn');
const mainModal = document.getElementById('main-modal');
const toggleBtns = document.querySelectorAll('.btn-toggle');
const modalFooterBtn = document.getElementById('submitBtn');
const submitBtn = document.getElementById('submitBtn');
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


// IMPORTANT!: I NEED TO CLEAN THE INPUTS WHEN CLOSING THE MODAL OR SWITCHING BETWEEN INCOMES AND EXPENSES

// I can avoid the problem of the btn an title labels using CSS, but it requires more HTML elements


// Helper Functions
function updateModalContent(view, type) {
  const modalTitle = document.querySelector('.modal-title');

  if (!view || !type) {
    modalFooterBtn.textContent = 'Aceptar';
  }

  const btnLabels = {
    'income': 'Agregar ingreso',
    'expense': 'Agregar gasto'
  };

  if (view === 'categories') {
    modalTitle.textContent = 'Administrar Categorias';
    modalFooterBtn.textContent = 'Aceptar';
    return;
  }

  modalTitle.textContent = 'Añadir Transacción';
  modalFooterBtn.textContent = btnLabels[type];
}

function toggleModal(view) {
  if (!view) return;

  mainModal.dataset.view = view;
  mainModal.dataset.type = 'income';

  document.querySelector('.modal-title').textContent;

  updateModalContent(view, 'income');
  if (view === 'transaction') {
    cleanSelect();
    submitBtn.setAttribute('form', 'transaction-form');
  } else {
    submitBtn.setAttribute('form', 'categories-form');
  }
}

function toggleModalView(type) {
  if (!type) {
    mainModal.dataset.type = 'income';
    return;
  }

  const isIncome = type === 'income';

  mainModal.dataset.type = type;

  if (mainModal.dataset.view === 'transaction') {
    modalFooterBtn.textContent = isIncome ? 'Agregar Ingreso' : 'Agregar Gasto';
    cleanSelect();
  } else {
    const addCategoryLabel = document.getElementById('add-category-label');
    const deleteCategoryLabel = document.getElementById('delete-category-label');
    addCategoryLabel.textContent = isIncome ? 'Ingreso' : 'Gasto';
    deleteCategoryLabel.textContent = addCategoryLabel.textContent; 

    newCategoryInput.setAttribute('placeholder', isIncome ? 'Ej: Alquileres, Comisiones, etc.' : 'Ej: Comida, Renta, etc.');
  }
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

function toggleAnalysis(type) {
  categoryAnalysisContainer.dataset.typeAnalysis = type || 'incomes';
}

// Event Listeners

actionBtns.forEach(btn => {
  btn.addEventListener('click', (e)=> {
    const view = e.currentTarget.dataset.modalAction;
    toggleModal(view);
  });
});

toggleBtns.forEach(btn => {
  btn.addEventListener('click', (e)=> {
    const type = e.currentTarget.dataset.mtype;
    toggleModalView(type);
  });
});

selectTrigger.addEventListener('click', toggleSelect);

selectOptions.forEach(opt => {
  opt.addEventListener('click', handleOptClick);
});

analysisBtns.forEach(btn => {
  btn.addEventListener('click', (e)=> {
    const aType = e.currentTarget.dataset.analysis;
    toggleAnalysis(aType);
  });
});