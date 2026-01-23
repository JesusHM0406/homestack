const filterBtns = document.querySelectorAll('.filter-btn');
const selectTrigger = document.getElementById('selectTriggerF');
const select = document.getElementById('customSelectF');
const selectOptList = document.getElementById('selectOptListF');

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

    window.location.href = `./history?filter=${filter}`;
  });
});

selectTrigger.addEventListener('click', toggleSelect);