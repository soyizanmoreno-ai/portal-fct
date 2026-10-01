import { useEffect, useMemo, useState } from 'react';
import { ArrowUpRight, BriefcaseBusiness, Check, ChevronRight, Clock3, Download, FileText, Plus, Search, Sparkles, Trash2, Upload } from 'lucide-react';
import { api, download, requestJson } from '../api';

const STATUS_LABELS = { pendiente: 'Pendiente', en_revision: 'En revisión', entrevista: 'Entrevista', aceptado: 'Aceptada', rechazado: 'No seleccionada', retirada: 'Retirada' };
const EMPTY_PROFILE = { full_name: '', github_url: '', linkedin_url: '', portfolio_url: '', technologies: [], suggested_technologies: [], location_city: '', location_province: '', education: [], experience_projects: [], availability: '', languages: [], soft_skills: [], profile_confirmed: false, cv_url: '' };

function SectionHeading({ eyebrow, title, aside }) {
  return <div className="section-heading"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1></div>{aside}</div>;
}

function Metric({ label, value, detail, tone = 'mint' }) {
  return <div className={`metric metric-${tone}`}><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>;
}

export default function StudentWorkspace({ page, user, notify }) {
  const [offers, setOffers] = useState([]);
  const [applications, setApplications] = useState([]);
  const [profile, setProfile] = useState(EMPTY_PROFILE);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({});
  const [busy, setBusy] = useState(false);
  const [search, setSearch] = useState('');
  const [query, setQuery] = useState('');
  const [logForm, setLogForm] = useState({ application_id: '', date: new Date().toISOString().slice(0, 10), hours: '', tasks: '' });
  const [profileForm, setProfileForm] = useState(EMPTY_PROFILE);

  async function loadPage() {
    try {
      const [offerRows, applicationRows, profileData, logRows, statsData] = await Promise.all([
        requestJson(`/offers/?search=${encodeURIComponent(query)}&limit=40`),
        requestJson('/applications/me'),
        requestJson('/users/profile'),
        requestJson('/fct-logs/me'),
        requestJson('/stats/student'),
      ]);
      setOffers(offerRows);
      setApplications(applicationRows);
      setProfile({ ...EMPTY_PROFILE, ...profileData });
      setProfileForm({ ...EMPTY_PROFILE, ...profileData });
      setLogs(logRows);
      setStats(statsData);
    } catch (error) {
      notify(error.message, 'error');
    }
  }

  useEffect(() => { loadPage(); }, [user.id, query]);

  const appliedIds = useMemo(() => new Set(applications.map((item) => item.offer_id)), [applications]);
  const acceptedApplications = applications.filter((item) => item.status === 'aceptado');
  const skillsText = (skills) => skills.map((item) => typeof item === 'string' ? item : `${item.name}${item.context ? ` | ${item.context}` : ''}`).join('\n');
  const parseSkills = (text) => text.split('\n').map((line) => line.trim()).filter(Boolean).map((line) => {
    const [name, ...context] = line.split('|');
    return { name: name.trim(), context: context.join('|').trim() || null };
  });

  async function applyToOffer(offerId) {
    setBusy(true);
    try {
      await requestJson('/applications/', { method: 'POST', body: JSON.stringify({ offer_id: offerId }) });
      notify('Candidatura enviada.');
      await loadPage();
    } catch (error) { notify(error.message, 'error'); }
    finally { setBusy(false); }
  }

  async function withdraw(id) {
    try {
      await requestJson(`/applications/${id}/withdraw`, { method: 'PATCH' });
      notify('Candidatura retirada.');
      await loadPage();
    } catch (error) { notify(error.message, 'error'); }
  }

  async function saveProfile(confirmProfile = false) {
    const payload = {
      full_name: profileForm.full_name || null,
      github_url: profileForm.github_url || null,
      linkedin_url: profileForm.linkedin_url || null,
      portfolio_url: profileForm.portfolio_url || null,
      technologies: parseSkills(skillsText(profileForm.technologies)),
      location_city: profileForm.location_city || null,
      location_province: profileForm.location_province || null,
      education: Array.isArray(profileForm.education) ? profileForm.education : profileForm.education.split('\n').filter(Boolean),
      experience_projects: Array.isArray(profileForm.experience_projects) ? profileForm.experience_projects : profileForm.experience_projects.split('\n').filter(Boolean),
      availability: profileForm.availability || null,
      languages: Array.isArray(profileForm.languages) ? profileForm.languages : profileForm.languages.split('\n').filter(Boolean),
      soft_skills: Array.isArray(profileForm.soft_skills) ? profileForm.soft_skills : profileForm.soft_skills.split('\n').filter(Boolean),
      confirm_profile: confirmProfile,
    };
    try {
      const saved = await requestJson('/users/profile', { method: 'PUT', body: JSON.stringify(payload) });
      setProfile({ ...EMPTY_PROFILE, ...saved });
      setProfileForm({ ...EMPTY_PROFILE, ...saved });
      notify(confirmProfile ? 'Perfil confirmado y visible para las empresas con tu candidatura.' : 'Cambios guardados como borrador.');
    } catch (error) { notify(error.message, 'error'); }
  }

  async function uploadCv(event) {
    event.preventDefault();
    const file = event.currentTarget.elements.cv.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    try {
      const response = await api('/users/upload-cv', { method: 'POST', body: form });
      const saved = await response.json();
      setProfile({ ...EMPTY_PROFILE, ...saved });
      setProfileForm({ ...EMPTY_PROFILE, ...saved });
      notify('CV subido. Revisa las sugerencias antes de confirmar el perfil.');
      event.currentTarget.reset();
    } catch (error) { notify(error.message, 'error'); }
  }

  async function createLog(event) {
    event.preventDefault();
    try {
      await requestJson('/fct-logs/', { method: 'POST', body: JSON.stringify({ ...logForm, application_id: Number(logForm.application_id), hours: Number(logForm.hours) }) });
      setLogForm((current) => ({ ...current, hours: '', tasks: '' }));
      notify('Parte registrado. Empresa y tutor han recibido un aviso.');
      await loadPage();
    } catch (error) { notify(error.message, 'error'); }
  }

  function downloadCv() {
    return download('/users/cv', 'mi-cv.pdf').catch((error) => notify(error.message, 'error'));
  }

  if (page === 'home') return (
    <div className="workspace-content">
      <SectionHeading eyebrow="TU CURSO, EN MOVIMIENTO" title={`Hola, ${profile.full_name?.split(' ')[0] || user.email.split('@')[0]}.`} aside={<span className="date-pill">{new Intl.DateTimeFormat('es-ES', { dateStyle: 'long' }).format(new Date())}</span>} />
      <div className="metric-grid">
        <Metric label="Candidaturas" value={stats.total_applications || 0} detail="Enviadas a empresas" />
        <Metric label="Horas registradas" value={`${stats.total_hours_logged || 0} h`} detail={`${stats.pending_hours || 0} h pendientes de validar`} tone="blue" />
        <Metric label="Horas aprobadas" value={`${stats.approved_hours || 0} h`} detail="Validadas por empresa y tutor" tone="coral" />
      </div>
      <div className="dashboard-grid">
        <section className="surface surface-large">
          <div className="surface-title"><div><span className="eyebrow">ACTIVIDAD</span><h2>Últimas candidaturas</h2></div><button className="text-button" onClick={() => window.dispatchEvent(new CustomEvent('fct:navigate', { detail: 'applications' }))}>Ver todas <ArrowUpRight size={15} /></button></div>
          {applications.length ? <div className="application-list">{applications.slice(0, 4).map((item) => <ApplicationRow key={item.id} item={item} />)}</div> : <EmptyState title="Todavía no hay candidaturas" action="Explorar ofertas" onClick={() => window.dispatchEvent(new CustomEvent('fct:navigate', { detail: 'offers' }))} />}
        </section>
        <section className="surface profile-progress">
          <div className="surface-title"><div><span className="eyebrow">PERFIL</span><h2>{profile.profile_confirmed ? 'Visible para empresas' : 'Completa tu ficha'}</h2></div><span className={`profile-state ${profile.profile_confirmed ? 'state-ok' : 'state-pending'}`}>{profile.profile_confirmed ? 'Confirmado' : 'Borrador'}</span></div>
          <p>{profile.profile_confirmed ? 'Tu información estructurada acompaña el CV cuando te postulas.' : 'Las empresas verán tu ficha cuando revises y confirmes los datos.'}</p>
          <div className="profile-meter"><span style={{ width: `${Math.min(100, [profile.full_name, profile.technologies?.length, profile.education?.length, profile.cv_url].filter(Boolean).length * 25)}%` }} /></div>
          <button className="button button-secondary" onClick={() => window.dispatchEvent(new CustomEvent('fct:navigate', { detail: 'profile' }))}>Revisar perfil <ChevronRight size={16} /></button>
        </section>
      </div>
      <section className="band-callout"><div><span className="eyebrow">SIGUIENTE PASO</span><strong>Encuentra prácticas que encajen contigo.</strong></div><button className="button button-light" onClick={() => window.dispatchEvent(new CustomEvent('fct:navigate', { detail: 'offers' }))}>Ver ofertas <ArrowUpRight size={16} /></button></section>
    </div>
  );

  if (page === 'offers') return (
    <div className="workspace-content">
      <SectionHeading eyebrow="OPORTUNIDADES ABIERTAS" title="Explorar ofertas" aside={<form className="search-box" onSubmit={(event) => { event.preventDefault(); setQuery(search); }}><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Puesto, tecnología…" /><button aria-label="Buscar"><ArrowUpRight size={16} /></button></form>} />
      <div className="offer-grid">{offers.map((offer) => <article className="offer-card" key={offer.id}><div className="offer-topline"><span className="offer-mark">{(offer.company_name || 'E').slice(0, 1)}</span><span className="offer-open"><i /> Abierta</span></div><h2>{offer.title}</h2><p className="offer-company">{offer.company_name || `Empresa #${offer.company_id}`}</p><p className="offer-description">{offer.description}</p><div className="offer-footer"><span><BriefcaseBusiness size={15} /> FCT</span><button className="button button-primary" disabled={busy || appliedIds.has(offer.id)} onClick={() => applyToOffer(offer.id)}>{appliedIds.has(offer.id) ? 'Ya solicitada' : 'Postularme'}{!appliedIds.has(offer.id) && <ArrowUpRight size={15} />}</button></div></article>)}{offers.length === 0 && <EmptyState title="No encontramos ofertas" action="Limpiar búsqueda" onClick={() => { setSearch(''); setQuery(''); }} />}</div>
    </div>
  );

  if (page === 'applications') return (
    <div className="workspace-content"><SectionHeading eyebrow="PROCESO DE SELECCIÓN" title="Mis candidaturas" /><section className="surface table-surface"><div className="table-head"><span>Oferta</span><span>Empresa</span><span>Fecha</span><span>Estado</span><span /></div>{applications.map((item) => <div className="table-row" key={item.id}><div><strong>{item.offer?.title || `Oferta #${item.offer_id}`}</strong><small>Referencia #{item.id}</small></div><span>{item.offer?.company_name || `Empresa #${item.offer?.company_id || ''}`}</span><span>{new Date(item.created_at).toLocaleDateString('es-ES')}</span><StatusBadge status={item.status} /><span>{['pendiente','en_revision','entrevista'].includes(item.status) && <button className="small-action" onClick={() => withdraw(item.id)}><Trash2 size={14} /> Retirar</button>}</span></div>)}{applications.length === 0 && <EmptyState title="Aún no te has postulado" action="Buscar ofertas" onClick={() => window.dispatchEvent(new CustomEvent('fct:navigate', { detail: 'offers' }))} />}</section></div>
  );

  if (page === 'profile') return (
    <div className="workspace-content"><SectionHeading eyebrow="FICHA PROFESIONAL" title="Mi perfil" aside={<span className={`profile-state ${profile.profile_confirmed ? 'state-ok' : 'state-pending'}`}>{profile.profile_confirmed ? 'Confirmado' : 'Pendiente de confirmar'}</span>} />
      <div className="profile-layout"><div className="profile-main-column"><section className="surface"><div className="surface-title"><div><span className="eyebrow">CV</span><h2>Currículum</h2></div>{profile.cv_url && <button className="icon-button" onClick={downloadCv} aria-label="Descargar CV"><Download size={18} /></button>}</div><form className="upload-zone" onSubmit={uploadCv}><label className="upload-control"><Upload size={19} /><span>{profile.cv_url ? 'Sustituir CV en PDF' : 'Subir CV en PDF'}</span><input name="cv" type="file" accept="application/pdf,.pdf" required /></label><span className="upload-hint">Máximo 5 MB</span><button className="button button-primary" type="submit">Subir CV</button></form>{profile.suggested_technologies?.length > 0 && <div className="suggestion-box"><div className="suggestion-heading"><Sparkles size={17} /><div><strong>Sugerencias detectadas</strong><small>Comprueba que el contexto sea correcto y añade las que quieras.</small></div></div><div className="suggestion-list">{profile.suggested_technologies.map((item) => <button key={`${item.name}-${item.context}`} className="suggestion-item" onClick={() => setProfileForm((current) => ({ ...current, technologies: [...current.technologies, item] }))}><span><strong>{item.name}</strong><small>{item.context}</small></span><Plus size={17} /></button>)}</div></div>}</section>
        <section className="surface"><div className="surface-title"><div><span className="eyebrow">INFORMACIÓN</span><h2>Tu ficha profesional</h2></div></div><div className="profile-form-grid"><label>Nombre completo<input value={profileForm.full_name || ''} onChange={(event) => setProfileForm({ ...profileForm, full_name: event.target.value })} /></label><label>Ciudad<input value={profileForm.location_city || ''} onChange={(event) => setProfileForm({ ...profileForm, location_city: event.target.value })} /></label><label>Provincia<input value={profileForm.location_province || ''} onChange={(event) => setProfileForm({ ...profileForm, location_province: event.target.value })} /></label><label>Disponibilidad<input placeholder="Ej. Septiembre 2026" value={profileForm.availability || ''} onChange={(event) => setProfileForm({ ...profileForm, availability: event.target.value })} /></label><label className="wide-field">Tecnologías y contexto<textarea rows="4" placeholder={'Una por línea: tecnología | proyecto o experiencia'} value={skillsText(profileForm.technologies || [])} onChange={(event) => setProfileForm({ ...profileForm, technologies: parseSkills(event.target.value) })} /></label><label>Formación<textarea rows="3" placeholder="Una por línea" value={(profileForm.education || []).join('\n')} onChange={(event) => setProfileForm({ ...profileForm, education: event.target.value.split('\n') })} /></label><label>Proyectos y experiencia<textarea rows="3" placeholder="Una por línea" value={(profileForm.experience_projects || []).join('\n')} onChange={(event) => setProfileForm({ ...profileForm, experience_projects: event.target.value.split('\n') })} /></label><label>Idiomas<textarea rows="2" placeholder="Uno por línea" value={(profileForm.languages || []).join('\n')} onChange={(event) => setProfileForm({ ...profileForm, languages: event.target.value.split('\n') })} /></label><label>Competencias<textarea rows="2" placeholder="Una por línea" value={(profileForm.soft_skills || []).join('\n')} onChange={(event) => setProfileForm({ ...profileForm, soft_skills: event.target.value.split('\n') })} /></label><label>GitHub<input type="url" value={profileForm.github_url || ''} onChange={(event) => setProfileForm({ ...profileForm, github_url: event.target.value })} /></label><label>LinkedIn<input type="url" value={profileForm.linkedin_url || ''} onChange={(event) => setProfileForm({ ...profileForm, linkedin_url: event.target.value })} /></label><label>Portfolio<input type="url" value={profileForm.portfolio_url || ''} onChange={(event) => setProfileForm({ ...profileForm, portfolio_url: event.target.value })} /></label></div><div className="form-actions"><button className="button button-secondary" onClick={() => saveProfile(false)}>Guardar borrador</button><button className="button button-primary" onClick={() => saveProfile(true)}><Check size={16} /> Confirmar ficha</button></div></section></div><aside className="profile-aside"><div className="surface profile-aside-card"><span className="eyebrow">VISIBILIDAD</span><div className="visibility-mark"><Check size={20} /></div><h3>{profile.profile_confirmed ? 'Tu ficha está lista' : 'Tu ficha aún no se comparte'}</h3><p>La empresa que reciba tu candidatura podrá ver los datos confirmados. El CV se comparte con esa empresa para que pueda valorar tu candidatura.</p></div></aside></div>
    </div>
  );

  if (page === 'hours') return (
    <div className="workspace-content"><SectionHeading eyebrow="CUADERNO DE PRÁCTICAS" title="Horas FCT" aside={<span className="hours-total"><Clock3 size={17} />{stats.total_hours_logged || 0} h registradas</span>} /><div className="hours-layout"><section className="surface"><div className="surface-title"><div><span className="eyebrow">NUEVO PARTE</span><h2>Registrar horas</h2></div></div>{acceptedApplications.length ? <form className="form-stack" onSubmit={createLog}><label>Práctica<select required value={logForm.application_id} onChange={(event) => setLogForm({ ...logForm, application_id: event.target.value })}><option value="">Selecciona una práctica</option>{acceptedApplications.map((item) => <option key={item.id} value={item.id}>{item.offer?.title || `Oferta #${item.offer_id}`}</option>)}</select></label><div className="form-row"><label>Fecha<input type="date" value={logForm.date} onChange={(event) => setLogForm({ ...logForm, date: event.target.value })} required /></label><label>Horas<input type="number" min="0.25" max="24" step="0.25" value={logForm.hours} onChange={(event) => setLogForm({ ...logForm, hours: event.target.value })} required /></label></div><label>Tareas realizadas<textarea maxLength={250} rows="4" value={logForm.tasks} onChange={(event) => setLogForm({ ...logForm, tasks: event.target.value })} required /></label><button className="button button-primary">Enviar parte <ArrowUpRight size={16} /></button></form> : <EmptyState title="Necesitas una práctica aceptada" />}</section><section className="surface"><div className="surface-title"><div><span className="eyebrow">HISTORIAL</span><h2>Partes registrados</h2></div></div><div className="log-list">{logs.map((item) => <div className="log-row" key={item.id}><span className="log-date">{new Date(item.date).toLocaleDateString('es-ES',{day:'2-digit',month:'short'})}</span><span className="log-hours">{item.hours} h</span><span className="approval-pair"><i className={item.is_approved ? 'approved' : ''} title="Empresa" /><i className={item.is_tutor_approved ? 'approved' : ''} title="Tutor" /></span><span className="log-state">{item.fully_approved ? 'Aprobado' : 'Pendiente de revisión'}</span></div>)}{logs.length === 0 && <p className="empty-inline">Todavía no hay partes registrados.</p>}</div><div className="approval-legend"><span><i className="approved" /> Empresa</span><span><i className="approved" /> Tutor</span></div></section></div></div>
  );

  return null;
}

function ApplicationRow({ item }) {
  return <div className="application-row"><span className="application-icon"><BriefcaseBusiness size={17} /></span><span className="application-row-main"><strong>{item.offer?.title || `Oferta #${item.offer_id}`}</strong><small>{item.offer?.company_name || `Empresa #${item.offer?.company_id || ''}`}</small></span><StatusBadge status={item.status} /><span className="row-date">{new Date(item.created_at).toLocaleDateString('es-ES')}</span></div>;
}

function StatusBadge({ status }) {
  const label = { pendiente: 'Pendiente', en_revision: 'En revisión', entrevista: 'Entrevista', aceptado: 'Aceptada', rechazado: 'No seleccionada', retirada: 'Retirada' }[status] || status;
  return <span className={`status-badge status-${status}`}>{label}</span>;
}

function EmptyState({ title, action, onClick }) {
  return <div className="empty-state"><span className="empty-symbol"><FileText size={20} /></span><strong>{title}</strong>{action && <button className="text-button" onClick={onClick}>{action} <ChevronRight size={15} /></button>}</div>;
}