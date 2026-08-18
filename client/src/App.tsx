import { useEffect, useState } from 'react'
import {
  CircleUserRound,
  ClipboardList,
  LogOut,
  Package,
  RefreshCw,
  Save,
  Trash2,
  UsersRound,
  Wrench,
} from 'lucide-react'
import { apiRequest, type ApiResult } from './api'
import './App.css'

type Entity = Record<string, unknown> & { id: number }

type Resource = {
  id: string
  label: string
  icon: typeof UsersRound
  path: string
  createTemplate: string
  columns: string[]
}

const resources: Resource[] = [
  {
    id: 'customers',
    label: 'Customers',
    icon: UsersRound,
    path: '/customers/',
    createTemplate: '{\n  "name": "New Customer",\n  "email": "customer@example.com",\n  "date_of_birth": "1990-01-01"\n}',
    columns: ['id', 'name', 'email', 'date_of_birth'],
  },
  {
    id: 'mechanics',
    label: 'Mechanics',
    icon: Wrench,
    path: '/mechanics/',
    createTemplate: '{\n  "name": "Jordan Lee",\n  "specialty": "Diagnostics",\n  "experience": "7 years",\n  "certification": "ASE Certified"\n}',
    columns: ['id', 'name', 'specialty', 'experience', 'certification'],
  },
  {
    id: 'inventory',
    label: 'Inventory',
    icon: Package,
    path: '/inventory/',
    createTemplate: '{\n  "name": "Brake Pad Set",\n  "sku": "BR-100",\n  "stock_quantity": 12\n}',
    columns: ['id', 'name', 'sku', 'stock_quantity'],
  },
  {
    id: 'service-tickets',
    label: 'Service Tickets',
    icon: ClipboardList,
    path: '/service-tickets/',
    createTemplate: '{\n  "repair_date": "2026-08-18",\n  "customer_id": 1\n}',
    columns: ['id', 'repair_date', 'customer_id'],
  },
]

