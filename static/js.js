// ─── Helpers ──────────────────────────────────────────────────
function todayLocal() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function getSettings() {
    try {
        return JSON.parse(localStorage.getItem('bibleTrackerSettings') || '{}');
    } catch { return {}; }
}

// ─── Tab Switching ────────────────────────────────────────────
const tabLinks = document.querySelectorAll('.tab-link');
const sections = document.querySelectorAll('.tab-content > section');

function activateTab(targetId) {
    sections.forEach(sec => {
        sec.hidden = sec.id !== targetId;
    });
    tabLinks.forEach(link => {
        link.classList.toggle('active', link.getAttribute('href') === '#' + targetId);
    });

    if (targetId === 'reading-history') loadReadings();
}

tabLinks.forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        const targetId = link.getAttribute('href').slice(1);
        activateTab(targetId);
        history.replaceState(null, '', '#' + targetId);
    });
});

// Restore tab from URL hash on load
const initialHash = location.hash.slice(1);
const validIds    = Array.from(sections).map(s => s.id);
activateTab(validIds.includes(initialHash) ? initialHash : 'dashboard');


// ─── Per-Chapter Verse Counts (Protestant Canon) ──────────────
const VERSE_COUNTS = {
  "Genesis":          [31,25,24,26,32,22,24,22,29,32,32,20,18,24,21,16,27,33,38,18,34,24,20,67,34,35,46,22,35,43,55,32,20,31,29,43,36,30,23,23,57,38,34,34,28,34,31,22,33,26],
  "Exodus":           [22,25,22,24,44,23,25,59,35,29,10,51,22,31,27,36,16,27,25,26,36,31,33,18,40,37,21,43,46,38,18,35,23,35,35,38,29,31,43,38],
  "Leviticus":        [17,16,17,35,19,30,38,36,24,20,47,8,59,57,33,34,16,30,24,46,24,13,44,23,55,46,34],
  "Numbers":          [54,34,51,49,31,27,89,26,23,36,35,16,33,45,41,50,13,32,22,29,35,41,30,25,18,65,23,31,40,16,54,42,56,29,34,13],
  "Deuteronomy":      [46,37,29,49,33,25,26,20,29,22,32,32,18,29,23,22,20,22,21,20,23,30,25,22,19,19,26,68,29,20,30,52,29,12],
  "Joshua":           [18,24,17,24,15,27,26,35,27,43,23,24,33,15,63,10,18,28,51,9,45,34,16,33],
  "Judges":           [36,23,31,24,31,40,25,35,57,18,40,15,25,20,20,31,13,31,30,48,25],
  "Ruth":             [22,23,18,22],
  "1 Samuel":         [28,36,21,22,12,21,17,22,27,27,15,25,23,52,35,23,58,30,24,42,15,23,29,22,44,25,12,25,11,31,13],
  "2 Samuel":         [27,32,39,12,25,23,29,18,13,19,27,31,39,33,37,23,29,33,43,26,22,51,39,25],
  "1 Kings":          [53,46,28,34,18,38,51,66,28,29,43,33,34,31,34,34,24,46,21,43,29,53],
  "2 Kings":          [18,25,27,44,27,33,20,29,37,36,21,21,25,29,38,20,41,37,37,21,26,20,37,20,30],
  "1 Chronicles":     [54,55,24,43,26,81,40,40,44,14,47,40,14,17,29,43,27,17,19,8,30,19,32,31,31,32,34,21,30],
  "2 Chronicles":     [17,18,17,22,14,42,22,18,31,19,23,16,22,15,19,14,19,34,11,37,20,12,21,27,28,23,9,27,36,27,21,33,25,33,27,23],
  "Ezra":             [11,70,13,24,17,22,28,36,15,44],
  "Nehemiah":         [11,20,32,23,19,19,73,18,38,39,36,47,31],
  "Esther":           [22,23,15,17,14,14,10,17,32,3],
  "Job":              [22,13,26,21,27,30,21,22,35,22,20,25,28,22,35,22,16,21,29,29,34,30,17,25,6,14,23,28,25,31,40,22,33,37,16,33,24,41,30,24,34,17],
  "Psalms":           [6,12,8,8,12,10,17,9,20,18,7,8,6,7,5,11,15,50,14,9,13,31,6,10,22,12,14,9,11,12,24,11,22,22,28,12,40,22,13,17,13,11,5,26,17,11,9,14,20,23,19,9,6,7,23,13,11,11,17,12,8,12,11,10,13,20,7,35,36,5,24,20,28,23,10,12,20,72,13,19,16,8,18,12,13,17,7,18,52,17,16,15,5,23,11,13,12,9,9,5,8,28,22,35,45,48,43,13,31,7,10,10,9,8,18,19,2,29,176,7,8,9,4,8,5,6,5,6,8,8,3,18,3,3,21,26,9,8,24,13,10,7,12,15,21,10,20,14,9,6],
  "Proverbs":         [33,22,35,27,23,35,27,36,18,32,31,28,25,35,33,33,28,24,29,30,31,29,35,34,28,28,27,28,62,33,31],
  "Ecclesiastes":     [18,26,22,16,20,12,29,17,18,20,10,14],
  "Song of Solomon":  [17,17,11,16,16,13,13,14],
  "Isaiah":           [31,22,26,6,30,13,25,22,21,34,16,6,22,32,9,14,14,7,25,6,17,25,18,23,12,21,13,29,24,33,9,20,24,17,10,22,38,22,8,31,29,25,28,28,25,13,15,22,26,11,23,15,12,17,13,12,21,14,21,22,11,12,19,12,25,24],
  "Jeremiah":         [19,37,25,31,31,30,34,22,26,25,23,17,27,22,21,21,27,23,15,18,14,30,40,10,38,24,22,17,32,24,40,44,26,22,19,32,21,28,18,16,18,22,13,30,5,28,7,47,39,46,64,34],
  "Lamentations":     [22,22,66,22,22],
  "Ezekiel":          [28,10,27,17,17,14,27,18,11,22,25,28,23,23,8,63,24,32,14,49,32,31,49,27,17,21,36,26,21,26,18,32,33,31,15,38,28,23,29,49,26,20,27,31,25,24,23,35],
  "Daniel":           [21,49,30,37,31,28,28,27,27,21,45,13],
  "Hosea":            [11,23,5,19,15,11,16,14,17,15,12,14,16,9],
  "Joel":             [20,32,21],
  "Amos":             [15,16,15,13,27,14,17,14,15],
  "Obadiah":          [21],
  "Jonah":            [17,10,10,11],
  "Micah":            [16,13,12,13,15,16,20],
  "Nahum":            [15,13,19],
  "Habakkuk":         [17,20,19],
  "Zephaniah":        [18,15,20],
  "Haggai":           [15,23],
  "Zechariah":        [21,13,10,14,11,15,14,23,17,12,17,14,9,21],
  "Malachi":          [14,17,18,6],
  "Matthew":          [25,23,17,25,48,34,29,34,38,42,30,50,58,36,39,28,27,35,30,34,46,46,39,51,46,75,66,20],
  "Mark":             [45,28,35,41,43,56,37,38,50,52,33,44,37,72,47,20],
  "Luke":             [80,52,38,44,39,49,50,56,62,42,54,59,35,35,32,31,37,43,48,47,38,71,56,53],
  "John":             [51,25,36,54,47,71,53,59,41,42,57,50,38,31,27,33,26,40,42,31,25],
  "Acts":             [26,47,26,37,42,15,60,40,43,48,30,25,52,28,41,40,34,28,41,38,40,30,35,27,27,32,44,31],
  "Romans":           [32,29,31,25,21,23,25,39,33,21,36,21,14,23,33,27],
  "1 Corinthians":    [31,16,23,21,13,20,40,13,27,33,34,31,13,40,58,24],
  "2 Corinthians":    [24,17,18,18,21,18,16,24,15,18,33,21,14],
  "Galatians":        [24,21,29,31,26,18],
  "Ephesians":        [23,22,21,32,33,24],
  "Philippians":      [30,30,21,23],
  "Colossians":       [29,23,25,18],
  "1 Thessalonians":  [10,20,13,18,28],
  "2 Thessalonians":  [12,17,18],
  "1 Timothy":        [20,15,16,16,25,21],
  "2 Timothy":        [18,26,17,22],
  "Titus":            [16,15,15],
  "Philemon":         [25],
  "Hebrews":          [14,18,19,16,14,20,28,13,28,39,40,29,25],
  "James":            [27,26,18,17,20],
  "1 Peter":          [25,25,22,19,14],
  "2 Peter":          [21,22,18],
  "1 John":           [10,29,24,21,21],
  "2 John":           [13],
  "3 John":           [14],
  "Jude":             [25],
  "Revelation":       [20,29,22,11,14,17,17,13,21,11,19,17,18,20,8,21,18,24,21,15,27,21],
};

