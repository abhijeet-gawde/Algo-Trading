import { useEffect, useState } from 'react'
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Check,
  ChevronRight,
  CircleHelp,
  Fingerprint,
  KeyRound,
  LayoutDashboard,
  LoaderCircle,
  LockKeyhole,
  LogOut,
  RefreshCw,
  ShieldCheck,
  UserRound,
  WalletCards,
} from 'lucide-react'
import { getProfile, getSession, login, logout } from './api.js'

const tabs = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'user', label: 'User', icon: UserRound },
  { id: 'activity', label: 'Activity', icon: Activity },
]

function Brand({ compact = false }) {
  return (
    <a className={`brand${compact ? ' brand-compact' : ''}`} href="#home" aria-label="Kite Desk home">
      <span className="brand-mark" aria-hidden="true"><span /></span>
      <span className="brand-name">kite<span>desk</span></span>
    </a>
  )
}

function LoginScreen({ onLogin }) {
  const [credentials, setCredentials] = useState({ api_key: '', api_secret: '', request_token: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function update(field, value) {
    setCredentials((current) => ({ ...current, [field]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(credentials)
      onLogin()
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="login-page">
      <header className="login-header"><Brand /><span className="local-indicator"><span /> LOCAL WORKSPACE</span></header>
      <div className="login-layout">
        <section className="login-intro">
          <div className="eyebrow"><span className="eyebrow-line" /> KITE CONNECT · PERSONAL DESK</div>
          <h1>Your market,<br />in <em>clear view.</em></h1>
          <p className="intro-copy">A quiet workspace for your Kite account. Sign in once, then pick up right where you left off.</p>
          <div className="intro-rule" />
          <div className="security-note">
            <span className="security-icon"><ShieldCheck size={19} strokeWidth={1.7} /></span>
            <div><strong>Private by design</strong><span>Your access token stays on this machine. It is never sent to the browser.</span></div>
          </div>
          <div className="market-stamp"><span>KC</span><span>CONNECTED TO<br />ZERODHA KITE</span></div>
        </section>

        <section className="login-panel" aria-labelledby="login-title">
          <div className="panel-heading">
            <span className="panel-icon"><KeyRound size={19} /></span>
            <span className="eyebrow">ACCOUNT ACCESS</span>
          </div>
          <h2 id="login-title">Connect your account</h2>
          <p className="panel-subtitle">Enter your Kite Connect credentials to continue.</p>
          <form className="login-form" onSubmit={handleSubmit}>
            <label className="field-label" htmlFor="api-key">API key</label>
            <input id="api-key" autoComplete="off" required value={credentials.api_key} onChange={(event) => update('api_key', event.target.value)} placeholder="Your Kite Connect API key" />
            <label className="field-label" htmlFor="api-secret">API secret</label>
            <input id="api-secret" type="password" autoComplete="new-password" required value={credentials.api_secret} onChange={(event) => update('api_secret', event.target.value)} placeholder="Your Kite Connect API secret" />
            <label className="field-label" htmlFor="request-token">Request token</label>
            <input id="request-token" autoComplete="off" required value={credentials.request_token} onChange={(event) => update('request_token', event.target.value)} placeholder="Paste the token from your redirect URL" />
            {error && <div className="form-error" role="alert">{error}</div>}
            <button className="primary-button login-submit" type="submit" disabled={submitting}>
              {submitting ? <><LoaderCircle className="spin" size={17} /> Connecting securely</> : <>Connect to Kite <ChevronRight size={17} /></>}
            </button>
          </form>
          <div className="form-footnote"><LockKeyhole size={13} /><span>Credentials are used only to create your session.</span></div>
        </section>
      </div>
      <footer className="login-footer"><span>FOR PERSONAL LOCAL DEVELOPMENT</span><span>ZERODHA KITE CONNECT</span></footer>
    </main>
  )
}

function Dashboard({ onLogout }) {
  const [activeTab, setActiveTab] = useState('user')
  const [profile, setProfile] = useState(null)
  const [profileError, setProfileError] = useState('')
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [loggingOut, setLoggingOut] = useState(false)

  async function loadProfile() {
    setLoadingProfile(true)
    setProfileError('')
    try {
      setProfile(await getProfile())
    } catch (error) {
      setProfileError(error.message)
      if (error.message.includes('expired') || error.message.includes('Log in')) onLogout()
    } finally {
      setLoadingProfile(false)
    }
  }

  useEffect(() => { loadProfile() }, [])

  async function handleLogout() {
    setLoggingOut(true)
    try {
      await logout()
    } finally {
      onLogout()
    }
  }

  return (
    <main className="dashboard-shell">
      <aside className="sidebar">
        <Brand compact />
        <div className="sidebar-caption">WORKSPACE</div>
        <nav className="side-nav" aria-label="Dashboard tabs">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button key={id} className={`nav-item${activeTab === id ? ' is-active' : ''}`} onClick={() => setActiveTab(id)} aria-current={activeTab === id ? 'page' : undefined}>
              <Icon size={17} strokeWidth={1.8} /><span>{label}</span>{activeTab === id && <span className="nav-active-mark" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="session-card"><span className="session-check"><Check size={13} /></span><div><strong>Session active</strong><span>Private connection</span></div></div>
          <button className="nav-item logout-item" onClick={handleLogout} disabled={loggingOut}><LogOut size={17} /><span>{loggingOut ? 'Signing out…' : 'Sign out'}</span></button>
          <div className="sidebar-version">KITE DESK <span>·</span> LOCAL</div>
        </div>
      </aside>

      <section className="dashboard-main">
        <header className="topbar">
          <div className="breadcrumb">Workspace <ChevronRight size={14} /><strong>{tabs.find((tab) => tab.id === activeTab)?.label}</strong></div>
          <div className="topbar-right"><span className="market-status"><i /> KITE CONNECTED</span><span className="avatar">{profile?.user_name?.slice(0, 1)?.toUpperCase() || 'K'}</span></div>
        </header>
        <div className="content-wrap">
          {activeTab === 'user' && <UserTab profile={profile} error={profileError} loading={loadingProfile} onRetry={loadProfile} />}
          {activeTab === 'overview' && <OverviewTab profile={profile} loading={loadingProfile} onOpenUser={() => setActiveTab('user')} />}
          {activeTab === 'activity' && <ActivityTab />}
        </div>
      </section>
    </main>
  )
}

function PageHeading({ eyebrow, title, description, action }) {
  return (
    <div className="page-heading">
      <div><div className="eyebrow"><span className="eyebrow-line" />{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>
      {action}
    </div>
  )
}

function UserTab({ profile, error, loading, onRetry }) {
  return <>
    <PageHeading eyebrow="ACCOUNT" title="Your profile" description="Identity and permissions for your Kite Connect account." action={<button className="icon-button" onClick={onRetry} aria-label="Refresh profile" title="Refresh profile"><RefreshCw size={16} /></button>} />
    {loading ? <div className="loading-state"><LoaderCircle className="spin" size={21} /><span>Loading account profile…</span></div> : error ? (
      <div className="error-state" role="alert"><CircleHelp size={19} /><div><strong>Could not load your profile</strong><span>{error}</span></div><button className="text-button" onClick={onRetry}>Try again</button></div>
    ) : profile && <>
      <section className="profile-banner"><div className="profile-monogram">{profile.user_name?.slice(0, 1)?.toUpperCase() || 'K'}</div><div><div className="eyebrow">KITE CONNECT USER</div><h2>{profile.user_name || 'Kite user'}</h2><span className="profile-id"><Fingerprint size={14} /> {profile.user_id || 'No user ID available'}</span></div><span className="verified-badge"><Check size={13} /> VERIFIED</span></section>
      <div className="section-label"><span>ACCOUNT DETAILS</span><span>01 — 03</span></div>
      <div className="detail-grid">
        <article className="detail-item"><div className="detail-top"><span className="detail-icon"><Fingerprint size={16} /></span><span className="detail-label">USER ID</span></div><strong className="detail-value mono">{profile.user_id || '—'}</strong><span className="detail-hint">Your unique Kite identifier</span></article>
        <article className="detail-item"><div className="detail-top"><span className="detail-icon"><WalletCards size={16} /></span><span className="detail-label">PRODUCTS</span></div><div className="tag-list">{profile.products?.length ? profile.products.map((product) => <span className="data-tag" key={product}>{product}</span>) : <span className="empty-value">No products listed</span>}</div><span className="detail-hint">Enabled trading products</span></article>
        <article className="detail-item"><div className="detail-top"><span className="detail-icon"><Activity size={16} /></span><span className="detail-label">EXCHANGES</span></div><div className="tag-list">{profile.exchanges?.length ? profile.exchanges.map((exchange) => <span className="data-tag exchange-tag" key={exchange}>{exchange}</span>) : <span className="empty-value">No exchanges listed</span>}</div><span className="detail-hint">Available market venues</span></article>
      </div>
      <div className="privacy-strip"><LockKeyhole size={15} /><span>Your profile is fetched directly from Kite Connect. No access token is exposed to this page.</span></div>
    </>}
  </>
}

function OverviewTab({ profile, loading, onOpenUser }) {
  return <>
    <PageHeading eyebrow="MONDAY, YOUR KITE WORKSPACE" title={`Good to see you${profile?.user_name ? `, ${profile.user_name.split(' ')[0]}` : ''}.`} description="Your account connection is ready. Here’s a quick look at your workspace." />
    <div className="overview-status"><div className="overview-status-icon"><ShieldCheck size={22} /></div><div><span className="eyebrow">CONNECTION STATUS</span><h2>Everything is connected.</h2><p>Your Kite session is securely stored on this machine.</p></div><span className="status-live"><i /> LIVE SESSION</span></div>
    <div className="section-label"><span>ACCOUNT SNAPSHOT</span><span>01 — 02</span></div>
    <div className="snapshot-grid"><button className="snapshot-item" onClick={onOpenUser}><span className="detail-top"><span className="detail-icon"><UserRound size={16} /></span><span className="detail-label">KITE PROFILE</span><ChevronRight size={16} className="snapshot-arrow" /></span><strong>{loading ? 'Loading…' : profile?.user_name || 'View profile'}</strong><span className="detail-hint">Identity and account details</span></button><div className="snapshot-item static-snapshot"><span className="detail-top"><span className="detail-icon"><WalletCards size={16} /></span><span className="detail-label">TRADING PRODUCTS</span></span><strong>{loading ? '—' : profile?.products?.length ?? 0}</strong><span className="detail-hint">Products enabled on your account</span></div></div>
    <div className="market-note"><span className="note-glyph"><ArrowUpRight size={18} /></span><p><strong>Connected locally.</strong> Kite account data is fetched only when you open your workspace and is never stored in the browser.</p><span className="note-mark">KD / 01</span></div>
  </>
}

function ActivityTab() {
  return <>
    <PageHeading eyebrow="WORKSPACE" title="Activity" description="A simple view of recent account activity in this workspace." />
    <section className="empty-activity"><div className="empty-graphic"><ArrowDownRight size={26} /></div><span className="eyebrow">NOTHING TO REVIEW</span><h2>No activity yet</h2><p>When this workspace records account actions, they’ll appear here.</p></section>
  </>
}

export default function App() {
  const [authenticated, setAuthenticated] = useState(false)
  const [checkingSession, setCheckingSession] = useState(true)

  useEffect(() => {
    let active = true
    getSession()
      .then(({ authenticated: hasSession }) => { if (active) setAuthenticated(hasSession) })
      .catch(() => { if (active) setAuthenticated(false) })
      .finally(() => { if (active) setCheckingSession(false) })
    return () => { active = false }
  }, [])

  if (checkingSession) return <main className="boot-screen"><Brand /><span><LoaderCircle className="spin" size={17} /> Checking local session</span></main>
  return authenticated
    ? <Dashboard onLogout={() => setAuthenticated(false)} />
    : <LoginScreen onLogin={() => setAuthenticated(true)} />
}