import { Link } from 'react-router-dom'

/** P-13. Sin sesión, «Ir al dashboard» acaba en el login. */
export function NotFoundPage() {
  return (
    <div className="fullscreen-center">
      <div className="state">
        <h1>Esta página no existe.</h1>
        <Link to="/" className="btn btn-primary">
          Ir al dashboard
        </Link>
      </div>
    </div>
  )
}