function getMaxVerse(bookName, chapter) {
    const counts = VERSE_COUNTS[bookName];
    return (counts && counts[chapter - 1]) ? counts[chapter - 1] : 176;
}


// ─── Shared Book Data ─────────────────────────────────────────
// Keyed by book id: { id, name, testament, chapter_count, order }
const booksById = {};
let   booksFetched = false;

async function fetchBooksForCurrentSettings() {
    const settings         = getSettings();
    const canon            = settings.canon           || 'P';
    const includeApocrypha = settings.includeApocrypha || false;

    const res   = await fetch(`/api/books?canon=${canon}`);
    let   books = await res.json();

    // Strip AP-testament books unless the user has opted in
    if (!includeApocrypha) {
        books = books.filter(b => b.testament !== 'AP');
    }

    return books;
}

async function ensureBooks() {
    if (booksFetched) return;
    try {
        const books = await fetchBooksForCurrentSettings();
        books.forEach((book, index) => {
            booksById[book.id] = { ...book, order: index };
        });
        booksFetched = true;
    } catch (err) {
        console.error('Failed to load books:', err);
    }
}

// Incremented each time refreshBooks() is called so stale async responses
// from earlier calls can be detected and discarded.
let refreshGeneration = 0;

async function refreshBooks() {
    const myGen = ++refreshGeneration;

    // Fetch fresh data directly — bypass the booksFetched cache so we always
    // get the data that matches the current settings.
    let books;
    try {
        books = await fetchBooksForCurrentSettings();
    } catch (err) {
        console.error('Failed to refresh books:', err);
        return;
    }

    // A newer call has already started — our data is stale; bail out.
    if (myGen !== refreshGeneration) return;

    // Commit new data to the shared cache
    Object.keys(booksById).forEach(k => delete booksById[k]);
    books.forEach((book, index) => {
        booksById[book.id] = { ...book, order: index };
    });
    booksFetched = true;

    // Rebuild the book dropdown
    const bookSelect = document.getElementById('book-select');
    bookSelect.innerHTML = '<option value="">— select a book —</option>';
    Object.values(booksById)
        .sort((a, b) => a.order - b.order)
        .forEach(book => {
            const opt = document.createElement('option');
            opt.value = book.id;
            opt.textContent = book.name;
            opt.dataset.chapters = book.chapter_count;
            bookSelect.appendChild(opt);
        });

    // Reset dependent selects since the book list changed
    resetSelect(document.getElementById('start-ch'), 'Ch');
    resetSelect(document.getElementById('start-vs'), 'Vs');
    resetSelect(document.getElementById('end-ch'),   'Ch');
    resetSelect(document.getElementById('end-vs'),   'Vs');
}


