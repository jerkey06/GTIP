import { getReadiness, listSources } from '../api/endpoints'
import { DataBlock } from '../components/DataState'
import { useApi } from '../hooks/useApi'
import { useAuth } from '../auth/context'
import { PageHeader } from '../layout/AppLayout'
import { formatDate, formatInterval } from '../lib/format'

/** P-12. Solo lectura: la configuración vive en variables de entorno (ADD §18). */
export function SettingsPage() {
  const { user, logout } = useAuth()
  const health = useApi(getReadiness, [])
  const sources = useApi(listSources, [])

  return (
    <>
      <PageHeader title="Configuración técnica" />
      <div className="grid-2">
        <section className="panel">
          <h2>Estado del sistema</h2>
          <DataBlock state={health}>
            {(h) => (
              <dl className="details">
                <dt>API</dt>
                <dd>
                  <span className="badge green">Disponible</span>
                </dd>
                <dt>PostgreSQL</dt>
                <dd>
                  {h.database === 'ok' ? (
                    <span className="badge green">Conectado</span>
                  ) : (
                    <span className="badge red">Sin conexión</span>
                  )}
                </dd>
                <dt>Versión</dt>
                <dd>{h.version}</dd>
                <dt>Entorno</dt>
                <dd>
                  <code>{h.environment}</code>
                </dd>
              </dl>
            )}
          </DataBlock>
        </section>
        <section className="panel">
          <h2>Sesión</h2>
          <dl className="details">
            <dt>Usuario</dt>
            <dd>{user?.username}</dd>
            <dt>Último acceso</dt>
            <dd>{formatDate(user?.last_login_at)}</dd>
          </dl>
          <button type="button" className="btn" onClick={() => logout()}>
            Cerrar sesión
          </button>
          <h3>Enlaces</h3>
          <ul>
            <li>
              <a href="/docs" target="_blank" rel="noopener noreferrer">
                Documentación de la API (si está expuesta en este entorno)
              </a>
            </li>
            <li>
              <a href="https://github.com/jerkey06/GTIP" target="_blank" rel="noopener noreferrer">
                Repositorio
              </a>
            </li>
          </ul>
        </section>
      </div>
      <section className="panel">
        <h2>Fuentes y credenciales</h2>
        <p className="muted">Nunca se muestra el valor de una clave, solo si está configurada.</p>
        <DataBlock state={sources}>
          {(list) => (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Fuente</th>
                    <th>Habilitada</th>
                    <th>Clave</th>
                    <th>Frecuencia</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((s) => (
                    <tr key={s.id}>
                      <td>{s.name}</td>
                      <td>{s.is_enabled ? 'Sí' : `No — ${s.disabled_reason}`}</td>
                      <td>
                        {s.api_key_configured === null
                          ? 'No usa clave'
                          : s.api_key_configured
                            ? 'Configurada'
                            : s.requires_api_key
                              ? 'No configurada (obligatoria)'
                              : 'No configurada (opcional)'}
                      </td>
                      <td>{formatInterval(s.schedule_interval_minutes)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </DataBlock>
      </section>
    </>
  )
}
