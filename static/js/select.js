const selectTrigger = document.getElementById('selTrigg');
const select = document.getElementById('customSelect');
const selectOptList = document.getElementById('selOptList');
const catOpts = document.querySelectorAll('.cust-sel-opt');

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
selectTrigger.addEventListener('click', toggleSelect);

catOpts.forEach(opt => {
  opt.addEventListener('click', (e)=>{
    const dateVal = e.currentTarget.dataset.date;

    if (!dateVal) {
      window.location.href = "./reports";
      return;
    }

    let date = new Date(dateVal);

    if (date.toISOString() === 'Invalid Date') {
      alert('La fecha es inválida');
      window.location.href = "./reports";
      return;
    }

    window.location.href = `./reports?date=${dateVal}`;
  })
})