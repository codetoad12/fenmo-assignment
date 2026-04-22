'use strict';

const list = document.getElementById('expense-list');
const totalEl = document.getElementById('total-amount');
const filterEl = document.getElementById('filter-category');
const sortEl = document.getElementById('sort-order');
const form = document.getElementById('expense-form');
const submitBtn = document.getElementById('submit-btn');
const formError = document.getElementById('form-error');

let idempotencyKey = crypto.randomUUID();

function resetKey() {
  idempotencyKey = crypto.randomUUID();
}

function formatDate(iso) {
  return iso ? iso.slice(0, 10) : '';
}

function formatDateTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleString();
}

function renderExpenses(items) {
  if (!items.length) {
    list.innerHTML = '<p class="empty">No expenses yet.</p>';
    totalEl.textContent = '0.00';
    return;
  }
  const total = items.reduce((s, e) => s + e.amount, 0);
  totalEl.textContent = total.toFixed(2);
  const rows = items.map(e => `
    <tr>
      <td>${e.amount.toFixed(2)}</td>
      <td>${e.category}</td>
      <td>${e.description}</td>
      <td>${formatDate(e.date)}</td>
      <td>${formatDateTime(e.created_at)}</td>
    </tr>
  `).join('');
  list.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Amount</th><th>Category</th>
          <th>Description</th><th>Date</th><th>Created</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

async function loadExpenses() {
  list.innerHTML = '<p class="loading">Loading...</p>';
  const category = filterEl.value.trim();
  const order = sortEl.value;
  const params = new URLSearchParams({ sort: 'date', order });
  if (category) params.set('category', category);
  try {
    const res = await fetch(`/expenses?${params}`);
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    const items = await res.json();
    renderExpenses(items);
  } catch (err) {
    list.innerHTML =
      `<p class="error">Failed to load expenses: ${err.message}</p>`;
  }
}

filterEl.addEventListener('input', loadExpenses);
sortEl.addEventListener('change', loadExpenses);

loadExpenses();
