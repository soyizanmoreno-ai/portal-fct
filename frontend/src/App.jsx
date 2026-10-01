import { useEffect, useState } from 'react';
import {
  Bell, BriefcaseBusiness, Building2, ClipboardCheck, FileText, GraduationCap,
  LayoutDashboard, LogOut, Menu, Search, ShieldCheck, Users, X,
} from 'lucide-react';
import { api, requestJson } from './api';
import StudentWorkspace from './features/StudentWorkspace.jsx';
import CompanyWorkspace from './features/CompanyWorkspace.jsx';
import TutorAdminWorkspace from './features/TutorAdminWorkspace.jsx';

const NAVIGATION = {
  alumno: [
    { key: 'home', label: 'Resumen', icon: LayoutDashboard },
    { key: 'offers', label: 'Explorar ofertas', icon: Search },
    { key: 'applications', label: 'Candidaturas', icon: ClipboardCheck },
    { key: 'profile', label: 'Mi perfil', icon: GraduationCap },
    { key: 'hours', label: 'Horas FCT', icon: FileText },
  ],
  empresa: [
    { key: 'home', label: 'Resumen', icon: LayoutDashboard },
    { key: 'offers', label: 'Mis ofertas', icon: BriefcaseBusiness },
    { key: 'candidates', label: 'Candidaturas', icon: Users },
    { key: 'hours', label: 'Revisión FCT', icon: ClipboardCheck },
    { key: 'profile', label: 'Empresa', icon: Building2 },
  ],
  tutor: [
    { key: 'students', label: 'Alumnado', icon: GraduationCap },
    { key: 'reviews', label: 'Revisión FCT', icon: ClipboardCheck },
  ],
  admin: [{ key: 'users', label: 'Usuarios', icon: ShieldCheck }],
};

const ROLE_NAMES = { alumno: 'Alumno', empresa: 'Empresa', tutor: 'Tutor', admin: 'Administrador' };
const PAGE_TITLES = {
  home: 'Resumen', offers: 'Ofertas de prácticas', applications: 'Candidaturas', profile: 'Mi perfil',
  hours: 'Seguimiento FCT', candidates: 'Candidaturas recibidas', students: 'Alumnado tutorizado',
  reviews: 'Revisión de prácticas', users: 'Gestión de usuarios',
};

function AuthScreen({ onLogin }) {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      if (mode === 'register') {
        await requestJson('/users/', {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        });
      }
      const response = await api('/auth/login', {
        method: 'POST',
        body: new URLSearchParams({ username: email, password }),
      });
      const tokenData = await response.json();
      localStorage.setItem('fct_token', tokenData.access_token);
      await onLogin();
    } catch (reason) {
      setError(reason.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-rail">
        <div className="brand brand-large"><span className="brand-mark">F</span><span>portal<span className="brand-light">fct</span></span></div>
        <div className="auth-orbit" aria-hidden="true"><div className="orbit-line" /><span className="orbit-dot dot-one" /><span className="orbit-dot dot-two" /><span className="orbit-dot dot-three" /><strong>FCT</strong></div>
        <div className="auth-rail-bottom"><span>FORMACIÓN EN CENTROS DE TRABAJO</span><span>CURSO 2025 — 2026</span></div>
      </section>
      <section className="auth-main">
        <div className="auth-card">
          <span className="eyebrow">PORTAL DE PRÁCTICAS</span>
          <h1>{mode === 'login' ? 'Tu siguiente paso.' : 'Empieza aquí.'}</h1>
          <p className="auth-copy">Accede a tu espacio de prácticas FCT.</p>
          <form onSubmit={submit} className="form-stack">
            <label>Email<input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
            <label>Contraseña<input type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} minLength={mode === 'register' ? 12 : 1} value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="button button-primary button-wide" disabled={busy}>{busy ? 'Un momento…' : mode === 'login' ? 'Entrar' : 'Crear cuenta'}</button>
          </form>
          <div className="auth-switch">
            {mode === 'login' ? '¿Aún no tienes cuenta?' : '¿Ya tienes cuenta?'}{' '}
            <button className="text-button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}>
              {mode === 'login' ? 'Regístrate como alumno' : 'Inicia sesión'}
            </button>
          </div>
          <p className="auth-note">Empresas y tutores reciben sus credenciales del administrador.</p>
        </div>
      </section>
    </main>
  );
}

