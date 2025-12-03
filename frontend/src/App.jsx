import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

const API_URL = 'http://localhost:8000'

function App() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [apiStatus, setApiStatus] = useState(null)

  useEffect(() => {
    // Check API health
    fetch(`${API_URL}/health`)
      .then(res => res.json())
      .then(data => setApiStatus(data.status))
      .catch(() => setApiStatus('disconnected'))

    // Fetch data
    fetch(`${API_URL}/api/data`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch data')
        return res.json()
      })
      .then(result => {
        setData(result.data)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>PnL Demo - Monorepo</h1>
      <h2>React + FastAPI</h2>
      
      <div className="card">
        <h3>API Status: 
          <span style={{ color: apiStatus === 'healthy' ? '#4ade80' : '#ef4444', marginLeft: '8px' }}>
            {apiStatus || 'checking...'}
          </span>
        </h3>
      </div>

      <div className="card">
        <h3>Data from Backend:</h3>
        {loading && <p>Loading...</p>}
        {error && <p style={{ color: '#ef4444' }}>Error: {error}</p>}
        {!loading && !error && (
          <table style={{ width: '100%', marginTop: '16px', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #646cff' }}>
                <th style={{ padding: '8px', textAlign: 'left' }}>ID</th>
                <th style={{ padding: '8px', textAlign: 'left' }}>Name</th>
                <th style={{ padding: '8px', textAlign: 'right' }}>Value</th>
              </tr>
            </thead>
            <tbody>
              {data.map(item => (
                <tr key={item.id} style={{ borderBottom: '1px solid #555' }}>
                  <td style={{ padding: '8px' }}>{item.id}</td>
                  <td style={{ padding: '8px' }}>{item.name}</td>
                  <td style={{ padding: '8px', textAlign: 'right' }}>{item.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <p className="read-the-docs">
        Frontend running on Vite + React | Backend running on FastAPI
      </p>
    </>
  )
}

export default App
