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

['amount', 'category', 'description', 'date'].forEach(id => {
  document.getElementById(id).addEventListener('input', resetKey);
});

document.getElementById('date').valueAsDate = new Date();

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  formError.textContent = '';
  formError.classList.add('hidden');
  submitBtn.disabled = true;

  const body = {
    amount: parseFloat(form.amount.value),
    category: form.category.value.trim(),
    description: form.description.value.trim(),
    date: form.date.value,
  };

  try {
    const res = await fetch('/expenses', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Idempotency-Key': idempotencyKey,
      },
      body: JSON.stringify(body),
    });

    if (res.status === 201 || res.status === 200) {
      form.reset();
      resetKey();
      await loadExpenses();
    } else if (res.status === 409) {
      formError.textContent =
        'Conflict: this idempotency key was used with different data.';
      formError.classList.remove('hidden');
    } else if (res.status === 422) {
      const data = await res.json();
      const msgs = (data.detail || [])
        .map(d => d.msg).join(', ');
      formError.textContent = msgs || 'Validation error.';
      formError.classList.remove('hidden');
    } else {
      formError.textContent = `Unexpected error (${res.status}).`;
      formError.classList.remove('hidden');
    }
  } catch (err) {
    formError.textContent =
      `Network error: ${err.message}. Click submit to retry.`;
    formError.classList.remove('hidden');
  } finally {
    submitBtn.disabled = false;
  }
});
