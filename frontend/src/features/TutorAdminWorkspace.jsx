import { useEffect, useState } from 'react';
import { ArrowUpRight, Check, GraduationCap, Plus, ShieldCheck } from 'lucide-react';
import { requestJson } from '../api';

export default function TutorAdminWorkspace({ role, page, user, notify }) {
  const [students, setStudents] = useState([]);
  const [studentId, setStudentId] = useState('');
  const [logs, setLogs] = useState([]);
  const [account, setAccount] = useState({ email: '', password: '', role: 'empresa' });
  const [busy, setBusy] = useState(false);

  async function loadStudents() {
    try { setStudents(await requestJson('/tutor/my-students')); }
    catch (error) { notify(error.message, 'error'); }
  }

  useEffect(() => { if (role === 'tutor') loadStudents(); }, [role, user.id]);

  async function assignStudent(event) {
    event.preventDefault();
    try {
      await requestJson(`/tutor/assign-student/${Number(studentId)}`, { method: 'POST' });
      setStudentId(''); notify('Alumno asignado a tu tutoría.'); await loadStudents();
    } catch (error) { notify(error.message, 'error'); }
  }

  async function showLogs(student) {
    try {
      setStudentId(String(student.student.id));
      setLogs(await requestJson(`/tutor/student/${student.student.id}/fct-logs`));
    } catch (error) { notify(error.message, 'error'); }
  }

  async function approve(studentIdValue, log) {
    try {
      await requestJson(`/tutor/student/${studentIdValue}/fct-logs/${log.id}/approve`, { method: 'PUT' });
      notify('Parte FCT aprobado.');
      setLogs(await requestJson(`/tutor/student/${studentIdValue}/fct-logs`));
      await loadStudents();
    } catch (error) { notify(error.message, 'error'); }
  }

  async function createUser(event) {
    event.preventDefault(); setBusy(true);
    try {
      await requestJson('/admin/users', { method: 'POST', body: JSON.stringify(account) });
      setAccount({ email: '', password: '', role: 'empresa' });
      notify(`Cuenta de ${account.role} creada.`);
    } catch (error) { notify(error.message, 'error'); }
    finally { setBusy(false); }
  }

  if (role === 'admin') return (
    <div className="workspace-content"><SectionHeading eyebrow="ADMINISTRACIÓN" title="Cuentas de prueba" /><div className="admin-intro"><span className="admin-shield"><ShieldCheck size={24} /></span><div><strong>Provisionamiento controlado</strong><p>Las cuentas de empresa y tutor las crea un administrador. No se ofrece registro público de roles privilegiados.</p></div></div><section className="surface admin-form"><div className="surface-title"><div><span className="eyebrow">NUEVA CUENTA</span><h2>Crear usuario</h2></div><Plus size={19} /></div><form className="form-stack admin-form-inner" onSubmit={createUser}><label>Email<input type="email" value={account.email} onChange={(event) => setAccount({ ...account, email: event.target.value })} required /></label><label>Contraseña temporal<input type="password" minLength={12} value={account.password} onChange={(event) => setAccount({ ...account, password: event.target.value })} required /><small>Mínimo 12 caracteres. Comunícala por un canal seguro.</small></label><label>Rol<select value={account.role} onChange={(event) => setAccount({ ...account, role: event.target.value })}><option value="alumno">Alumno</option><option value="empresa">Empresa</option><option value="tutor">Tutor</option></select></label><button className="button button-primary" disabled={busy}>{busy ? 'Creando…' : 'Crear cuenta'} <ArrowUpRight size={16} /></button></form></section></div>
  );

  if (page === 'students') return (
    <div className="workspace-content"><SectionHeading eyebrow="SEGUIMIENTO DEL CENTRO" title="Alumnado tutorizado" /><section className="surface assign-row"><div><span className="eyebrow">ASIGNACIÓN</span><strong>Vincular un alumno a tu tutoría</strong></div><form onSubmit={assignStudent}><input type="number" min="1" placeholder="ID del alumno" value={studentId} onChange={(event) => setStudentId(event.target.value)} required /><button className="button button-primary"><Plus size={16} /> Asignar</button></form></section><div className="student-cards">{students.map((summary) => <article className="surface student-summary" key={summary.student.id}><div className="student-summary-top"><span className="avatar avatar-candidate">{(summary.student.full_name || summary.student.email).slice(0, 1)}</span><span><strong>{summary.student.full_name || summary.student.email}</strong><small>{summary.student.email}</small></span><span className={`profile-state ${summary.status === 'en_practicas' ? 'state-ok' : 'state-pending'}`}>{summary.status === 'en_practicas' ? 'En prácticas' : 'Sin prácticas'}</span></div><div className="summary-company"><span>{summary.company_name || 'Empresa pendiente'}</span><strong>{summary.offer_title || 'Sin candidatura aceptada'}</strong></div><div className="hours-progress"><div><span>Horas aprobadas</span><strong>{summary.total_hours_approved} / {summary.total_hours_registered} h</strong></div><div className="profile-meter"><span style={{ width: `${summary.total_hours_registered ? Math.min(100, summary.total_hours_approved / summary.total_hours_registered * 100) : 0}%` }} /></div></div><button className="button button-secondary" onClick={() => showLogs(summary)}>Revisar cuaderno <ArrowUpRight size={15} /></button></article>)}</div>{students.length === 0 && <EmptyState title="No tienes alumnado asignado" />}{logs.length > 0 && <section className="surface tutor-log-panel"><div className="surface-title"><div><span className="eyebrow">CUADERNO FCT</span><h2>Partes del alumno</h2></div></div>{logs.map((log) => <div className="log-row" key={log.id}><span>{new Date(log.date).toLocaleDateString('es-ES')}</span><span>{log.tasks}</span><strong>{log.hours} h</strong><span className="approval-pair"><i className={log.is_approved ? 'approved' : ''} /><i className={log.is_tutor_approved ? 'approved' : ''} /></span>{!log.is_tutor_approved && <button className="button button-secondary button-compact" onClick={() => approve(Number(studentId), log)}>Aprobar <Check size={14} /></button>}</div>)}</section>}</div>
  );

  if (page === 'reviews') return <div className="workspace-content"><SectionHeading eyebrow="VALIDACIÓN EDUCATIVA" title="Revisión FCT" /><section className="surface"><div className="surface-title"><div><span className="eyebrow">DOBLE VALIDACIÓN</span><h2>Selecciona un alumno</h2></div></div>{students.map((student) => <button className="student-review-row" key={student.student.id} onClick={() => showLogs(student)}><GraduationCap size={18} /><span><strong>{student.student.full_name || student.student.email}</strong><small>{student.total_hours_approved} horas aprobadas de {student.total_hours_registered}</small></span><ArrowUpRight size={16} /></button>)}</section>{logs.length > 0 && <section className="surface tutor-log-panel"><div className="surface-title"><div><span className="eyebrow">PARTES</span><h2>Por revisar</h2></div></div>{logs.map((log) => <div className="log-row" key={log.id}><span>{new Date(log.date).toLocaleDateString('es-ES')}</span><span>{log.tasks}</span><strong>{log.hours} h</strong><span className="approval-pair"><i className={log.is_approved ? 'approved' : ''} /><i className={log.is_tutor_approved ? 'approved' : ''} /></span>{!log.is_tutor_approved && <button className="button button-secondary button-compact" onClick={() => approve(Number(studentId), log)}>Aprobar <Check size={14} /></button>}</div>)}</section>}</div>;

  return null;
}

function SectionHeading({ eyebrow, title }) { return <div className="section-heading"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1></div></div>; }
function EmptyState({ title }) { return <div className="empty-state"><span className="empty-symbol"><GraduationCap size={20} /></span><strong>{title}</strong></div>; }