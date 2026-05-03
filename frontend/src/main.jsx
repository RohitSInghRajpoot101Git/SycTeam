import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { CheckCircle2, ClipboardList, FolderKanban, LogOut, Plus, Users } from 'lucide-react';
import './styles.css';

const API = import.meta.env.VITE_API_URL || '/api';
const statuses = ['Todo', 'In Progress', 'Done'];

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || 'null'));
  const [authMode, setAuthMode] = useState('login');
  const [error, setError] = useState('');

  const auth = async (event) => {
    event.preventDefault();
    setError('');
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    try {
      const data = await request(`/auth/${authMode}`, { method: 'POST', body: payload });
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      setToken(data.token);
      setUser(data.user);
    } catch (err) {
      setError(err.message);
    }
  };

  if (!token) {
    return (
      <main className="auth-page">
        <section className="auth-panel">
          <div>
            <p className="eyebrow">Full-stack assignment</p>
            <h1>Team Task Manager</h1>
            <p className="muted">Create projects, assign work, and track progress with Admin and Member access.</p>
          </div>
          <div className="tabs">
            <button className={authMode === 'login' ? 'active' : ''} onClick={() => setAuthMode('login')}>Login</button>
            <button className={authMode === 'signup' ? 'active' : ''} onClick={() => setAuthMode('signup')}>Signup</button>
          </div>
          <form onSubmit={auth} className="stack">
            {authMode === 'signup' && <input name="name" placeholder="Name" required minLength="2" />}
            <input name="email" placeholder="Email" type="email" required />
            <input name="password" placeholder="Password" type="password" required minLength="6" />
            {error && <p className="error">{error}</p>}
            <button className="primary" type="submit">{authMode === 'login' ? 'Login' : 'Create account'}</button>
          </form>
        </section>
      </main>
    );
  }

  return <Workspace token={token} user={user} onLogout={() => {
    localStorage.clear();
    setToken('');
    setUser(null);
  }} />;
}