function NotificationPopover({ items, onRead, onClose }) {
  return (
    <div className="notification-popover">
      <div className="popover-heading"><strong>Notificaciones</strong><button className="icon-button" onClick={onClose} aria-label="Cerrar"><X size={17} /></button></div>
      {items.length === 0 ? <p className="empty-inline">No tienes notificaciones.</p> : items.slice(0, 8).map((item) => (
        <button key={item.id} className={`notification-item ${item.is_read ? '' : 'unread'}`} onClick={() => !item.is_read && onRead(item.id)}>
          <span className="notification-dot" /><span><strong>{item.title}</strong><small>{item.message}</small><time>{new Date(item.created_at).toLocaleDateString('es-ES')}</time></span>
        </button>
      ))}
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [page, setPage] = useState('home');
  const [notifications, setNotifications] = useState([]);
  const [notice, setNotice] = useState(null);
  const [showNotifications, setShowNotifications] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(Boolean(localStorage.getItem('fct_token')));

  async function loadUser() {
    try {
      const data = await requestJson('/users/me');
      setUser(data);
      setPage(data.role === 'tutor' ? 'students' : data.role === 'admin' ? 'users' : 'home');
      return data;
    } catch {
      localStorage.removeItem('fct_token');
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (localStorage.getItem('fct_token')) loadUser();
  }, []);

  useEffect(() => {
    if (!user) return;
    requestJson('/notifications/me').then(setNotifications).catch(() => setNotifications([]));
  }, [user]);

  useEffect(() => {
    const navigate = (event) => setPage(event.detail);
    window.addEventListener('fct:navigate', navigate);
    return () => window.removeEventListener('fct:navigate', navigate);
  }, []);

  useEffect(() => {
    if (!notice) return undefined;
    const timer = window.setTimeout(() => setNotice(null), 4200);
    return () => window.clearTimeout(timer);
  }, [notice]);

  async function markRead(id) {
    try {
      await requestJson(`/notifications/${id}/read`, { method: 'PUT' });
      setNotifications((items) => items.map((item) => item.id === id ? { ...item, is_read: true } : item));
    } catch (error) {
      setNotice({ text: error.message, kind: 'error' });
    }
  }

  function logout() {
    localStorage.removeItem('fct_token');
    setNotifications([]);
    setUser(null);
  }

  if (loading) return <main className="boot-screen"><span className="brand-mark">F</span><span>Conectando con Portal FCT…</span></main>;
  if (!user) return <AuthScreen onLogin={loadUser} />;

  const role = user.role in NAVIGATION ? user.role : 'alumno';
  const navigation = NAVIGATION[role];
  const unreadCount = notifications.filter((item) => !item.is_read).length;

  return (
    <div className="app-frame">
      <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <div className="brand"><span className="brand-mark">F</span><span>portal<span className="brand-light">fct</span></span></div>
        <div className="sidebar-label">ESPACIO {ROLE_NAMES[role]?.toUpperCase()}</div>
        <nav className="side-nav" aria-label="Navegación principal">
          {navigation.map(({ key, label, icon: Icon }) => (
            <button key={key} className={`nav-item ${page === key ? 'nav-active' : ''}`} onClick={() => { setPage(key); setSidebarOpen(false); }}>
              <Icon size={18} strokeWidth={1.8} /><span>{label}</span>{key === 'hours' && role === 'empresa' && <span className="nav-mini-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="user-chip"><span className="avatar">{(user.full_name || user.email).slice(0, 1).toUpperCase()}</span><span className="user-chip-text"><strong>{user.full_name || user.email.split('@')[0]}</strong><small>{ROLE_NAMES[role]}</small></span><button className="icon-button logout-button" onClick={logout} aria-label="Cerrar sesión" title="Cerrar sesión"><LogOut size={17} /></button></div>
        </div>
      </aside>
      {sidebarOpen && <button className="mobile-scrim" onClick={() => setSidebarOpen(false)} aria-label="Cerrar menú" />}
      <main className="main-area">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setSidebarOpen(true)} aria-label="Abrir menú"><Menu size={21} /></button>
          <div className="breadcrumb"><span>Portal FCT</span><i>/</i><strong>{PAGE_TITLES[page] || 'Portal'}</strong></div>
          <div className="topbar-actions">
            <span className="session-indicator"><span /> Sesión activa</span>
            <div className="notification-anchor">
              <button className={`icon-button notification-toggle ${unreadCount ? 'has-unread' : ''}`} onClick={() => setShowNotifications(!showNotifications)} aria-label="Notificaciones">
                <Bell size={19} />{unreadCount > 0 && <span className="notification-count">{unreadCount > 9 ? '9+' : unreadCount}</span>}
              </button>
              {showNotifications && <NotificationPopover items={notifications} onRead={markRead} onClose={() => setShowNotifications(false)} />}
            </div>
          </div>
        </header>
        {notice && <div className={`toast toast-${notice.kind}`} role="status">{notice.text}<button className="icon-button" onClick={() => setNotice(null)} aria-label="Cerrar aviso"><X size={16} /></button></div>}
        {role === 'alumno' && <StudentWorkspace page={page} user={user} notify={(text, kind = 'success') => setNotice({ text, kind })} />}
        {role === 'empresa' && <CompanyWorkspace page={page} user={user} notify={(text, kind = 'success') => setNotice({ text, kind })} />}
        {(role === 'tutor' || role === 'admin') && <TutorAdminWorkspace role={role} page={page} user={user} notify={(text, kind = 'success') => setNotice({ text, kind })} />}
        <footer className="page-footer"><span>Portal FCT</span><span>Formación · Prácticas · Futuro</span></footer>
      </main>
    </div>
  );
}