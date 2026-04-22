import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export default function IntakeForm() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    organization: '',
    role: '',
    email: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await axios.post(`${API_URL}/api/sessions/`, form)
      navigate(`/diagnostic/${res.data.session_id}`)
    } catch (err) {
      setError('Something went wrong. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <img src="/gensyn-logo.svg" alt="Gensyn" className="intake-logo" />
      <div className="card">
        <h1>Organizational Diagnostic</h1>
        <p className="subtitle">
          Tell us a bit about yourself and your organization. We'll walk you through
          a few questions to understand your situation — it takes about 5 minutes.
        </p>

        {error && <p className="error">{error}</p>}

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>First name</label>
              <input name="first_name" value={form.first_name} onChange={handleChange} required placeholder="John" />
            </div>
            <div className="form-group">
              <label>Last name</label>
              <input name="last_name" value={form.last_name} onChange={handleChange} required placeholder="Smith" />
            </div>
          </div>

          <div className="form-group">
            <label>Organization</label>
            <input name="organization" value={form.organization} onChange={handleChange} required placeholder="Your company or organization" />
          </div>

          <div className="form-group">
            <label>Your role</label>
            <input name="role" value={form.role} onChange={handleChange} required placeholder="e.g. VP of Operations, Team Lead" />
          </div>

          <div className="form-group">
            <label>Email</label>
            <input name="email" type="email" value={form.email} onChange={handleChange} required placeholder="you@company.com" />
          </div>

          <button type="submit" disabled={loading}>
            {loading ? 'Getting things ready...' : 'Start Diagnostic'}
          </button>
        </form>
      </div>
      <p className="footer">Powered by <a href="https://www.gensyndesign.com" target="_blank" rel="noopener">Gensyn Design</a></p>
    </div>
  )
}