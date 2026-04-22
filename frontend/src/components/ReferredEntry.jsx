import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import axios from 'axios'

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export default function ReferredEntry() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(Boolean(token))
  const started = useRef(false)

  useEffect(() => {
    if (!token) return

    if (started.current) return
    started.current = true

    const createSessionFromToken = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/sessions/referred`, {
          params: { token },
        })
        navigate(`/diagnostic/${res.data.session_id}`, { replace: true })
      } catch (err) {
        setError(err?.response?.data?.detail || 'This link has expired or is invalid')
        setLoading(false)
      }
    }

    createSessionFromToken()
  }, [navigate, token])

  if (!token) {
    return (
      <div className="container">
        <img src="/gensyn-logo.svg" alt="Gensyn" className="diagnostic-logo" />
        <div className="card">
          <h2>Unable to start diagnostic</h2>
          <p className="error">Missing referral token.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <img src="/gensyn-logo.svg" alt="Gensyn" className="diagnostic-logo" />
      <div className="card">
        {loading ? (
          <div className="loading">
            <div className="spinner" />
            <h2>Preparing your diagnostic</h2>
            <p>Verifying your referral link...</p>
          </div>
        ) : (
          <>
            <h2>Unable to start diagnostic</h2>
            <p className="error">{error}</p>
          </>
        )}
      </div>
    </div>
  )
}
