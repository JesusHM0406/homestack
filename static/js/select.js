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
    const { baseUrl, query } = select.dataset;
    const value = e.currentTarget.dataset.value;

    if (!value) {
      window.location.href = baseUrl;
    } else {
      window.location.href = `${baseUrl}${query}${value}`;
    }
  })
})