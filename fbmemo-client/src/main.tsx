import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import "./assets/styles.css"
import App from './App'
import { AuthProvider } from './site_components/authcontext'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </StrictMode>,
)