// ─── Add Reading Form ─────────────────────────────────────────
async function initForm() {
    document.getElementById('date-read').value = todayLocal();

    await ensureBooks();

    const bookSelect = document.getElementById('book-select');
    Object.values(booksById)
        .sort((a, b) => a.order - b.order)
        .forEach(book => {
            const opt = document.createElement('option');
            opt.value = book.id;
            opt.textContent = book.name;
            opt.dataset.chapters = book.chapter_count;
            bookSelect.appendChild(opt);
        });
}

function populateRange(selectEl, min, max, placeholder) {
    selectEl.innerHTML = `<option value="">${placeholder}</option>`;
    for (let i = min; i <= max; i++) {
        const opt = document.createElement('option');
        opt.value = i;
        opt.textContent = i;
        selectEl.appendChild(opt);
    }
    selectEl.disabled = false;
}

function resetSelect(selectEl, placeholder) {
    selectEl.innerHTML = `<option value="">${placeholder}</option>`;
    selectEl.disabled = true;
}

function selectedBookName() {
    const sel = document.getElementById('book-select');
    return sel.options[sel.selectedIndex]?.textContent ?? '';
}

document.getElementById('book-select').addEventListener('change', function () {
    resetSelect(document.getElementById('start-vs'), 'Vs');
    resetSelect(document.getElementById('end-vs'),   'Vs');

    if (!this.value) {
        resetSelect(document.getElementById('start-ch'), 'Ch');
        resetSelect(document.getElementById('end-ch'),   'Ch');
        return;
    }

    const chapters = parseInt(this.options[this.selectedIndex].dataset.chapters);
    populateRange(document.getElementById('start-ch'), 1, chapters, 'Ch');
    populateRange(document.getElementById('end-ch'),   1, chapters, 'Ch');
});

