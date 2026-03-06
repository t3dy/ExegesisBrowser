document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('entrySearch');
    const cards = document.querySelectorAll('.card');

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            cards.forEach(card => {
                const title = card.getAttribute('data-title').toLowerCase();
                const text = card.querySelector('p').textContent.toLowerCase();

                if (title.includes(query) || text.includes(query)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
});
