// HTML Elements
const actionBtns = document.querySelectorAll('.action-btn');
const mainModal = document.getElementById('main-modal');

// Helper Functions
function updateModalContent(view, type) {
  const modalFooterBtn = document.getElementById('submitBtn');
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

  modalTitle.textContent = 'Añadir Transacción'
  modalFooterBtn.textContent = btnLabels[type];
}

function toggleModal(view) {
  if (!view) return;

  mainModal.dataset.view = view;
  mainModal.dataset.type = 'income';

  document.querySelector('.modal-title').textContent;

  updateModalContent(view, 'income');
}

// Event Listeners

actionBtns.forEach(btn => {
  btn.addEventListener('click', (e)=> {
    const view = e.currentTarget.dataset.modalAction;
    toggleModal(view);
  });
});
