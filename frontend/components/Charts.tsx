'use client';

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

const ACCENT = '#6FC1EF';
const PALETTE = ['#6FC1EF', '#F6D948', '#A7DBF5', '#FBE896', '#3FA3DA', '#E8C233'];

const TOOLTIP_STYLE = {
  background: '#FFFFFF',
  border: '1px solid #BFE0F5',
  borderRadius: 8,
  fontSize: 13,
  color: '#1E3245',
  boxShadow: '0 4px 14px rgba(111, 193, 239, 0.25)',
};

function EmptyChart({ label }: { label: string }) {
  return (
    <div className="chartEmpty" style={{ height: 260 }}>
      {label}
    </div>
  );
}

export function SpendBar({ data }: { data: { month: string; total: number }[] }) {
  if (data.length === 0) {
    return <EmptyChart label="Add an expense to see monthly spending here." />;
  }
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#D9ECF9" vertical={false} />
        <XAxis dataKey="month" stroke="#5E7A91" fontSize={12} tickLine={false} axisLine={false} />
        <YAxis
          stroke="#5E7A91"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `$${v}`}
        />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(value: number) => [`$${value.toFixed(2)}`, 'Total']}
        />
        <Bar dataKey="total" fill={ACCENT} radius={[6, 6, 0, 0]} maxBarSize={56} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function CategoryPie({ data }: { data: { category: string; total: number }[] }) {
  if (data.length === 0) {
    return <EmptyChart label="Add an expense to see the category breakdown here." />;
  }
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={data}
          dataKey="total"
          nameKey="category"
          innerRadius={55}
          outerRadius={90}
          paddingAngle={3}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={PALETTE[i % PALETTE.length]} stroke="none" />
          ))}
        </Pie>
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(value: number, name: string) => [`$${value.toFixed(2)}`, name]}
        />
        <Legend
          verticalAlign="bottom"
          height={36}
          iconType="circle"
          wrapperStyle={{ fontSize: 12, color: '#5E7A91' }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