function Workspace({ token, user, onLogout }) {
  const [projects, setProjects] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [tasks, setTasks] = useState([]);
  const [members, setMembers] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [message, setMessage] = useState('');

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === Number(selectedId)),
    [projects, selectedId]
  );

  const api = (path, options = {}) => request(path, options, token);
  const handleError = (err) => {
    if (err.status === 401) {
      setMessage('Session expired. Please login again.');
      setTimeout(onLogout, 900);
      return;
    }
    setMessage(err.message || 'Something went wrong');
  };

  const load = async (preferredProjectId = '') => {
    const [projectData, dashboardData] = await Promise.all([api('/projects'), api('/dashboard')]);
    setProjects(projectData);
    setDashboard(dashboardData);
    setSelectedId((currentSelectedId) => {
      const preferredId = preferredProjectId ? String(preferredProjectId) : '';
      if (preferredId && projectData.some((project) => String(project.id) === preferredId)) {
        return preferredId;
      }
      if (currentSelectedId && projectData.some((project) => String(project.id) === String(currentSelectedId))) {
        return currentSelectedId;
      }
      return projectData[0] ? String(projectData[0].id) : '';
    });
  };

  const loadProjectData = async () => {
    if (!selectedId) {
      setTasks([]);
      setMembers([]);
      return;
    }
    const [taskData, memberData] = await Promise.all([
      api(`/tasks?project_id=${selectedId}`),
      api(`/projects/${selectedId}/members`),
    ]);
    setTasks(taskData);
    setMembers(memberData);
  };

  useEffect(() => { load().catch(handleError); }, []);
  useEffect(() => { loadProjectData().catch(handleError); }, [selectedId]);

  const submitProject = async (event) => {
    event.preventDefault();
    setMessage('');
    try {
      const form = new FormData(event.currentTarget);
      const project = await api('/projects', { method: 'POST', body: Object.fromEntries(form.entries()) });
      event.currentTarget.reset();
      await load(project.id);
    } catch (err) {
      handleError(err);
    }
  };

  const submitMember = async (event) => {
    event.preventDefault();
    setMessage('');
    try {
      const form = new FormData(event.currentTarget);
      await api(`/projects/${selectedId}/members`, { method: 'POST', body: Object.fromEntries(form.entries()) });
      event.currentTarget.reset();
      await loadProjectData();
    } catch (err) {
      handleError(err);
    }
  };

  const submitTask = async (event) => {
    event.preventDefault();
    setMessage('');
    try {
      const form = new FormData(event.currentTarget);
      const body = Object.fromEntries(form.entries());
      body.assignee_id = body.assignee_id ? Number(body.assignee_id) : null;
      body.due_date = body.due_date || null;
      await api(`/projects/${selectedId}/tasks`, { method: 'POST', body });
      event.currentTarget.reset();
      await Promise.all([load(), loadProjectData()]);
    } catch (err) {
      handleError(err);
    }
  };

  const updateStatus = async (task, status) => {
    setMessage('');
    try {
      await api(`/tasks/${task.id}`, { method: 'PATCH', body: { status } });
      await Promise.all([load(), loadProjectData()]);
    } catch (err) {
      handleError(err);
    }
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Signed in as {user?.name}</p>
          <h1>Team Task Manager</h1>
        </div>
        <button className="ghost" onClick={onLogout}><LogOut size={18} /> Logout</button>
      </header>

      {dashboard && (
        <section className="metrics">
          <Metric icon={<FolderKanban />} label="Projects" value={dashboard.projects} />
          <Metric icon={<ClipboardList />} label="Tasks" value={dashboard.total_tasks} />
          <Metric icon={<CheckCircle2 />} label="Done" value={dashboard.done} />
          <Metric icon={<ClipboardList />} label="Overdue" value={dashboard.overdue} tone="danger" />
        </section>
      )}

      <section className="grid">
        <aside className="panel">
          <h2>Projects</h2>
          <form onSubmit={submitProject} className="stack">
            <input name="name" placeholder="Project name" required minLength="2" />
            <textarea name="description" placeholder="Description" rows="3" />
            <button className="primary" type="submit"><Plus size={17} /> Add project</button>
          </form>
          <div className="list">
            {projects.map((project) => (
              <button
                key={project.id}
                className={`project-row ${project.id === Number(selectedId) ? 'active' : ''}`}
                onClick={() => setSelectedId(String(project.id))}
              >
                <span>{project.name}</span>
                <small>{project.role}</small>
              </button>
            ))}
          </div>
        </aside>

        <section className="panel main-panel">
          {!selectedProject ? (
            <p className="muted">Create a project to start assigning work.</p>
          ) : (
            <>
              <div className="section-head">
                <div>
                  <h2>{selectedProject.name}</h2>
                  <p className="muted">{selectedProject.description || 'No description added.'}</p>
                </div>
                <span className="badge">{selectedProject.role}</span>
              </div>

              <div className="split">
                <form onSubmit={submitTask} className="stack framed">
                  <h3>New task</h3>
                  <input name="title" placeholder="Task title" required minLength="2" />
                  <textarea name="description" placeholder="Description" rows="3" />
                  <select name="assignee_id">
                    <option value="">Unassigned</option>
                    {members.map((member) => <option key={member.user.id} value={member.user.id}>{member.user.name}</option>)}
                  </select>
                  <input name="due_date" type="date" />
                  <button className="primary" type="submit"><Plus size={17} /> Add task</button>
                </form>

                <form onSubmit={submitMember} className="stack framed">
                  <h3><Users size={17} /> Team</h3>
                  <input name="email" placeholder="Member email" type="email" required />
                  <select name="role" defaultValue="Member">
                    <option>Member</option>
                    <option>Admin</option>
                  </select>
                  <button type="submit">Add or update member</button>
                  <div className="member-list">
                    {members.map((member) => <p key={member.id}>{member.user.name} <span>{member.role}</span></p>)}
                  </div>
                </form>
              </div>

              <div className="tasks">
                {tasks.map((task) => (
                  <article className="task-card" key={task.id}>
                    <div>
                      <h3>{task.title}</h3>
                      <p>{task.description || 'No description.'}</p>
                      <small>{task.assignee ? `Assigned to ${task.assignee.name}` : 'Unassigned'} {task.due_date ? `• Due ${task.due_date}` : ''}</small>
                    </div>
                    <select value={task.status} onChange={(event) => updateStatus(task, event.target.value)}>
                      {statuses.map((status) => <option key={status}>{status}</option>)}
                    </select>
                  </article>
                ))}
                {tasks.length === 0 && <p className="muted">No tasks yet.</p>}
              </div>
            </>
          )}
        </section>
      </section>
      {message && <p className="toast">{message}</p>}
    </main>
  );
}

function Metric({ icon, label, value, tone = '' }) {
  return <div className={`metric ${tone}`}>{React.cloneElement(icon, { size: 22 })}<span>{label}</span><strong>{value}</strong></div>;
}

async function request(path, options = {}, token = '') {
  const response = await fetch(`${API}${path}`, {
    method: options.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.detail || 'Request failed');
    error.status = response.status;
    throw error;
  }
  return data;
}

createRoot(document.getElementById('root')).render(<App />);
