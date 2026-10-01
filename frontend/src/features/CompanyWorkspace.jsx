import { useEffect, useState } from 'react';
import { ArrowUpRight, Building2, Check, Download, FilePlus2, Pause, Play, Users } from 'lucide-react';
import { download, requestJson } from '../api';

const STATUS_OPTIONS = [
  ['pendiente', 'Pendiente'], ['en_revision', 'En revisión'], ['entrevista', 'Entrevista'],
  ['aceptado', 'Aceptado'], ['rechazado', 'No seleccionado'],
];

export default function CompanyWorkspace({ page, user, notify }) {
  const [offers, setOffers] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [pendingLogs, setPendingLogs] = useState([]);
  const [stats, setStats] = useState({});
  const [companyProfile, setCompanyProfile] = useState({ company_name: '', cif: '', website: '' });
  const [selectedOffer, setSelectedOffer] = useState('');
  const [offerForm, setOfferForm] = useState({ title: '', description: '' });
  const [loading, setLoading] = useState(false);

  async function loadData() {
    try {
      const [offerRows, logRows, statsData, profileData] = await Promise.all([
        requestJson('/offers/mine'),
        requestJson('/fct-logs/company/pending'),
        requestJson('/stats/company'),
        requestJson('/users/company-profile').catch(() => ({ company_name: '', cif: '', website: '' })),
      ]);
      setOffers(offerRows);
      setPendingLogs(logRows);
      setStats(statsData);
      setCompanyProfile(profileData);
      if (!selectedOffer && offerRows.length) setSelectedOffer(String(offerRows[0].id));
    } catch (error) { notify(error.message, 'error'); }
  }

  async function loadCandidates(offerId) {
    if (!offerId) { setCandidates([]); return; }
    try { setCandidates(await requestJson(`/applications/offer/${offerId}`)); }
    catch (error) { notify(error.message, 'error'); }
  }

  useEffect(() => { loadData(); }, [user.id]);
  useEffect(() => { if (page === 'candidates') loadCandidates(selectedOffer); }, [page, selectedOffer]);

  async function createOffer(event) {
    event.preventDefault(); setLoading(true);
    try {
      await requestJson('/offers/', { method: 'POST', body: JSON.stringify(offerForm) });
      setOfferForm({ title: '', description: '' });
      notify('Oferta publicada.');
      await loadData();
    } catch (error) { notify(error.message, 'error'); }
    finally { setLoading(false); }
  }

  async function toggleOffer(offer) {
    try {
      await requestJson(`/offers/${offer.id}/status`, { method: 'PATCH', body: JSON.stringify({ is_active: !offer.is_active }) });
      notify(offer.is_active ? 'Oferta pausada.' : 'Oferta reactivada.');
      await loadData();
    } catch (error) { notify(error.message, 'error'); }
  }

  async function updateApplication(application, status) {
    try {
      await requestJson(`/applications/${application.id}/status`, { method: 'PUT', body: JSON.stringify({ status }) });
      notify(status === 'entrevista' ? 'Candidatura en entrevista. El contacto ya está disponible.' : 'Estado actualizado.');
      await loadCandidates(selectedOffer);
    } catch (error) { notify(error.message, 'error'); }
  }

  async function approveLog(log) {
    try {
      await requestJson(`/fct-logs/${log.id}/approve`, { method: 'PUT' });
      notify('Horas revisadas.');
      await loadData();
    } catch (error) { notify(error.message, 'error'); }
  }

  async function saveProfile(event) {
    event.preventDefault();
    try {
      const saved = await requestJson('/users/company-profile', { method: 'PUT', body: JSON.stringify({ ...companyProfile, website: companyProfile.website || null }) });
      setCompanyProfile(saved);
      notify('Perfil de empresa guardado.');
      await loadData();
    } catch (error) { notify(error.message, 'error'); }
  }

  if (page === 'home') return (
    <div className="workspace-content"><SectionHeading eyebrow="PANEL DE EMPRESA" title={`Hola, ${companyProfile.company_name || user.email.split('@')[0]}.`} />
      <div className="metric-grid"><Metric label="Ofertas activas" value={stats.total_offers || 0} detail="Publicadas por tu empresa" /><Metric label="Candidaturas" value={stats.total_applications_received || 0} detail="En todos tus procesos" tone="blue" /><Metric label="Partes por revisar" value={stats.pending_fct_approvals || 0} detail="Pendientes de tu validación" tone="coral" /></div>
      <div className="dashboard-grid"><section className="surface surface-large"><div className="surface-title"><div><span className="eyebrow">PUBLICACIONES</span><h2>Tus ofertas</h2></div><button className="button button-secondary" onClick={() => window.dispatchEvent(new CustomEvent('fct:navigate', { detail: 'offers' }))}><FilePlus2 size={16} /> Gestionar</button></div><div className="company-offer-list">{offers.slice(0, 4).map((offer) => <OfferRow key={offer.id} offer={offer} onToggle={toggleOffer} />)}{offers.length === 0 && <EmptyState title="Completa tu empresa y publica la primera oferta" onAction={() => window.dispatchEvent(new CustomEvent('fct:navigate', { detail: 'profile' }))} />}</div></section><section className="surface profile-progress"><div className="surface-title"><div><span className="eyebrow">CENTRO DE CONTROL</span><h2>Revisa los procesos</h2></div><span className="home-icon"><Users size={19} /></span></div><p>Consulta quién se ha postulado y avanza cada candidatura por su fase.</p><button className="button button-primary" onClick={() => window.dispatchEvent(new CustomEvent('fct:navigate', { detail: 'candidates' }))}>Ver candidaturas <ArrowUpRight size={16} /></button></section></div>
      <section className="band-callout"><div><span className="eyebrow">PRÁCTICAS FCT</span><strong>Una nueva incorporación empieza con una buena oportunidad.</strong></div><button className="button button-light" onClick={() => window.dispatchEvent(new CustomEvent('fct:navigate', { detail: 'offers' }))}>Publicar oferta <ArrowUpRight size={16} /></button></section>
    </div>
  );

  if (page === 'offers') return (
    <div className="workspace-content"><SectionHeading eyebrow="PUBLICACIONES" title="Mis ofertas" /><div className="company-work-grid"><section className="surface"><div className="surface-title"><div><span className="eyebrow">NUEVA OPORTUNIDAD</span><h2>Publicar oferta</h2></div><FilePlus2 size={19} /></div><form className="form-stack" onSubmit={createOffer}><label>Título<input maxLength={50} value={offerForm.title} onChange={(event) => setOfferForm({ ...offerForm, title: event.target.value })} required /></label><label>Descripción<textarea rows="5" maxLength={200} value={offerForm.description} onChange={(event) => setOfferForm({ ...offerForm, description: event.target.value })} required /></label><button className="button button-primary" disabled={loading}>{loading ? 'Publicando…' : 'Publicar oferta'} <ArrowUpRight size={16} /></button></form></section><section className="surface"><div className="surface-title"><div><span className="eyebrow">GESTIÓN</span><h2>Ofertas publicadas</h2></div><span className="count-pill">{offers.length}</span></div><div className="company-offer-list">{offers.map((offer) => <OfferRow key={offer.id} offer={offer} onToggle={toggleOffer} />)}{offers.length === 0 && <p className="empty-inline">Todavía no hay ofertas.</p>}</div></section></div></div>
  );

  if (page === 'candidates') return (
    <div className="workspace-content"><SectionHeading eyebrow="SELECCIÓN" title="Candidaturas recibidas" aside={<select className="inline-select" value={selectedOffer} onChange={(event) => setSelectedOffer(event.target.value)}><option value="">Todas las ofertas</option>{offers.map((offer) => <option key={offer.id} value={offer.id}>{offer.title}</option>)}</select>} /><section className="surface table-surface"><div className="candidate-head"><span>Candidato</span><span>Perfil</span><span>Fase</span><span>Currículum</span></div>{candidates.map((application) => { const candidate = application.student || {}; return <div className="candidate-row" key={application.id}><div className="candidate-identity"><span className="avatar avatar-candidate">{(candidate.full_name || 'A').slice(0, 1)}</span><span><strong>{candidate.full_name || 'Alumno'}</strong><small>{candidate.email || 'Contacto disponible al pasar a entrevista'}</small></span></div><div className="candidate-skills">{(candidate.technologies || []).slice(0, 3).map((tech) => <span className="skill-chip" key={tech.name}>{tech.name}</span>)}<small>{candidate.location_city || candidate.location_province || 'Ubicación no indicada'}</small></div><select className="status-select" value={application.status} onChange={(event) => updateApplication(application, event.target.value)}>{STATUS_OPTIONS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select><button className="icon-button cv-download" title="Descargar CV" aria-label="Descargar CV" onClick={() => download(`/applications/${application.id}/cv`, `${candidate.full_name || 'candidato'}.pdf`).catch((error) => notify(error.message, 'error'))}><Download size={18} /></button></div>; })}{candidates.length === 0 && <EmptyState title={selectedOffer ? 'Esta oferta todavía no tiene candidaturas' : 'Selecciona una oferta'} />}</section><p className="privacy-note">El CV está disponible para valorar la candidatura. El email se muestra al avanzar a entrevista.</p></div>
  );

  if (page === 'hours') return (
    <div className="workspace-content"><SectionHeading eyebrow="VALIDACIÓN DE PRÁCTICAS" title="Partes FCT pendientes" /><section className="surface table-surface"><div className="candidate-head fct-head"><span>Fecha</span><span>Parte</span><span>Horas</span><span>Estado</span></div>{pendingLogs.map((log) => <div className="candidate-row fct-row" key={log.id}><span>{new Date(log.date).toLocaleDateString('es-ES')}</span><span>Registro #{log.id}</span><strong>{log.hours} h</strong><span className="approval-pair"><i className={log.is_approved ? 'approved' : ''} title="Empresa" /><i className={log.is_tutor_approved ? 'approved' : ''} title="Tutor" /></span><button className="button button-secondary button-compact" disabled={log.is_approved} onClick={() => approveLog(log)}>{log.is_approved ? 'Revisado' : 'Validar'} <Check size={15} /></button></div>)}{pendingLogs.length === 0 && <EmptyState title="No hay partes pendientes" />}</section></div>
  );

  if (page === 'profile') return (
    <div className="workspace-content"><SectionHeading eyebrow="IDENTIDAD CORPORATIVA" title="Perfil de empresa" /><section className="surface profile-editor"><div className="surface-title"><div><span className="eyebrow">DATOS DE ORGANIZACIÓN</span><h2>Información pública</h2></div><Building2 size={20} /></div><form className="profile-form-grid" onSubmit={saveProfile}><label>Nombre de empresa<input value={companyProfile.company_name || ''} onChange={(event) => setCompanyProfile({ ...companyProfile, company_name: event.target.value })} required /></label><label>CIF<input value={companyProfile.cif || ''} onChange={(event) => setCompanyProfile({ ...companyProfile, cif: event.target.value.toUpperCase() })} placeholder="B12345678" required /></label><label className="wide-field">Web corporativa<input type="url" value={companyProfile.website || ''} onChange={(event) => setCompanyProfile({ ...companyProfile, website: event.target.value })} placeholder="https://empresa.es" /></label><div className="wide-field form-actions"><button className="button button-primary">Guardar perfil <Check size={16} /></button></div></form><p className="privacy-note">El nombre aparece junto a tus ofertas. El CIF no se muestra a los candidatos.</p></section></div>
  );

  return null;
}

function SectionHeading({ eyebrow, title, aside }) { return <div className="section-heading"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1></div>{aside}</div>; }
function Metric({ label, value, detail, tone = 'mint' }) { return <div className={`metric metric-${tone}`}><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>; }
function OfferRow({ offer, onToggle }) { return <div className="company-offer-row"><span className="offer-mark">{(offer.title || 'P').slice(0, 1)}</span><span className="company-offer-main"><strong>{offer.title}</strong><small>{offer.is_active ? 'Recibiendo candidaturas' : 'Pausada'}</small></span><button className="icon-button" onClick={() => onToggle(offer)} aria-label={offer.is_active ? 'Pausar oferta' : 'Reactivar oferta'} title={offer.is_active ? 'Pausar' : 'Reactivar'}>{offer.is_active ? <Pause size={16} /> : <Play size={16} />}</button></div>; }
function EmptyState({ title, action, onAction }) { return <div className="empty-state"><span className="empty-symbol"><Users size={20} /></span><strong>{title}</strong>{action && <button className="text-button" onClick={onAction}>{action}</button>}</div>; }