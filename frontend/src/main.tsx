import ReactDOM from 'react-dom/client'
import React from 'react'
import App from './App.tsx'
import './index.css'
import ErrorBoundary from './components/ui/ErrorBoundary'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)
