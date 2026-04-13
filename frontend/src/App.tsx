import { Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import CorporationList from './pages/CorporationList'
import CorporationDetail from './pages/CorporationDetail'
import './App.css'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-content">
          <h1><Link to="/">Welfare Facilities DB</Link></h1>
          <nav className="app-nav">
            <Link to="/">Dashboard</Link>
            <Link to="/corporations">Corporations</Link>
          </nav>
        </div>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/corporations" element={<CorporationList />} />
          <Route path="/corporations/:id" element={<CorporationDetail />} />
        </Routes>
      </main>

      <footer className="app-footer">
        <p>&copy; 2026 Welfare Facilities Database. All rights reserved.</p>
      </footer>
    </div>
  )
}

export default App