document.getElementById('start-ch').addEventListener('change', function () {
    resetSelect(document.getElementById('start-vs'), 'Vs');
    resetSelect(document.getElementById('end-vs'),   'Vs');

    if (!this.value) {
        resetSelect(document.getElementById('end-ch'), 'Ch');
        return;
    }

    const startChNum = parseInt(this.value);
    const chapters   = parseInt(document.getElementById('book-select').options[
                           document.getElementById('book-select').selectedIndex
                       ].dataset.chapters);

    populateRange(document.getElementById('start-vs'), 1, getMaxVerse(selectedBookName(), startChNum), 'Vs');
    populateRange(document.getElementById('end-ch'), startChNum, chapters, 'Ch');
});

document.getElementById('start-vs').addEventListener('change', function () {
    const startChNum = parseInt(document.getElementById('start-ch').value);
    const endChNum   = parseInt(document.getElementById('end-ch').value);
    const endVs      = document.getElementById('end-vs');

    if (endChNum && startChNum === endChNum && this.value) {
        populateRange(endVs, parseInt(this.value), getMaxVerse(selectedBookName(), endChNum), 'Vs');
    }
});

document.getElementById('end-ch').addEventListener('change', function () {
    const endVs      = document.getElementById('end-vs');
    const startChNum = parseInt(document.getElementById('start-ch').value);
    const startVs    = parseInt(document.getElementById('start-vs').value);

    if (!this.value) { resetSelect(endVs, 'Vs'); return; }

    const endChNum = parseInt(this.value);
    const minVerse = (endChNum === startChNum && startVs) ? startVs : 1;
    populateRange(endVs, minVerse, getMaxVerse(selectedBookName(), endChNum), 'Vs');
});

document.getElementById('reading-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const bookSel  = document.getElementById('book-select');
    const bookId   = parseInt(bookSel.value);
    const dateRead = document.getElementById('date-read').value;
    const startCh  = parseInt(document.getElementById('start-ch').value);
    const startVs  = parseInt(document.getElementById('start-vs').value);
    const endCh    = parseInt(document.getElementById('end-ch').value);
    const endVs    = parseInt(document.getElementById('end-vs').value);

    if (!bookId || !dateRead || !startCh || !startVs || !endCh || !endVs) return;

    try {
        const res = await fetch('/api/readings/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                book_id: bookId, date_read: dateRead,
                start_chapter: startCh, start_verse: startVs,
                end_chapter: endCh,     end_verse:   endVs,
            }),
        });

        if (!res.ok) {
            const body = await res.text();
            let msg = body;
            try { msg = JSON.parse(body).detail; } catch {}
            showConfirmation(`Error: ${msg}`, true);
            return;
        }

        const bookName = bookSel.options[bookSel.selectedIndex].textContent;
        const ref      = `${bookName} ${startCh}:${startVs}–${endCh}:${endVs}`;
        const dateFmt  = new Date(dateRead + 'T00:00:00').toLocaleDateString('en-US', {
            month: 'long', day: 'numeric', year: 'numeric',
        });
        showConfirmation(`Saved: ${ref} (${dateFmt})`);
        clearForm();

        // Refresh cached readings so history is up to date
        fetchReadings();

    } catch (err) {
        showConfirmation('Error saving reading. Please try again.', true);
        console.error(err);
    }
});

function showConfirmation(message, isError = false) {
    const el = document.getElementById('reading-confirmation');
    el.textContent = message;
    el.className = isError ? 'confirmation error' : 'confirmation';
    el.hidden = false;
    setTimeout(() => { el.hidden = true; }, 6000);
}