function pretty(value: unknown) {
  return JSON.stringify(value, null, 2)
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('cg_token') ?? '')
  const [user, setUser] = useState<Entity | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [resourceId, setResourceId] = useState('customers')
  const [records, setRecords] = useState<Entity[]>([])
  const [body, setBody] = useState(resources[0].createTemplate)
  const [activity, setActivity] = useState<ApiResult | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const resource = resources.find((item) => item.id === resourceId) ?? resources[0]
  const isAdmin = user?.role === 'admin'

  useEffect(() => {
    setBody(resource.createTemplate)
  }, [resource])

  useEffect(() => {
    if (token) void loadProfile()
  }, [])

  async function run<T>(path: string, method: string, requestBody?: unknown): Promise<T | null> {
    setError('')
    setLoading(true)
    try {
      const result = await apiRequest<T>(path, method, token, requestBody)
      setActivity(result)
      return result.data
    } catch (requestError) {
      const errorWithResult = requestError as Error & { result?: ApiResult }
      if (errorWithResult.result) setActivity(errorWithResult.result)
      setError(errorWithResult.message)
      return null
    } finally {
      setLoading(false)
    }
  }

  async function loadProfile() {
    const profile = await run<Entity>('/users/me', 'GET')
    if (profile) setUser(profile)
  }

  async function loadRecords() {
    const data = await run<Entity[]>(resource.path, 'GET')
    if (data) setRecords(data)
  }

  async function login(event: React.FormEvent) {
    event.preventDefault()
    const result = await run<{ auth_token: string }>('/users/login', 'POST', { email, password })
    if (!result) return
    localStorage.setItem('cg_token', result.auth_token)
    setToken(result.auth_token)
    setPassword('')
    const profile = await apiRequest<Entity>('/users/me', 'GET', result.auth_token)
    setActivity(profile)
    setUser(profile.data)
  }

  async function createRecord(event: React.FormEvent) {
    event.preventDefault()
    let payload: unknown
    try {
      payload = JSON.parse(body)
    } catch {
      setError('Request JSON is not valid.')
      return
    }
    const created = await run(resource.path, 'POST', payload)
    if (created) await loadRecords()
  }

  async function deleteRecord(record: Entity) {
    if (!window.confirm(`Delete ${resource.label.slice(0, -1)} #${record.id}?`)) return
    const deleted = await run(`${resource.path}${record.id}`, 'DELETE')
    if (deleted) await loadRecords()
  }

  function logout() {
    localStorage.removeItem('cg_token')
    setToken('')
    setUser(null)
    setRecords([])
    setActivity(null)
  }

  if (!token || !user) {
    return (
      <main className="login-shell">
        <section className="login-panel">
          <div className="brand-mark">CG</div>
          <p className="eyebrow">Operations console</p>
          <h1>Chucks Garage</h1>
          <p className="subtle">Sign in to manage live garage records through the deployed API.</p>
          <form onSubmit={login} className="login-form">
            <label>Email<input value={email} type="email" onChange={(event) => setEmail(event.target.value)} required /></label>
            <label>Password<input value={password} type="password" onChange={(event) => setPassword(event.target.value)} required /></label>
            {error && <p className="form-error">{error}</p>}
            <button className="primary" disabled={loading}>{loading ? 'Signing in...' : 'Sign in'}</button>
          </form>
          <p className="login-note">Use the administrator account for create and delete actions.</p>
        </section>
      </main>
    )
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand"><div className="brand-mark">CG</div><span>Chucks Garage</span></div>
        <div className="session"><CircleUserRound size={19} /><span>{String(user.email)}</span><span className="role-pill">{String(user.role)}</span><button onClick={logout} title="Sign out"><LogOut size={18} /></button></div>
      </header>
      <aside className="sidebar">
        <p className="nav-label">Live data</p>
        {resources.map((item) => {
          const Icon = item.icon
          return <button key={item.id} className={item.id === resourceId ? 'nav-item active' : 'nav-item'} onClick={() => setResourceId(item.id)}><Icon size={18} />{item.label}</button>
        })}
        <div className="sidebar-footer"><span className="live-dot" />Connected to Render</div>
      </aside>
      <main className="workspace">
        <section className="page-heading">
          <div><p className="eyebrow">Database workspace</p><h1>{resource.label}</h1><p className="subtle">Live records returned from the Chucks Garage API.</p></div>
          <button className="secondary" onClick={loadRecords} disabled={loading}><RefreshCw size={17} />Refresh</button>
        </section>
        <section className="data-card">
          <div className="card-title"><div><h2>{resource.label} table</h2><span>{records.length} loaded record{records.length === 1 ? '' : 's'}</span></div><button className="secondary compact" onClick={loadRecords} disabled={loading}><RefreshCw size={16} /></button></div>
          {records.length === 0 ? <div className="empty-state"><Package size={25} /><p>No records loaded yet.</p><button className="text-button" onClick={loadRecords}>Load {resource.label.toLowerCase()}</button></div> : <div className="table-wrap"><table><thead><tr>{resource.columns.map((column) => <th key={column}>{column.replaceAll('_', ' ')}</th>)}<th aria-label="Actions" /></tr></thead><tbody>{records.map((record) => <tr key={record.id}>{resource.columns.map((column) => <td key={column}>{String(record[column] ?? '—')}</td>)}<td>{isAdmin && <button className="icon-danger" onClick={() => deleteRecord(record)} title={`Delete ${resource.label.slice(0, -1)}`}><Trash2 size={16} /></button>}</td></tr>)}</tbody></table></div>}
        </section>
        <div className="work-grid">
          <section className="data-card request-card">
            <div className="card-title"><div><h2>Run a CRUD action</h2><span>Post JSON to the selected resource</span></div><span className="method-badge">POST</span></div>
            <form onSubmit={createRecord}><label className="endpoint"><span>Endpoint</span><code>{resource.path}</code></label><label className="json-label">Request JSON<textarea value={body} onChange={(event) => setBody(event.target.value)} spellCheck="false" /></label>{error && <p className="form-error">{error}</p>}<button className="primary" disabled={loading || !isAdmin}><Save size={17} />{isAdmin ? `Create ${resource.label.slice(0, -1)}` : 'Administrator access required'}</button></form>
          </section>
          <section className="data-card response-card">
            <div className="card-title"><div><h2>API activity</h2><span>Request and response proof</span></div>{activity && <span className={activity.status < 400 ? 'status ok' : 'status fail'}>{activity.status}</span>}</div>
            {activity ? <><div className="request-line"><span className="method">{activity.method}</span><code>{activity.path}</code></div>{activity.requestBody !== undefined && <pre className="request-json">{pretty(activity.requestBody)}</pre>}<pre>{pretty(activity.data)}</pre></> : <div className="empty-state"><ClipboardList size={25} /><p>Run an action to inspect the live API response.</p></div>}
          </section>
        </div>
      </main>
    </div>
  )
}

export default App
