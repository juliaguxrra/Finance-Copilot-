'use client';

import { useEffect, useState } from 'react';
import {
  getDashboard,
  getCategories,
  addTransaction,
  deleteTransaction,
  askQuestion,
  Dashboard,
} from '../lib/api';
import { SpendBar, CategoryPie } from '../components/Charts';

const DEFAULT_CATEGORIES = [
  'Groceries',
  'Restaurants',
  'Transportation',
  'Subscriptions',
  'Shopping',
  'Entertainment',
  'Utilities',
  'Healthcare',
  'Travel',
  'Other',
];

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function sourceLabel(source: string) {
  switch (source) {
    case 'claude':
      return '✨ Answered by Claude';
    case 'gemini':
      return '✨ Answered by Gemini';
    default:
      return 'Answered from your spending history';
  }
}

export default function Page() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState('');

  // Ask-the-dashboard state
  const [question, setQuestion] = useState('Why did I spend more this month?');
  const [answer, setAnswer] = useState('');
  const [answerSource, setAnswerSource] = useState('');
  const [asking, setAsking] = useState(false);

  // Add-expense form state
  const [categories, setCategories] = useState<string[]>(DEFAULT_CATEGORIES);
  const [category, setCategory] = useState(DEFAULT_CATEGORIES[0]);
  const [customCategory, setCustomCategory] = useState('');
  const [merchant, setMerchant] = useState('');
  const [amount, setAmount] = useState('');
  const [txnDate, setTxnDate] = useState(todayISO());
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(() => setError('Hmm, we couldn\'t connect just now. Make sure the backend is running on port 8000.'));
    getCategories()
      .then((cats) => {
        if (cats.length) {
          setCategories(cats);
          setCategory(cats[0]);
        }
      })
      .catch(() => {
        /* keep the default category list if this fails */
      });
  }, []);

  async function handleAsk() {
    if (!question.trim()) return;
    setAsking(true);
    setAnswer('');
    setAnswerSource('');
    try {
      const result = await askQuestion(question);
      setAnswer(result.answer);
      setAnswerSource(result.source || '');
    } catch {
      setAnswer('Something went wrong on our end, mind trying that again?');
    } finally {
      setAsking(false);
    }
  }

  async function handleAddExpense(e: React.FormEvent) {
    e.preventDefault();
    setFormError('');

    const finalCategory = category === 'Other' && customCategory.trim() ? customCategory.trim() : category;
    const amountNum = parseFloat(amount);

    if (!finalCategory.trim()) {
      setFormError('Pick a category, or type your own.');
      return;
    }
    if (!merchant.trim()) {
      setFormError('Let us know where you spent this.');
      return;
    }
    if (!amountNum || amountNum <= 0) {
      setFormError('Enter an amount greater than $0.');
      return;
    }

    setSubmitting(true);
    try {
      const payload: Parameters<typeof addTransaction>[0] = {
        category: finalCategory,
        merchant: merchant.trim(),
        amount: amountNum,
      };
      if (txnDate) {
        payload.date = txnDate;
      }
      const updated = await addTransaction(payload);
      setData(updated);
      setMerchant('');
      setAmount('');
      setCustomCategory('');
      setTxnDate(todayISO());
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'We couldn\'t save that expense, please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    setDeletingId(id);
    try {
      const updated = await deleteTransaction(id);
      setData(updated);
    } catch {
      setFormError('We couldn\'t remove that one, please try again.');
    } finally {
      setDeletingId(null);
    }
  }

  if (error) {
    return (
      <main className="container">
        <div className="card">{error}</div>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="container">
        <div className="card">Getting your dashboard ready...</div>
      </main>
    );
  }

  const currentMonthTotal = data.monthly_totals[data.monthly_totals.length - 1]?.total ?? 0;
  const hasTransactions = data.transactions.length > 0;

  return (
    <main className="container">
      <div className="top">
        <div>
          <span className="badge">Your data, your entries</span>
          <h1>Welcome to your Finance Co-Pilot</h1>
          <p className="small">
            We'll help you track your spending and plan your savings. Add your expenses below,
            don't worry, everything saves automatically, even if you refresh the page.
          </p>
        </div>
      </div>

      <section className="hero">
        <h2>Your monthly snapshot</h2>
        <p className="small">Current month: {data.current_month ?? 'No expenses yet, let\'s add your first one!'}</p>
        <div className="grid kpis">
          <div className="card">
            <div className="small">Spent this month</div>
            <div className="value">${currentMonthTotal.toFixed(2)}</div>
          </div>
          <div className="card">
            <div className="small">What we expect next month</div>
            <div className="value">${data.forecast_next_month.toFixed(2)}</div>
          </div>
          <div className="card">
            <div className="small">Here's what stands out</div>
            <div>{data.insight}</div>
          </div>
        </div>
      </section>

      <section className="grid two">
        <div className="card">
          <h3>How your spending looks over time</h3>
          <SpendBar data={data.monthly_totals} />
        </div>
        <div className="card">
          <h3>Where your money is going</h3>
          <CategoryPie data={data.category_breakdown} />
        </div>
      </section>

      <section className="grid two">
        <div className="card">
          <h3>Log a new expense</h3>
          <form className="expenseForm" onSubmit={handleAddExpense}>
            <label className="field">
              <span className="fieldLabel">Category</span>
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                {categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>

            {category === 'Other' && (
              <label className="field">
                <span className="fieldLabel">What kind of expense is this?</span>
                <input
                  value={customCategory}
                  onChange={(e) => setCustomCategory(e.target.value)}
                  placeholder="e.g. Home Improvement"
                />
              </label>
            )}

            <label className="field">
              <span className="fieldLabel">Where did you spend it?</span>
              <input
                value={merchant}
                onChange={(e) => setMerchant(e.target.value)}
                placeholder="e.g. Trader Joe's"
              />
            </label>

            <div className="fieldRow">
              <label className="field">
                <span className="fieldLabel">How much? ($)</span>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                />
              </label>
              <label className="field">
                <span className="fieldLabel">When?</span>
                <input type="date" value={txnDate} onChange={(e) => setTxnDate(e.target.value)} />
              </label>
            </div>

            {formError && <p className="formError">{formError}</p>}

            <button type="submit" disabled={submitting}>
              {submitting ? 'Adding...' : 'Add expense'}
            </button>
          </form>
        </div>

        <div className="card">
          <h3>Ask me anything about your money</h3>
          <p className="small">
            Try: "How much did I spend on groceries?", "What's my biggest expense?", "How can I save
            $300?", or "What's my forecast for next month?"
          </p>
          <div className="inputRow">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
            />
            <button onClick={handleAsk} disabled={asking}>
              {asking ? 'Thinking...' : 'Ask'}
            </button>
          </div>
          {answer && (
            <div style={{ marginTop: 14 }}>
              <p>{answer}</p>
              {answerSource && <span className="sourceTag">{sourceLabel(answerSource)}</span>}
            </div>
          )}
        </div>
      </section>

      <section className="grid">
        <div className="card">
          <h3>Your recent activity</h3>
          {hasTransactions ? (
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Merchant</th>
                  <th>Category</th>
                  <th>Amount</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {data.transactions.map((t) => (
                  <tr key={t.id}>
                    <td>{t.date}</td>
                    <td>{t.merchant}</td>
                    <td>{t.category}</td>
                    <td>${t.amount.toFixed(2)}</td>
                    <td>
                      <button
                        type="button"
                        className="deleteBtn"
                        onClick={() => handleDelete(t.id)}
                        disabled={deletingId === t.id}
                      >
                        {deletingId === t.id ? '...' : 'Remove'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="small">Nothing here yet, add your first expense above to get started.</p>
          )}
        </div>
      </section>
    </main>
  );
}
