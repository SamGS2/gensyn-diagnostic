import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export default function Results() {
  const { sessionId } = useParams()
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const res = await axios.post(`${API_URL}/api/diagnostic/analyze`, {
          session_id: sessionId,
          mode: 'public',
        })
        setAnalysis(res.data)
      } catch (err) {
        setError('Failed to generate analysis. Please try again.')
      }
      setLoading(false)
    }
    fetchAnalysis()
  }, [sessionId])

  if (loading) {
    return (
      <div className="container">
        <img src="/gensyn-logo.svg" alt="Gensyn" className="results-logo" />
        <div className="card">
          <div className="loading">
            <div className="spinner" />
            <h2>Analyzing your responses</h2>
            <p>We're putting together a personalized assessment. This usually takes 10–15 seconds.</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container">
        <img src="/gensyn-logo.svg" alt="Gensyn" className="results-logo" />
        <div className="card">
          <p className="error">{error}</p>
        </div>
      </div>
    )
  }

  if (!analysis) return null

  return (
    <div className="container">
      <img src="/gensyn-logo.svg" alt="Gensyn" className="results-logo" />
      <div className="card results">
        <h1>Your Diagnostic Results</h1>
        <p className="results-intro">
          Based on what you shared, here's our assessment of your situation and what we'd recommend.
        </p>

        <div className="result-section">
          <h3>What We Heard</h3>
          <p>{analysis.problem_summary}</p>
        </div>

        <div className="result-section">
          <h3>Type of Challenge</h3>
          <span className="problem-type">{analysis.problem_type} problem</span>
          <p>{analysis.problem_type_explanation}</p>
        </div>

        <div className="result-section">
          <h3>Our Analysis</h3>
          <p>{analysis.analysis}</p>
        </div>

        {analysis.workshop_recommendation && (
          <div className="result-section recommendation">
            <h3>What We'd Recommend</h3>
            <p className="workshop-name">{analysis.workshop_recommendation}</p>
            <p>{analysis.recommendation_explanation}</p>
          </div>
        )}

        {analysis.suggested_next_steps && analysis.suggested_next_steps.length > 0 && (
          <div className="result-section">
            <h3>Suggested Next Steps</h3>
            <ul>
              {analysis.suggested_next_steps.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="cta-section">
          <p>Want to explore how we can help? Let's start a conversation.</p>
          <a href="https://www.gensyndesign.com" className="cta-btn" target="_blank" rel="noopener">
            Get in Touch
          </a>
        </div>
      </div>
      <p className="footer">© 2026 <a href="https://www.gensyndesign.com" target="_blank" rel="noopener">Gensyn Design</a></p>
    </div>
  )
}