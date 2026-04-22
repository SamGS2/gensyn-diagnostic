import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import IntakeForm from './components/IntakeForm'
import Diagnostic from './components/Diagnostic'
import Results from './components/Results'
import ReferredEntry from './components/ReferredEntry'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/" element={<IntakeForm />} />
          <Route path="/referred" element={<ReferredEntry />} />
          <Route path="/diagnostic/:sessionId" element={<Diagnostic />} />
          <Route path="/results/:sessionId" element={<Results />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
