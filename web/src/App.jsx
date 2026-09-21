import { useState } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { setCredentials, logout } from './app/authSlice'
import { useLoginMutation } from './app/api'
import ApplyDashboard from './pages/ApplyDashboard'
import AnalystDashboard from './pages/AnalystDashboard'

function LoginScreen() {
  const dispatch = useDispatch()
  const [username, setUsername] = useState('analyst')
  const [password, setPassword] = useState('')
  const [login, { isLoading }] = useLoginMutation()
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    try {
      const res = await login({ username, password }).unwrap()
      dispatch(setCredentials(res))
    } catch (err) {
      // Deliberately uniform error text -- backend gives no signal about
      // which field was wrong (see AuthController.java).
      setError('Those details did not match an account.')
    }
  }

  return (
    <div className="login-wrap">
      <form className="card login-card" onSubmit={handleSubmit}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--accent)', boxShadow: '0 0 10px var(--accent)' }} />
          <h1 style={{ margin: 0 }}>VIGIL</h1>
        </div>
        <p className="muted" style={{ marginTop: 0, marginBottom: 18 }}>
          Real-time fraud decisioning for Indian digital lending
        </p>
        <div className="field">
          <label>Username</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} />
        </div>
        <div className="field">
          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button className="primary" type="submit" disabled={isLoading} style={{ width: '100%' }}>
          {isLoading ? 'Signing in…' : 'Sign in'}
        </button>
        {error && <div className="error-text">{error}</div>}
        <p className="faint" style={{ marginTop: 16 }}>
          Demo accounts: <span className="mono">analyst</span> / <span className="mono">admin</span>
        </p>
      </form>
    </div>
  )
}

export default function App() {
  const { token, displayName, role } = useSelector((s) => s.auth)
  const dispatch = useDispatch()
  const [tab, setTab] = useState('apply')

  if (!token) return <LoginScreen />

  return (
    <div className="app-shell">
      <div className="topbar">
        <div className="brand">
          <span className="dot" />
          VIGIL
        </div>
        <nav>
          <button className={tab === 'apply' ? 'active' : ''} onClick={() => setTab('apply')}>
            Application
          </button>
          <button className={tab === 'analyst' ? 'active' : ''} onClick={() => setTab('analyst')}>
            Analyst
          </button>
        </nav>
        <div className="who">
          <span>{displayName} · {role}</span>
          <button onClick={() => dispatch(logout())}>Sign out</button>
        </div>
      </div>
      <div className="content">
        {tab === 'apply' ? <ApplyDashboard /> : <AnalystDashboard />}
      </div>
    </div>
  )
}
