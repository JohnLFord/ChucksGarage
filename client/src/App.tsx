import { useEffect, useState } from 'react'
import {
  ChevronDown,
  CircleUserRound,
  ClipboardList,
  LogOut,
  Package,
  RefreshCw,
  Save,
  UsersRound,
  Wrench,
} from 'lucide-react'
import { apiRequest, type ApiResult } from './api'
import './App.css'

type Entity = Record<string, unknown> & { id: number }
type CrudMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'

type Resource = {
  id: string
  label: string
  icon: typeof UsersRound
  path: string
  template: string
  columns: string[]
}

const resources: Resource[] = [
  { id: 'customers', label: 'Customers', icon: UsersRound, path: '/customers/', template: '{\n  "name": "New Customer",\n  "email": "customer@example.com",\n  "date_of_birth": "1990-01-01"\n}', columns: ['id', 'name', 'email', 'date_of_birth'] },
  { id: 'mechanics', label: 'Mechanics', icon: Wrench, path: '/mechanics/', template: '{\n  "name": "Jordan Lee",\n  "specialty": "Diagnostics",\n  "experience": "7 years",\n  "certification": "ASE Certified"\n}', columns: ['id', 'name', 'specialty', 'experience', 'certification'] },
  { id: 'inventory', label: 'Inventory', icon: Package, path: '/inventory/', template: '{\n  "name": "Brake Pad Set",\n  "sku": "BR-100",\n  "stock_quantity": 12\n}', columns: ['id', 'name', 'sku', 'stock_quantity'] },
  { id: 'service-tickets', label: 'Service Tickets', icon: ClipboardList, path: '/service-tickets/', template: '{\n  "repair_date": "2026-08-18",\n  "customer_id": 1\n}', columns: ['id', 'repair_date', 'customer_id'] },
]

