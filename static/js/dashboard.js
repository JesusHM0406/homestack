// HTML Elements
const actionBtns = document.querySelectorAll('.action-btn');
const mainModal = document.getElementById('main-modal');
const toggleBtns = document.querySelectorAll('.btn-toggle');
const modalFooterBtn = document.getElementById('submitBtn');
const newCategoryInput = document.getElementById('new_category_input');

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
}

function toggleModalView(type) {
  if (!type) {
    mainModal.dataset.type = 'income';
    return;
  }

  const isIncome = type == 'income';

  mainModal.dataset.type = type;

  if (mainModal.dataset.view === 'transaction') {
    modalFooterBtn.textContent = isIncome ? 'Agregar Ingreso' : 'Agregar Gasto';
    return;
  }

  const addCategoryLabel = document.getElementById('add-category-label');
  addCategoryLabel.textContent = isIncome ? 'Agregar Nueva Categoria de Ingreso' : 'Agregar Nueva Categoria de Gasto';

  newCategoryInput.setAttribute('placeholder', isIncome ? 'Ej: Alquileres, Comisiones, etc.' : 'Ej: Comida, Renta, etc.')
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
    toggleModalView(type)
  })
})