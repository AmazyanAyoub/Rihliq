import { Routes, Route } from 'react-router-dom'
import { TripProvider } from './context/TripContext'
import Navbar from './components/Navbar'
import HomePage from './pages/HomePage'
import ResultsPage from './pages/ResultsPage'
import ChatPage from './pages/ChatPage'

export default function App() {
  return (
    <TripProvider>
      <div className="min-h-screen bg-slate-900">
        <Navbar />
        <Routes>
          <Route path="/"        element={<HomePage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/chat"    element={<ChatPage />} />
        </Routes>
      </div>
    </TripProvider>
  )
}
