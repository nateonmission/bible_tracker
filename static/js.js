// ─── Tab Switching ────────────────────────────────────────────
const tabLinks   = document.querySelectorAll('.tab-link');
const sections   = document.querySelectorAll('.tab-content > section');

function activateTab(targetId) {
    sections.forEach(sec => {
        sec.hidden = sec.id !== targetId;
    });
    tabLinks.forEach(link => {
        link.classList.toggle('active', link.getAttribute('href') === '#' + targetId);
    });
}

tabLinks.forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        const targetId = link.getAttribute('href').slice(1); // strip '#'
        activateTab(targetId);
        history.replaceState(null, '', '#' + targetId);
    });
});

// Restore tab from URL hash on load (e.g. bookmarked or refreshed)
const initialHash = location.hash.slice(1);
const validIds    = Array.from(sections).map(s => s.id);
activateTab(validIds.includes(initialHash) ? initialHash : 'dashboard');