function clearForm() {
    document.getElementById('date-read').value = todayLocal();
    document.getElementById('book-select').value = '';
    resetSelect(document.getElementById('start-ch'), 'Ch');
    resetSelect(document.getElementById('start-vs'), 'Vs');
    resetSelect(document.getElementById('end-ch'),   'Ch');
    resetSelect(document.getElementById('end-vs'),   'Vs');
}

document.getElementById('clear-btn').addEventListener('click', () => {
    document.getElementById('reading-confirmation').hidden = true;
    clearForm();
});


// ─── Reading History ──────────────────────────────────────────
let allReadings = [];
let sortMode    = 'chrono'; // 'chrono' | 'book'

async function fetchReadings() {
    try {
        const res = await fetch('/api/readings/?canon=P');
        allReadings = await res.json();
    } catch (err) {
        console.error('Failed to fetch readings:', err);
    }
}

async function loadReadings() {
    await ensureBooks();
    await fetchReadings();
    renderReadings();
}

function renderReadings() {
    const list   = document.getElementById('readings-list');
    let   sorted = [...allReadings];

    if (sortMode === 'chrono') {
        // Newest date first; tie-break by id desc (insertion order)
        sorted.sort((a, b) =>
            b.date_read.localeCompare(a.date_read) || b.id - a.id
        );
    } else {
        // Biblical order → chapter → verse
        sorted.sort((a, b) => {
            const orderA = booksById[a.book_id]?.order ?? 999;
            const orderB = booksById[b.book_id]?.order ?? 999;
            return orderA - orderB
                || a.start_chapter - b.start_chapter
                || a.start_verse   - b.start_verse;
        });
    }

    if (sorted.length === 0) {
        list.innerHTML = '<p class="empty-state">No readings recorded yet.</p>';
        return;
    }

    list.innerHTML = '';
    sorted.forEach(reading => {
        const book    = booksById[reading.book_id];
        const name    = book?.name ?? `Book #${reading.book_id}`;
        const ref     = `${name} ${reading.start_chapter}:${reading.start_verse}–${reading.end_chapter}:${reading.end_verse}`;
        const dateFmt = new Date(reading.date_read + 'T00:00:00').toLocaleDateString('en-US', {
            month: 'short', day: 'numeric', year: 'numeric',
        });

        const entry = document.createElement('div');
        entry.className = 'reading-entry';
        entry.dataset.id = reading.id;
        entry.innerHTML = `
            <span class="ref">${ref}</span>
            <span class="date">${dateFmt}</span>
            <div class="entry-actions">
                <button class="btn-delete" data-id="${reading.id}" type="button">Delete</button>
            </div>
        `;
        list.appendChild(entry);
    });
}

// Sort toggle
document.getElementById('sort-toggle').addEventListener('click', function () {
    sortMode = sortMode === 'chrono' ? 'book' : 'chrono';
    this.textContent = sortMode === 'chrono' ? 'Sort by Book' : 'Sort Chronologically';
    renderReadings();
});

// Delete — event-delegated on the list
document.getElementById('readings-list').addEventListener('click', async function (e) {
    // Confirm button: execute the delete
    if (e.target.closest('.btn-confirm-delete')) {
        const btn = e.target.closest('.btn-confirm-delete');
        const id  = parseInt(btn.dataset.id);
        try {
            const res = await fetch(`/api/readings/${id}`, { method: 'DELETE' });
            if (res.ok || res.status === 204) {
                allReadings = allReadings.filter(r => r.id !== id);
                renderReadings();
            }
        } catch (err) {
            console.error('Delete failed:', err);
        }
        return;
    }

    // Cancel button: restore the original delete button
    if (e.target.closest('.btn-cancel-delete')) {
        const entry = e.target.closest('.reading-entry');
        const id    = parseInt(entry.dataset.id);
        entry.querySelector('.entry-actions').innerHTML =
            `<button class="btn-delete" data-id="${id}" type="button">Delete</button>`;
        return;
    }

    // Delete button: swap in confirm/cancel
    const btn = e.target.closest('.btn-delete');
    if (!btn) return;

    const actions = btn.closest('.entry-actions');
    const id      = parseInt(btn.dataset.id);
    actions.innerHTML = `
        <span class="delete-confirm-label">Delete?</span>
        <button class="btn-confirm-delete" data-id="${id}" type="button">Yes</button>
        <button class="btn-cancel-delete" type="button">No</button>
    `;
});


