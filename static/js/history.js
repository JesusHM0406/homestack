const filterBtns = document.querySelectorAll('.filter-btn');

filterBtns.forEach(btn => {
  btn.addEventListener('click', (e)=> {
    const filter = e.currentTarget.dataset.filter;

    window.location.href = `./history?filter=${filter}`;
  })
})