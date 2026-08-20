const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type Transaction = {
  id: string;
  date: string;
  merchant: string;
  category: string;
  amount: number;
};

export type Dashboard = {
  monthly_totals: { month: string; total: number }[];
  current_month: string | null;
  category_breakdown: { category: string; total: number }[];
  forecast_next_month: number;
  insight: string;
  transactions: Transaction[];
};

export type TransactionInput = {
  category: string;
  merchant: string;
  amount: number;
  date?: string; 
};

async function parseErrorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json();
    if (Array.isArray(body?.detail)) {
      const messages = body.detail.map((d: { loc?: (string | number)[]; msg?: string }) => {
        const field = d.loc?.[d.loc.length - 1];
        return field && d.msg ? `${field}: ${d.msg}` : d.msg;
      });
      return messages.filter(Boolean).join('; ') || fallback;
    }
    if (typeof body?.detail === 'string') return body.detail;
  } catch {
    // fall through to default message
  }
  return fallback;
}

export async function getDashboard(): Promise<Dashboard> {
  const res = await fetch(`${API_URL}/dashboard`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Failed to load dashboard (${res.status})`));
  }
  return res.json();
}

export async function getCategories(): Promise<string[]> {
  const res = await fetch(`${API_URL}/categories`, { cache: 'no-store' });
  if (!res.ok) return [];
  return res.json();
}

export async function addTransaction(input: TransactionInput): Promise<Dashboard> {
  const res = await fetch(`${API_URL}/transactions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Failed to add expense (${res.status})`));
  }
  return res.json();
}

export async function deleteTransaction(id: string): Promise<Dashboard> {
  const res = await fetch(`${API_URL}/transactions/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Failed to delete expense (${res.status})`));
  }
  return res.json();
}

export async function askQuestion(question: string): Promise<{ answer: string; source?: string }> {
  const res = await fetch(`${API_URL}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    throw new Error(`Failed to get an answer (${res.status})`);
  }
  return res.json();
}
