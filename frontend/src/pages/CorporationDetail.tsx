import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { corporationsAPI } from '../api/client'
import type { Corporation, CorporationFinancial, Facility } from '../types'

export default function CorporationDetail() {
  const { id } = useParams<{ id: string }>()
  const [corporation, setCorporation] = useState<Corporation | null>(null)
  const [financials, setFinancials] = useState<CorporationFinancial[]>([])
  const [facilities, setFacilities] = useState<Facility[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [id])

  const fetchData = async () => {
    if (!id) return

    try {
      setLoading(true)
      const [corpRes, finRes, facRes] = await Promise.all([
        corporationsAPI.detail(id),
        corporationsAPI.financials(id),
        corporationsAPI.facilities(id),
      ])

      setCorporation(corpRes.data)
      setFinancials(finRes.data.financials || [])
      setFacilities(facRes.data.facilities || [])
    } catch (err) {
      setError('Failed to load corporation details')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="loading">Loading...</div>
  if (error) return <div className="error">{error}</div>
  if (!corporation) return <div className="error">Corporation not found</div>

  const chartData = financials.map((f) => ({
    year: f.fiscal_year,
    revenue: f.revenue || 0,
    profit: f.ordinary_profit || 0,
  }))

  return (
    <div className="corporation-detail">
      <Link to="/corporations" className="link">&larr; Back</Link>

      <h1>{corporation.name}</h1>

      <div className="detail-grid">
        <div className="detail-card">
          <h3>Corporation Info</h3>
          <p><strong>ID:</strong> {corporation.corporation_id}</p>
          <p><strong>Type:</strong> {corporation.type || '-'}</p>
          <p><strong>Prefecture:</strong> {corporation.prefecture || '-'}</p>
          <p><strong>City:</strong> {corporation.city || '-'}</p>
          <p><strong>Address:</strong> {corporation.address || '-'}</p>
        </div>

        <div className="detail-card">
          <h3>Facility Summary</h3>
          <p><strong>Total Facilities:</strong> {facilities.length}</p>
          <p>
            <strong>Total Capacity:</strong>{' '}
            {facilities.reduce((sum, f) => sum + (f.capacity || 0), 0).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Financial Trend */}
      {chartData.length > 0 && (
        <div className="chart-section">
          <h2>Financial Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Tooltip formatter={(value) => `¥${(value as number).toLocaleString()}`} />
              <Legend />
              <Line type="monotone" dataKey="revenue" stroke="#8884d8" name="Revenue" />
              <Line type="monotone" dataKey="profit" stroke="#82ca9d" name="Ordinary Profit" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Financial Details */}
      {financials.length > 0 && (
        <div className="section">
          <h2>Financial Details</h2>
          <table>
            <thead>
              <tr>
                <th>Year</th>
                <th>Revenue</th>
                <th>Ordinary Profit</th>
                <th>Net Assets</th>
                <th>Employees</th>
              </tr>
            </thead>
            <tbody>
              {financials.map((f) => (
                <tr key={f.id}>
                  <td>{f.fiscal_year}</td>
                  <td>{f.revenue ? `¥${f.revenue.toLocaleString()}` : '-'}</td>
                  <td>{f.ordinary_profit ? `¥${f.ordinary_profit.toLocaleString()}` : '-'}</td>
                  <td>{f.net_assets ? `¥${f.net_assets.toLocaleString()}` : '-'}</td>
                  <td>{f.employees || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Facilities */}
      {facilities.length > 0 && (
        <div className="section">
          <h2>Facilities ({facilities.length})</h2>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Service Type</th>
                <th>Capacity</th>
                <th>Prefecture</th>
              </tr>
            </thead>
            <tbody>
              {facilities.map((f) => (
                <tr key={f.facility_id}>
                  <td>{f.name}</td>
                  <td>{f.service_type || '-'}</td>
                  <td>{f.capacity || '-'}</td>
                  <td>{f.prefecture || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
