import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ChakraProvider, createSystem, defaultConfig } from '@chakra-ui/react'
import { RouterProvider } from 'react-router-dom'
import { Box } from '@chakra-ui/react'
import { theme } from "./theme"
import router from './router.jsx'
import './index.css'

// Set background to dark mode by default
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ChakraProvider value={theme}>
      <Box minH="100vh">
        <RouterProvider router={router} />
      </Box>
    </ChakraProvider>
  </StrictMode>,
)

// Remopve the app loader element after the app has rendered
function removeAppLoader() {
  const el = document.getElementById('app-loader')
  if (!el) return
  el.style.transition = 'opacity 240ms ease'
  el.style.opacity = '0'
  setTimeout(() => el.remove(), 300)
}

// Run removal on next paint to ensure app is visible
requestAnimationFrame(() => requestAnimationFrame(removeAppLoader))
