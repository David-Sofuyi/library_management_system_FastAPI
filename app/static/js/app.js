// State
let state = {
  books: [],
  activeLoans: [],
  allLoans: [],
  currentTab: 'books',
  searchQuery: ''
};

// Toast Notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Format Date Helper
function formatDate(dateString) {
  if (!dateString) return '—';
  const d = new Date(dateString);
  return d.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// API Functions
async function loadAllData() {
  await Promise.all([loadBooks(), loadActiveLoans(), loadAllLoans()]);
  updateStats();
}

async function loadBooks(query = '') {
  try {
    const url = query ? `/books/?query=${encodeURIComponent(query)}` : '/books/';
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch books');
    state.books = await res.json();
    renderBooks();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadActiveLoans(borrowerId = '') {
  try {
    const url = borrowerId
      ? `/books/loans/active?borrower_id=${encodeURIComponent(borrowerId)}`
      : '/books/loans/active';
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch active loans');
    state.activeLoans = await res.json();
    renderActiveLoans();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadAllLoans() {
  try {
    const res = await fetch('/books/loans');
    if (!res.ok) throw new Error('Failed to fetch loan history');
    state.allLoans = await res.json();
    renderLoanHistory();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Update Stats Cards
function updateStats() {
  const totalTitles = state.books.length;
  let totalCopies = 0;
  let availableCopies = 0;

  state.books.forEach(b => {
    totalCopies += b.total_copies || 0;
    availableCopies += b.available_copies || 0;
  });

  const activeLoans = state.activeLoans.length;

  document.getElementById('stat-total-titles').textContent = totalTitles;
  document.getElementById('stat-total-copies').textContent = totalCopies;
  document.getElementById('stat-available-copies').textContent = availableCopies;
  document.getElementById('stat-active-loans').textContent = activeLoans;
}

// Render Functions
function renderBooks() {
  const container = document.getElementById('books-container');
  if (!state.books || state.books.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <h3>No books found</h3>
        <p>Get started by clicking "+ Add Book" above.</p>
      </div>`;
    return;
  }

  container.innerHTML = state.books
    .map(book => {
      const inStock = book.available_copies > 0;
      const statusBadge = inStock
        ? `<span class="badge badge-in-stock">${book.available_copies} Available</span>`
        : `<span class="badge badge-out-of-stock">Out of Stock</span>`;

      return `
        <div class="book-card">
          <div class="book-header">
            <h3 class="book-title">${escapeHtml(book.title)}</h3>
            <div class="book-author">by ${escapeHtml(book.author)}</div>
          </div>
          <div class="book-meta">
            <div class="meta-row">
              <span><strong>ISBN:</strong> <code>${escapeHtml(book.isbn)}</code></span>
              ${statusBadge}
            </div>
            <div class="meta-row">
              <span><strong>Total Owned:</strong> ${book.total_copies}</span>
              <span><strong>On Loan:</strong> ${book.total_copies - book.available_copies}</span>
            </div>
          </div>
          <div class="book-actions">
            <button class="btn btn-primary btn-sm" onclick="openBorrowModal('${escapeHtml(book.isbn)}')" ${!inStock ? 'disabled style="opacity:0.6;cursor:not-allowed;"' : ''}>
              Borrow
            </button>
            <button class="btn btn-secondary btn-sm" onclick="openEditModal(${book.id}, '${escapeHtml(book.title)}', '${escapeHtml(book.author)}', ${book.total_copies})">
              Edit
            </button>
            <button class="btn btn-danger btn-sm" onclick="confirmDeleteBook(${book.id}, '${escapeHtml(book.title)}')">
              Delete
            </button>
          </div>
        </div>
      `;
    })
    .join('');
}

function renderActiveLoans() {
  const tbody = document.getElementById('active-loans-tbody');
  if (!state.activeLoans || state.activeLoans.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="empty-state">No active loans found. All borrowed books have been returned!</td>
      </tr>`;
    return;
  }

  tbody.innerHTML = state.activeLoans
    .map(loan => {
      const bookTitle = loan.book ? loan.book.title : `Book #${loan.book_id}`;
      const bookIsbn = loan.book ? loan.book.isbn : 'N/A';
      return `
        <tr>
          <td><strong>${escapeHtml(bookTitle)}</strong><br><small style="color:var(--text-muted)">ISBN: ${escapeHtml(bookIsbn)}</small></td>
          <td><span class="badge" style="background:#e0f2fe;color:#0369a1">${escapeHtml(loan.borrower_id)}</span></td>
          <td>${formatDate(loan.borrowed_at)}</td>
          <td><span class="badge badge-borrowed">Active Loan</span></td>
          <td>
            <button class="btn btn-success btn-sm" onclick="handleQuickReturn('${escapeHtml(bookIsbn)}', '${escapeHtml(loan.borrower_id)}')">
              Return Book
            </button>
          </td>
        </tr>
      `;
    })
    .join('');
}

function renderLoanHistory() {
  const tbody = document.getElementById('history-loans-tbody');
  if (!state.allLoans || state.allLoans.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="empty-state">No loan transactions recorded yet.</td>
      </tr>`;
    return;
  }

  tbody.innerHTML = state.allLoans
    .map(loan => {
      const bookTitle = loan.book ? loan.book.title : `Book #${loan.book_id}`;
      const statusBadge = loan.is_active
        ? '<span class="badge badge-borrowed">Active</span>'
        : '<span class="badge badge-in-stock">Returned</span>';

      return `
        <tr>
          <td><strong>${escapeHtml(bookTitle)}</strong></td>
          <td>${escapeHtml(loan.borrower_id)}</td>
          <td>${formatDate(loan.borrowed_at)}</td>
          <td>${formatDate(loan.returned_at)}</td>
          <td>${statusBadge}</td>
        </tr>
      `;
    })
    .join('');
}

// Tab Switching
function switchTab(tabName) {
  state.currentTab = tabName;
  document.querySelectorAll('.nav-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabName);
  });

  document.getElementById('view-books').style.display = tabName === 'books' ? 'block' : 'none';
  document.getElementById('view-active-loans').style.display = tabName === 'active-loans' ? 'block' : 'none';
  document.getElementById('view-history').style.display = tabName === 'history' ? 'block' : 'none';

  if (tabName === 'active-loans') loadActiveLoans();
  if (tabName === 'history') loadAllLoans();
}

// Modal Helpers
function openModal(id) {
  document.getElementById(id).classList.add('open');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}

function openBorrowModal(isbn = '') {
  const input = document.getElementById('borrow-isbn');
  if (input) input.value = isbn;
  document.getElementById('borrow-member').value = '';
  openModal('modal-borrow');
}

function openEditModal(id, title, author, totalCopies) {
  document.getElementById('edit-book-id').value = id;
  document.getElementById('edit-title').value = title;
  document.getElementById('edit-author').value = author;
  document.getElementById('edit-copies').value = totalCopies;
  openModal('modal-edit-book');
}

// Forms Handlers
async function handleAddBook(e) {
  e.preventDefault();
  const isbn = document.getElementById('add-isbn').value.trim();
  const title = document.getElementById('add-title').value.trim();
  const author = document.getElementById('add-author').value.trim();
  const total_copies = parseInt(document.getElementById('add-copies').value, 10);

  try {
    const res = await fetch('/books/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ isbn, title, author, total_copies })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Could not add book');

    showToast(`Book "${title}" added successfully!`, 'success');
    closeModal('modal-add-book');
    e.target.reset();
    await loadAllData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function handleEditBook(e) {
  e.preventDefault();
  const id = document.getElementById('edit-book-id').value;
  const title = document.getElementById('edit-title').value.trim();
  const author = document.getElementById('edit-author').value.trim();
  const total_copies = parseInt(document.getElementById('edit-copies').value, 10);

  try {
    const res = await fetch(`/books/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, author, total_copies })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Could not update book');

    showToast('Book updated successfully!', 'success');
    closeModal('modal-edit-book');
    await loadAllData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function confirmDeleteBook(id, title) {
  if (!confirm(`Are you sure you want to delete "${title}"?`)) return;

  try {
    const res = await fetch(`/books/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Could not delete book');

    showToast(`Book "${title}" deleted successfully!`, 'success');
    await loadAllData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function handleBorrowSubmit(e) {
  e.preventDefault();
  const isbn = document.getElementById('borrow-isbn').value.trim();
  const borrower_id = document.getElementById('borrow-member').value.trim();

  try {
    const res = await fetch('/books/borrow', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ isbn, borrower_id })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to borrow book');

    showToast(`Book borrowed successfully for ${borrower_id}!`, 'success');
    closeModal('modal-borrow');
    await loadAllData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function handleQuickReturn(isbn, borrowerId) {
  try {
    const res = await fetch('/books/return', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ isbn, borrower_id: borrowerId })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to return book');

    showToast('Book returned successfully!', 'success');
    await loadAllData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function handleReturnSubmit(e) {
  e.preventDefault();
  const isbn = document.getElementById('return-isbn').value.trim();
  const borrower_id = document.getElementById('return-member').value.trim();

  await handleQuickReturn(isbn, borrower_id);
  closeModal('modal-return');
}

// Utilities
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Event Listeners Init
document.addEventListener('DOMContentLoaded', () => {
  loadAllData();

  // Search filter debounce
  let searchTimeout;
  const searchInput = document.getElementById('search-books-input');
  if (searchInput) {
    searchInput.addEventListener('input', e => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        loadBooks(e.target.value);
      }, 250);
    });
  }

  // Active loans borrower filter
  const filterBorrowerInput = document.getElementById('filter-borrower-input');
  if (filterBorrowerInput) {
    let filterTimeout;
    filterBorrowerInput.addEventListener('input', e => {
      clearTimeout(filterTimeout);
      filterTimeout = setTimeout(() => {
        loadActiveLoans(e.target.value.trim());
      }, 250);
    });
  }

  // Forms
  document.getElementById('form-add-book').addEventListener('submit', handleAddBook);
  document.getElementById('form-edit-book').addEventListener('submit', handleEditBook);
  document.getElementById('form-borrow-book').addEventListener('submit', handleBorrowSubmit);
  document.getElementById('form-return-book').addEventListener('submit', handleReturnSubmit);
});
