import { useEffect, useState } from 'react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { analyticsAPI } from '../api/client'
import type { RankingItem, RegionalSummary } from '../types'

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0']

export default function Dashboard() {
  const [fiscalYear, setFiscalYear] = useState(2022)
  const [ranking, setRanking] = useState<RankingItem[]>([])
  const [regional, setRegional] = useState<RegionalSummary[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [fiscalYear])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [rankRes, regRes, sumRes] = await Promise.all([
        analyticsAPI.ranking(fiscalYear, 10),
        analyticsAPI.regional(fiscalYear),
        analyticsAPI.summary(),
      ])

      setRanking(rankRes.data.data)
      setRegional(regRes.data.data)
      setSummary(sumRes.data)
    } catch (err) {
      setError('Failed to load data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (error) return <div className="error">{error}</div>
  if (loading) return <div className="loading">Loading...</div>

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>

      {/* Year Selector */}
      <div className="dashboard__controls">
        <label>
          Fiscal Year:
          <select value={fiscalYear} onChange={(e) => setFiscalYear(Number(e.target.value))}>
            <option>2020</option>
            <option>2021</option>
            <option>2022</option>
            <option>2023</option>
          </select>
        </label>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="dashboard__stats">
          <div className="stat-card">
            <div className="stat-value">{summary.corporation_count}</div>
            <div className="stat-label">Corporations</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{summary.facility_count}</div>
            <div className="stat-label">Facilities</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{summary.total_capacity.toLocaleString()}</div>
            <div className="stat-label">Total Capacity</div>
          </div>
        </div>
      )}

      {/* Revenue Ranking */}
      <div className="dashboard__chart">
        <h2>Top Corporations by Revenue ({fiscalYear})</h2>
        {ranking.length > 0 && (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={ranking}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip formatter={(value) => `¥${(value as number).toLocaleString()}`} />
              <Bar dataKey="revenue" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Regional Summary */}
      <div className="dashboard__chart">
        <h2>Regional Summary</h2>
        {regional.length > 0 && (
          <div className="regional-grid">
            {regional.slice(0, 6).map((item, idx) => (
              <div key={item.prefecture} className="regional-card">
                <h3>{item.prefecture}</h3>
                <p><strong>{item.corporation_count}</strong> corporations</p>
                <p><strong>{item.facility_count}</strong> facilities</p>
                <p><strong>{item.total_capacity.toLocaleString()}</strong> capacity</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Facility Distribution */}
      <div className="dashboard__chart">
        <h2>Top 6 Prefectures by Facility Count</h2>
        {regional.length > 0 && (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={regional.slice(0, 6)}
                dataKey="facility_count"
                nameKey="prefecture"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label
              >
                {regional.slice(0, 6).map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
