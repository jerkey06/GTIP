import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/context'

const svg = {
  width: 24,
  height: 24,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  'aria-hidden': true,
}

// Íconos provisionales con el estilo del diseño; se pueden cambiar por los SVG de Figma.
const ICONS = {
  dashboard: (
    <svg {...svg}>
      <path d="M3 3v18h18" />
      <path d="m7 15 4-4 3 3 5-6" />
    </svg>
  ),
  shield: (
    <svg {...svg}>
      <path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z" />
      <path d="M12 8v5M12 16v.01" />
    </svg>
  ),
  target: (
    <svg {...svg}>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1" />
    </svg>
  ),
  search: (
    <svg {...svg}>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  ),
  globe: (
    <svg {...svg}>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" />
    </svg>
  ),
  history: (
    <svg {...svg}>
      <path d="M5 3h14v18H5z" />
      <path d="M9 8h6M9 12h6M9 16h4" />
    </svg>
  ),
  settings: (
    <svg {...svg}>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2" />
    </svg>
  ),
  user: (
    <svg {...svg}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c1-4 4-6 8-6s7 2 8 6" />
    </svg>
  ),
}

const NAV = [
  { to: '/', label: 'Dashboard', end: true, icon: ICONS.dashboard },
  { to: '/vulnerabilidades', label: 'Vulnerabilidades', icon: ICONS.shield },
  { to: '/indicadores', label: 'Indicadores', icon: ICONS.target },
  { to: '/buscar', label: 'Búsqueda', icon: ICONS.search },
  { to: '/fuentes', label: 'Fuentes de inteligencia', icon: ICONS.globe },
  { to: '/ingestas', label: 'Historial de ingesta', icon: ICONS.history },
]

/** Layout autenticado: menú lateral y barra superior con búsqueda global (UI §3.1). */
export function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  const closeMenus = () => {
    setMenuOpen(false)
    setUserMenuOpen(false)
  }

  const submitSearch = (event: React.FormEvent) => {
    event.preventDefault()
    const q = query.trim()
    if (q) {
      closeMenus()
      navigate(`/buscar?q=${encodeURIComponent(q)}`)
    }
  }

  return (
    <div className={`app ${menuOpen ? 'menu-open' : ''}`}>
      <aside className="sidebar" aria-label="Navegación principal">
        <Link to="/" className="brand" onClick={closeMenus}>
          <span>GTIP</span>
        </Link>
        <nav onClick={closeMenus}>
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end}>
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}
          <NavLink to="/configuracion">
            {ICONS.settings}
            <span>Configuración técnica</span>
          </NavLink>
        </nav>
        <div className="sidebar-logo">
          <img src="/logo.svg" alt="" />
        </div>
      </aside>
      <div className="sidebar-backdrop" onClick={() => setMenuOpen(false)} aria-hidden="true" />

      <div className="main">
        <header className="topbar">
          <button
            type="button"
            className="btn btn-ghost menu-button"
            aria-label="Abrir menú"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
          >
            ☰
          </button>
          <form className="global-search" role="search" onSubmit={submitSearch}>
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar CVE, IP, dominio, URL o hash…"
              aria-label="Búsqueda global"
            />
          </form>
          <div className="user-menu">
            <button
              type="button"
              className="btn btn-ghost"
              aria-haspopup="menu"
              aria-expanded={userMenuOpen}
              onClick={() => setUserMenuOpen((open) => !open)}
            >
              <span className="avatar">{ICONS.user}</span>
              {user?.username ?? 'usuario'} ▾
            </button>
            {userMenuOpen && (
              <div className="dropdown" role="menu">
                <Link to="/configuracion" role="menuitem" onClick={closeMenus}>
                  Configuración
                </Link>
                <button type="button" role="menuitem" onClick={() => logout()}>
                  Cerrar sesión
                </button>
              </div>
            )}
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export function PageHeader({
  title,
  crumbs,
  actions,
  children,
}: {
  title: React.ReactNode
  crumbs?: { to: string; label: string }[]
  actions?: React.ReactNode
  children?: React.ReactNode
}) {
  return (
    <div className="page-header">
      {crumbs && (
        <nav className="crumbs" aria-label="Migas de pan">
          {crumbs.map((c) => (
            <span key={c.to}>
              <Link to={c.to}>{c.label}</Link> /{' '}
            </span>
          ))}
        </nav>
      )}
      <div className="page-title">
        <h1>{title}</h1>
        {actions && <div className="page-actions">{actions}</div>}
      </div>
      {children}
    </div>
  )
}
