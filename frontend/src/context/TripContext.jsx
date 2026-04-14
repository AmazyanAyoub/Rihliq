import { createContext, useContext, useState } from 'react'

const TripContext = createContext(null)

const STEPS = [
  { id: 'parsing',     label: 'Parsing your trip details...' },
  { id: 'flights',     label: 'Searching flights...' },
  { id: 'hotels',      label: 'Finding hotels...' },
  { id: 'restaurants', label: 'Loading restaurants...' },
  { id: 'done',        label: 'Done!' },
]

export function TripProvider({ children }) {
  const [tripDetails, setTripDetails]     = useState(null)
  const [flights, setFlights]             = useState([])
  const [hotels, setHotels]               = useState([])
  const [restaurants, setRestaurants]     = useState([])
  const [isLoading, setIsLoading]         = useState(false)
  const [error, setError]                 = useState(null)
  const [currentStep, setCurrentStep]     = useState(null)

  const reset = () => {
    setFlights([])
    setHotels([])
    setRestaurants([])
    setError(null)
    setCurrentStep(null)
  }

  return (
    <TripContext.Provider value={{
      tripDetails, setTripDetails,
      flights,     setFlights,
      hotels,      setHotels,
      restaurants, setRestaurants,
      isLoading,   setIsLoading,
      error,       setError,
      currentStep, setCurrentStep,
      steps: STEPS,
      reset,
    }}>
      {children}
    </TripContext.Provider>
  )
}

export function useTripContext() {
  const ctx = useContext(TripContext)
  if (!ctx) throw new Error('useTripContext must be used inside <TripProvider>')
  return ctx
}
