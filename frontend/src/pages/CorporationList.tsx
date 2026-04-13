import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { corporationsAPI } from '../api/client'
import type { Corporation } from '../types'

export default function CorporationList() {
  const [corporations, setCorporations] = useState<Corporation[]>([])
  const [prefecture, setPrefecture] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCorporations()
  }, [prefecture])

  const fetchCorporations = async () => {
    try {
      setLoading(true)
      const res = await corporationsAPI.list(0, 100, prefecture || undefined)
      setCorporations(res.data)
    } catch (err) {
      setError('Failed to load corporations')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (error) return <div className="error">{error}</div>

  return (
    <div className="corporation-list">
      <h1>Corporations</h1>

      <div className="controls">
        <input
          type="text"
          placeholder="Filter by prefecture..."
          value={prefecture}
          onChange={(e) => setPrefecture(e.target.value)}
        />
      </div>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Type</th>
              <th>Prefecture</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {corporations.map((corp) => (
              <tr key={corp.corporation_id}>
                <td>{corp.corporation_id}</td>
                <td>{corp.name}</td>
                <td>{corp.type || '-'}</td>
                <td>{corp.prefecture || '-'}</td>
                <td>
                  <Link to={`/corporations/${corp.corporation_id}`} className="link">
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {corporations.length === 0 && !loading && (
        <p>No corporations found</p>
      )}
    </div>
  )
}
