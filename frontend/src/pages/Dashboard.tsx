import { useEffect, useState } from 'react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { analyticsAPI, collectionAPI } from '../api/client'
import type { RankingItem, RegionalSummary, CollectionLog } from '../types'

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0']

export default function Dashboard() {
  const [fiscalYear, setFiscalYear] = useState(2022)
  const [ranking, setRanking] = useState<RankingItem[]>([])
  const [regional, setRegional] = useState<RegionalSummary[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [serviceTypeStats, setServiceTypeStats] = useState<any[]>([])
  const [topPrefectures, setTopPrefectures] = useState<any[]>([])
  const [collectionLogs, setCollectionLogs] = useState<CollectionLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [fiscalYear])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [rankRes, regRes, sumRes, stRes, tpRes, colRes] = await Promise.all([
        analyticsAPI.ranking(fiscalYear, 10),
        analyticsAPI.regional(fiscalYear),
        analyticsAPI.summary(),
        analyticsAPI.serviceTypeStats(fiscalYear),
        analyticsAPI.topPrefectures(fiscalYear, 'revenue', 5),
        collectionAPI.list(0, 5),
      ])

      setRanking(rankRes.data.data)
      setRegional(regRes.data.data)
      setSummary(sumRes.data)
      setServiceTypeStats(stRes.data.data || [])
      setTopPrefectures(tpRes.data.data || [])
      setCollectionLogs(colRes.data.data || [])
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

      {/* Service Type Stats */}
      <div className="dashboard__chart">
        <h2>Facilities by Service Type</h2>
        {serviceTypeStats.length > 0 && (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={serviceTypeStats.slice(0, 10)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="service_type" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="facility_count" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Prefecture Revenue Trend */}
      <div className="dashboard__chart">
        <h2>Top 5 Prefectures Revenue Trend</h2>
        {topPrefectures.length > 0 && (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={topPrefectures.slice(0, 5)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="prefecture" />
              <YAxis />
              <Tooltip formatter={(value) => `¥${(value as number).toLocaleString()}`} />
              <Legend />
              <Line type="monotone" dataKey="total_revenue" stroke="#ff7c7c" name="Total Revenue" />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Collection Logs Monitor */}
      <div className="dashboard__chart">
        <h2>Latest Data Collection Logs</h2>
        {collectionLogs.length > 0 && (
          <div className="collection-logs-panel">
            {collectionLogs.map((log) => (
              <div key={log.id} className={`log-item log-${log.status}`}>
                <div className="log-header">
                  <span className="log-script">{log.script_name}</span>
                  <span className={`log-status status-${log.status}`}>{log.status.toUpperCase()}</span>
                </div>
                <div className="log-details">
                  <small>{new Date(log.started_at).toLocaleString()}</small>
                  {log.records_processed > 0 && (
                    <small>{log.records_processed} records</small>
                  )}
                  {log.error_message && (
                    <div className="log-error">{log.error_message}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