const actions: Array<{ method: CrudMethod; label: string }> = [
  { method: 'GET', label: 'Read' },
  { method: 'POST', label: 'Create' },
  { method: 'PUT', label: 'Update' },
  { method: 'DELETE', label: 'Delete' },
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
  const [method, setMethod] = useState<CrudMethod>('GET')
  const [expandedResourceId, setExpandedResourceId] = useState('customers')
  const [records, setRecords] = useState<Entity[]>([])
  const [recordId, setRecordId] = useState('')
  const [body, setBody] = useState(resources[0].template)
  const [activity, setActivity] = useState<ApiResult | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const resource = resources.find((item) => item.id === resourceId) ?? resources[0]
  const action = actions.find((item) => item.method === method) ?? actions[0]
  const isAdmin = user?.role === 'admin'
  const requiresRecordId = method === 'PUT' || method === 'DELETE'
  const endpoint = method === 'GET' || method === 'POST' ? resource.path : `${resource.path}${recordId || ':id'}`

  useEffect(() => {
    if (!token) return
    let cancelled = false
    async function loadSavedProfile() {
      try {
        const result = await apiRequest<Entity>('/users/me', 'GET', token)
        if (!cancelled) {
          setActivity(result)
          setUser(result.data)
        }
      } catch {
        if (!cancelled) logout()
      }
    }
    void loadSavedProfile()
    return () => { cancelled = true }
  }, [token])

  async function run<T>(path: string, requestMethod: CrudMethod, requestBody?: unknown) {
    setError('')
    setLoading(true)
    try {
      const result = await apiRequest<T>(path, requestMethod, token, requestBody)
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

  async function readRecords(nextResource = resource) {
    const data = await run<Entity[]>(nextResource.path, 'GET')
    if (data) setRecords(data)
  }

  function selectAction(nextResource: Resource, nextMethod: CrudMethod) {
    setResourceId(nextResource.id)
    setExpandedResourceId(nextResource.id)
    setMethod(nextMethod)
    setRecordId('')
    setBody(nextResource.template)
    setError('')
    if (nextMethod === 'GET') void readRecords(nextResource)
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

  async function submitAction(event: React.FormEvent) {
    event.preventDefault()
    if (method === 'GET') {
      await readRecords()
      return
    }
    if (requiresRecordId && !recordId) {
      setError('Enter a record ID for this action.')
      return
    }
    let payload: unknown
    if (method !== 'DELETE') {
      try { payload = JSON.parse(body) } catch {
        setError('Request JSON is not valid.')
        return
      }
    }
    if (method === 'DELETE' && !window.confirm(`Delete ${resource.label.slice(0, -1)} #${recordId}?`)) return
    const result = await run(endpoint, method, payload)
    if (result) await readRecords()
  }

  function logout() {
    localStorage.removeItem('cg_token')
    setToken('')
    setUser(null)
    setRecords([])
    setActivity(null)
  }

  if (!token || !user) {
    return <main className="login-shell"><section className="login-panel"><div className="brand-mark">CG</div><p className="eyebrow">Operations console</p><h1>Chucks Garage</h1><p className="subtle">Sign in to manage live garage records through the deployed API.</p><form onSubmit={login} className="login-form"><label>Email<input value={email} type="email" onChange={(event) => setEmail(event.target.value)} required /></label><label>Password<input value={password} type="password" onChange={(event) => setPassword(event.target.value)} required /></label>{error && <p className="form-error">{error}</p>}<button className="primary" disabled={loading}>{loading ? 'Signing in...' : 'Sign in'}</button></form><p className="login-note">Use the administrator account for create, update, and delete actions.</p></section></main>
  }

  return <div className="app-shell">
    <header className="topbar"><div className="brand"><div className="brand-mark">CG</div><span>Chucks Garage</span></div><div className="session"><CircleUserRound size={19} /><span>{String(user.email)}</span><span className="role-pill">{String(user.role)}</span><button onClick={logout} title="Sign out"><LogOut size={18} /></button></div></header>
    <aside className="sidebar"><p className="nav-label">CRUD workspace</p>{resources.map((item) => {
      const Icon = item.icon
      const expanded = item.id === expandedResourceId
      return <div key={item.id} className="nav-group"><button className={item.id === resourceId ? 'nav-item active' : 'nav-item'} onClick={() => setExpandedResourceId(expanded ? '' : item.id)}><Icon size={18} />{item.label}<ChevronDown className={expanded ? 'chevron open' : 'chevron'} size={16} /></button>{expanded && <div className="nav-actions">{actions.map((itemAction) => <button key={itemAction.method} className={item.id === resourceId && method === itemAction.method ? 'nav-action selected' : 'nav-action'} onClick={() => selectAction(item, itemAction.method)}><span className={`nav-method ${itemAction.method.toLowerCase()}`}>{itemAction.method}</span><span>{itemAction.label}</span></button>)}</div>}</div>
    })}<div className="sidebar-footer"><span className="live-dot" />Connected to Render</div></aside>
    <main className="workspace"><section className="page-heading"><div><p className="eyebrow">{action.label} / {method}</p><h1>{resource.label}</h1><p className="subtle">Choose an action in the sidebar, then run the live request below.</p></div><button className="secondary" onClick={() => readRecords()} disabled={loading}><RefreshCw size={17} />Read records</button></section>
      <section className="data-card"><div className="card-title"><div><h2>{resource.label} table</h2><span>{records.length} loaded record{records.length === 1 ? '' : 's'}</span></div><button className="secondary compact" onClick={() => readRecords()} disabled={loading}><RefreshCw size={16} /></button></div>{records.length === 0 ? <div className="empty-state"><Package size={25} /><p>No records loaded yet.</p><button className="text-button" onClick={() => readRecords()}>Read {resource.label.toLowerCase()}</button></div> : <div className="table-wrap"><table><thead><tr>{resource.columns.map((column) => <th key={column}>{column.replaceAll('_', ' ')}</th>)}</tr></thead><tbody>{records.map((record) => <tr key={record.id}>{resource.columns.map((column) => <td key={column}>{String(record[column] ?? '—')}</td>)}</tr>)}</tbody></table></div>}</section>
      <div className="work-grid"><section className="data-card request-card"><div className="card-title"><div><h2>{action.label} {resource.label}</h2><span>Send a {method} request</span></div><span className={`method-badge ${method.toLowerCase()}`}>{method}</span></div><form onSubmit={submitAction}><label className="endpoint"><span>Endpoint</span><code>{endpoint}</code></label>{requiresRecordId && <label className="record-id">Record ID<input value={recordId} inputMode="numeric" placeholder="e.g. 1" onChange={(event) => setRecordId(event.target.value)} required /></label>}{method !== 'DELETE' && <label className="json-label">Request JSON<textarea value={body} onChange={(event) => setBody(event.target.value)} spellCheck="false" /></label>}{error && <p className="form-error">{error}</p>}<button className="primary" disabled={loading || (method !== 'GET' && !isAdmin)}>{method === 'GET' ? <RefreshCw size={17} /> : <Save size={17} />}{method === 'GET' ? `Read ${resource.label}` : !isAdmin ? 'Administrator access required' : `${action.label} ${resource.label.slice(0, -1)}`}</button></form></section>
        <section className="data-card response-card"><div className="card-title"><div><h2>API activity</h2><span>Request and response proof</span></div>{activity && <span className={activity.status < 400 ? 'status ok' : 'status fail'}>{activity.status}</span>}</div>{activity ? <><div className="request-line"><span className="method">{activity.method}</span><code>{activity.path}</code></div>{activity.requestBody !== undefined && <pre className="request-json">{pretty(activity.requestBody)}</pre>}<pre>{pretty(activity.data)}</pre></> : <div className="empty-state"><ClipboardList size={25} /><p>Choose a CRUD action to inspect its live API response.</p></div>}</section>
      </div></main>
  </div>
}

export default App
