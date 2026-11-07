import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider, createBrowserRouter } from 'react-router-dom'
import { AuthProvider } from './auth/AuthProvider'
import { RequireAuth } from './auth/RequireAuth'
import '@fontsource/habibi/400.css'
import '@fontsource/hind-vadodara/400.css'
import '@fontsource/hind-vadodara/700.css'
import '@fontsource/inria-serif/400.css'
import '@fontsource/inria-serif/700.css'
import '@fontsource/saira-stencil-one/400.css'
import '@fontsource/space-mono/400.css'
import '@fontsource/space-mono/700.css'
import './index.css'
import { AppLayout } from './layout/AppLayout'
import { AuthCallbackPage } from './pages/AuthCallbackPage'
import { DashboardPage } from './pages/DashboardPage'
import { IndicatorDetailPage } from './pages/IndicatorDetailPage'
import { IndicatorsPage } from './pages/IndicatorsPage'
import { IngestionDetailPage } from './pages/IngestionDetailPage'
import { IngestionsPage } from './pages/IngestionsPage'
import { LoginPage } from './pages/LoginPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { SearchPage } from './pages/SearchPage'
import { SettingsPage } from './pages/SettingsPage'
import { SourceDetailPage } from './pages/SourceDetailPage'
import { SourcesPage } from './pages/SourcesPage'
import { VulnerabilitiesPage } from './pages/VulnerabilitiesPage'
import { VulnerabilityDetailPage } from './pages/VulnerabilityDetailPage'

// Mapa de pantallas del UI §2.
const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/auth/callback', element: <AuthCallbackPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: 'vulnerabilidades', element: <VulnerabilitiesPage /> },
          { path: 'vulnerabilidades/:cveId', element: <VulnerabilityDetailPage /> },
          { path: 'indicadores', element: <IndicatorsPage /> },
          { path: 'indicadores/:indicatorId', element: <IndicatorDetailPage /> },
          { path: 'buscar', element: <SearchPage /> },
          { path: 'fuentes', element: <SourcesPage /> },
          { path: 'fuentes/:sourceId', element: <SourceDetailPage /> },
          { path: 'ingestas', element: <IngestionsPage /> },
          { path: 'ingestas/:runId', element: <IngestionDetailPage /> },
          { path: 'configuracion', element: <SettingsPage /> },
        ],
      },
    ],
  },
  { path: '*', element: <NotFoundPage /> },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </StrictMode>,
)