// ─── Settings ─────────────────────────────────────────────────
function initSettings() {
    const settings      = getSettings();
    const canonSelect   = document.getElementById('canon-select');
    const apocryphaRow  = document.getElementById('apocrypha-row');
    const apocryphaChk  = document.getElementById('apocrypha-check');

    // Restore persisted values
    canonSelect.value    = settings.canon           || 'P';
    apocryphaChk.checked = settings.includeApocrypha || false;
    apocryphaRow.hidden  = canonSelect.value !== 'P';

    // Persist current UI state and refresh the book dropdown immediately
    async function applyAndSave() {
        const updated = {
            canon:            canonSelect.value,
            includeApocrypha: canonSelect.value === 'P' && apocryphaChk.checked,
        };
        localStorage.setItem('bibleTrackerSettings', JSON.stringify(updated));
        await refreshBooks();
    }

    // Canon dropdown — show/hide Apocrypha row and apply immediately
    canonSelect.addEventListener('change', function () {
        apocryphaRow.hidden = this.value !== 'P';
        if (this.value !== 'P') apocryphaChk.checked = false;
        applyAndSave();
    });

    // Apocrypha checkbox — apply immediately
    apocryphaChk.addEventListener('change', () => applyAndSave());

    // Save button — apply (in case nothing changed) and show confirmation
    document.getElementById('save-settings-btn').addEventListener('click', async () => {
        await applyAndSave();
        const el = document.getElementById('settings-confirmation');
        el.textContent = 'Settings saved.';
        el.className   = 'confirmation';
        el.hidden      = false;
        setTimeout(() => { el.hidden = true; }, 4000);
    });
}


// ─── Heatmap ──────────────────────────────────────────────────
const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

async function loadHeatmap() {
    try {
        const res  = await fetch('/api/heatmap');
        const data = await res.json();

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Today sits in the last column (col 51); its row = day-of-week (0=Sun)
        const todayCell = 51 * 7 + today.getDay() + 1;  // 1-based cell index

        data.forEach(({ date, count }) => {
            const d       = new Date(date + 'T00:00:00');
            const daysAgo = Math.round((today - d) / 86400000);
            const cellIdx = todayCell - daysAgo;
            if (cellIdx < 1 || cellIdx > 364) return;

            const cell = document.getElementById('hm' + cellIdx);
            if (!cell) return;

            cell.dataset.level = count === 0 ? 0
                               : count <  5  ? 1
                               : count < 15  ? 2
                               : count < 30  ? 3
                               :               4;

            const label = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            cell.title  = count > 0 ? `${label}: ${count} verses` : label;
        });

        buildHeatmapMonthLabels(today);

    } catch (err) {
        console.error('Failed to load heatmap:', err);
    }
}

function buildHeatmapMonthLabels(today) {
    const thead = document.querySelector('thead.heatmap');
    if (!thead) return;

    // Sunday of the current week
    const weekStart = new Date(today);
    weekStart.setDate(today.getDate() - today.getDay());

    // Determine which month each of the 52 columns belongs to (by its Sunday)
    const colMonths = [];
    for (let col = 0; col < 52; col++) {
        const sunday = new Date(weekStart);
        sunday.setDate(weekStart.getDate() - (51 - col) * 7);
        colMonths.push(sunday.getMonth());
    }

    // Collapse consecutive same-month columns into spans
    const spans = [];
    let run = 1;
    for (let col = 1; col < 52; col++) {
        if (colMonths[col] === colMonths[col - 1]) {
            run++;
        } else {
            spans.push({ month: colMonths[col - 1], span: run });
            run = 1;
        }
    }
    spans.push({ month: colMonths[51], span: run });

    // Build the header row
    const row = document.createElement('tr');
    const spacer = document.createElement('td');   // aligns with the day-label column
    spacer.className = 'day-label';
    row.appendChild(spacer);

    spans.forEach(({ month, span }) => {
        const th = document.createElement('th');
        th.colSpan   = span;
        th.className = 'heatmap-month';
        th.textContent = span >= 3 ? MONTH_NAMES[month] : '';
        row.appendChild(th);
    });

    thead.innerHTML = '';
    thead.appendChild(row);
}


// ─── Init ─────────────────────────────────────────────────────
initForm();
initSettings();
loadHeatmap();
