const filterBtns = document.querySelectorAll('.filter-btn');
const selectTrigger = document.getElementById('selectTriggerF');
const select = document.getElementById('customSelectF'); 

// HELPER FUNCTIONS
function toggleSelect(e) {
  const isExpanded = select.ariaExpanded === 'true';

  if (isExpanded) {
    select.ariaExpanded = 'false';
    return;
  }

  select.ariaExpanded = 'true';
}

// EVENT LISTENERS
filterBtns.forEach(btn => {
  btn.addEventListener('click', (e)=> {
    const filter = e.currentTarget.dataset.filter;

    window.location.href = `./history?filter=${filter}`;
  });
});

selectTrigger.addEventListener('click', toggleSelect);