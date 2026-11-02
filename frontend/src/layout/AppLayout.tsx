import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/context'

const NAV = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/vulnerabilidades', label: 'Vulnerabilidades' },
  { to: '/indicadores', label: 'Indicadores' },
  { to: '/buscar', label: 'Búsqueda' },
  { to: '/fuentes', label: 'Fuentes de inteligencia' },
  { to: '/ingestas', label: 'Historial de ingesta' },
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
          <img src="/favicon.svg" alt="" width="28" height="28" />
          <span>GTIP</span>
        </Link>
        <nav onClick={closeMenus}>
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end}>
              {item.label}
            </NavLink>
          ))}
          <hr />
          <NavLink to="/configuracion">Configuración técnica</NavLink>
        </nav>
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
