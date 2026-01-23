const filterBtns = document.querySelectorAll('.filter-btn');
const selectTrigger = document.getElementById('selectTriggerF');
const select = document.getElementById('customSelectF');
const selectOptList = document.getElementById('selectOptListF');
const catOpts = document.querySelectorAll('.cat-option');

const filters = ['all', 'income', 'expense'];

// HELPER FUNCTIONS
function handleSelectList(e) {
  if (!selectOptList.contains(e.target)) {
    closeSelect();
  }
}

function closeSelect() {
  select.ariaExpanded = 'false';
  window.removeEventListener('click', handleSelectList);
}

function toggleSelect(e) {
  e.stopPropagation();

  const isOpen = select.ariaExpanded === 'true';

  if (isOpen) {
    closeSelect();
  } else {
    select.ariaExpanded = 'true';
    window.addEventListener('click', handleSelectList);
  }
}

// EVENT LISTENERS
filterBtns.forEach(btn => {
  btn.addEventListener('click', (e)=> {
    const filter = e.currentTarget.dataset.filter;

    const isValid = filters.includes(filter);

    if (!isValid) {
      alert('Filtro inválido');
      window.location.reload();
      return;
    }

    window.location.href = `./history?filter=${filter}`;
  });
});

selectTrigger.addEventListener('click', toggleSelect);

catOpts.forEach(opt => {
  opt.addEventListener('click', (e)=>{
    const cat_id = e.currentTarget.dataset.catId;

    if (!cat_id) {
      window.location.reload();
      return;
    }

    let id = parseInt(cat_id);

    if (isNaN(id)) {
      alert('La categoría es invalida');
      window.location.reload();
      return;
    }

    window.location.href = `./history?cat_id=${id}`;
  })
})