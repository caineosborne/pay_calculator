import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import 'https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
