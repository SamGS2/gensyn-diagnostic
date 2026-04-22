import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export default function Diagnostic() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [question, setQuestion] = useState(null)
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const fetchNextQuestion = async () => {
    setLoading(true)
    setAnswer('')
    setError(null)
    try {
      const res = await axios.post(`${API_URL}/api/diagnostic/next`, {
        session_id: sessionId,
      })
      if (res.data.complete) {
        navigate(`/results/${sessionId}`)
      } else {
        setQuestion(res.data.question)
      }
    } catch (err) {
      setError('Failed to load question. Please try again.')
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchNextQuestion()
  }, [])

  const handleSubmit = async () => {
    if (!answer.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      await axios.post(`${API_URL}/api/diagnostic/answer`, {
        session_id: sessionId,
        stage: question.stage,
        question_text: question.question_text,
        response_type: question.response_type,
        response_value: answer,
        options_presented: question.options,
      })
      await fetchNextQuestion()
    } catch (err) {
      setError('Failed to save answer. Please try again.')
    }
    setSubmitting(false)
  }

  if (loading) {
    return (
      <div className="container">
        <img src="/gensyn-logo.svg" alt="Gensyn" className="diagnostic-logo" />
        <div className="card">
          <div className="loading">
            <div className="spinner" />
            <h2>Preparing your next question</h2>
            <p>This won't take long.</p>
          </div>
        </div>
      </div>
    )
  }

  if (!question) return null

  const progress = ((question.stage - 1) / question.total_stages) * 100

  return (
    <div className="container">
      <img src="/gensyn-logo.svg" alt="Gensyn" className="diagnostic-logo" />
      <div className="card">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
        <p className="stage-label">
          Question {question.stage} of {question.total_stages}
        </p>

        <h2 className="question-text">{question.question_text}</h2>

        {error && <p className="error">{error}</p>}

        {question.response_type === 'selection' && question.options ? (
          <div className="options">
            {question.options.map((option, i) => (
              <button
                key={i}
                className={`option-btn ${answer === option ? 'selected' : ''}`}
                onClick={() => setAnswer(option)}
              >
                {option}
              </button>
            ))}
          </div>
        ) : (
          <textarea
            className="text-input"
            placeholder="Take your time — the more context you share, the more useful our analysis will be..."
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={5}
          />
        )}

        <button
          className="submit-btn"
          onClick={handleSubmit}
          disabled={!answer.trim() || submitting}
        >
          {submitting ? 'Saving...' : question.stage === question.total_stages ? 'Complete Diagnostic' : 'Continue'}
        </button>
      </div>
    </div>
  )
}