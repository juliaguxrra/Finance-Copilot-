# Finance Co-Pilot

Hi, I'm Julia! Finance Co-Pilot is a simple, friendly dashboard where you log your expenses, watch your spending patterns show up as charts, and ask plain-English questions like *"How much did I spend on groceries?"* or *"How can I save $300 next month?"* and get a real answer back.

![status](https://img.shields.io/badge/status-active-6FC1EF) ![made with](https://img.shields.io/badge/made%20with-FastAPI%20%2B%20Next.js-F6D948)

---

## What it does

- **Logs expenses in seconds** ⚪️ pick a category, type the merchant, enter the amount, done. Everything saves automatically, even if you refresh.
- **Shows you the shape of your spending** ⚪️ a monthly bar chart and a category breakdown pie chart, powered by Recharts.
- **Forecasts next month** so you're not caught off guard.
- **Explains *why*** your spending moved, not just that it did (e.g. "You spent $42 more than last month because Restaurants increased by $30").
- **Answers questions in your own words** ⚪️ ask about a category, a merchant, a specific month, or a savings goal, and it'll figure out what you mean.
- **Has a brain even without an API key** ⚪️ if you don't hook up Claude or Gemini, it falls back to a solid rule-based answer engine, so the app never feels broken.

## How it's built

It's a two-part app: a Next.js frontend and a FastAPI backend, talking to each other over a simple REST API.

| Layer | Stack |
|---|---|
| Frontend | Next.js, TypeScript, Recharts |
| Backend | FastAPI, Pydantic |
| AI | Claude (Anthropic) first, Gemini as backup, rule-based answers if neither is configured |
| Storage | A local `transactions.json` file — no database setup needed |

## Getting it running on your machine

You'll need **Python 3.10+** and **Node.js 18+** installed. That's it.

### 1. Clone it

```bash
git clone https://github.com/juliaguxrra/finance-copilot.git
cd finance-copilot
```

### 2. Set up the backend

```bash
cd backend
pip install -r requirements.txt
```

Copy the example env file and fill in what you have:

```bash
cp .env.example .env
```

```env
ANTHROPIC_API_KEY=       # optional ⚪️ enables Claude-powered answers
GEMINI_API_KEY=          # optional ⚪️ used if no Anthropic key is set
FRONTEND_ORIGIN=         # optional ⚪️ only needed if you deploy the frontend somewhere other than localhost
```

If you don't have either API key handy, leave them blank and the app will answer questions using its built-in rule-based logic instead.

Start the server:

```bash
uvicorn main:app --reload
```

It'll be running at `http://localhost:8000`.

### 3. Set up the frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` and you should see your dashboard.

## Using it

1. **Add an expense** ⚪️ pick a category (or type your own under "Other"), enter where you spent it and how much, and hit *Add expense*. It shows up instantly in your charts and your activity table.
2. **Ask it anything** ⚪️ type a question like *"What's my biggest expense?"* or *"How can I save $300?"* and hit *Ask*. You'll see a little tag telling you whether Claude, Gemini, or the built-in logic answered.
3. **Delete a mistake** ⚪️ hit *Remove* next to any transaction in your activity table.
4. **Watch your forecast update** ⚪️ the "what we expect next month" number recalculates automatically as you add more history.

## Roadmap ideas

- [ ] Multi-user accounts with auth
- [ ] Recurring transaction detection
- [ ] CSV import from your bank
- [ ] Budget limits per category with alerts

## About me

I'm Julia a Computer Science grad who likes building things that make everyday tasks (like actually looking at your bank statement) a little less painful. If you use this and it helps you save a coffee-run's worth of money, that's a win in my book.

Feel free to open an issue, fork it, or reach out — [linkedin.com/in/juliaiguerra](https://linkedin.com/in/juliaiguerra) or guerrajuliaisabella@gmail.com.
