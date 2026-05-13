import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PubNub from 'pubnub';
import {
  Activity,
  AlertTriangle,
  DoorClosed,
  DoorOpen,
  Download,
  LogOut,
  RefreshCw,
  Save,
  Shield,
  UserCheck,
  Users,
} from 'lucide-react';
import EventCard from '../../components/EventCard/EventCard';
import Button from '../../components/Button/Button';
import Input from '../../components/Input/Input';
import { apiRequest } from '../../services/api';
import { Collaborator, CollaboratorFormData, MonitoringSummary, RFIDEvent } from '../../types';
import styles from './Dashboard.module.css';

const PUBNUB_SUBSCRIBE_KEY = import.meta.env.VITE_PUBNUB_SUBSCRIBE_KEY || 'sub-c-7830b8bc-9ccc-4f70-b89d-0a22951b20a8';
const PUBNUB_CHANNEL = import.meta.env.VITE_PUBNUB_CHANNEL || 'meu_canal';

type ActiveView = 'monitoring' | 'collaborators' | 'logs';

type PubNubMessageEnvelope = {
  data?: RFIDEvent;
};

const emptySummary: MonitoringSummary = {
  latest_entries: [],
  latest_exits: [],
  denied_attempts: [],
  intrusion_attempts: [],
  people_inside: [],
  recent_alerts: [],
};

const emptyForm: CollaboratorFormData = {
  name: '',
  registration: '',
  rfid_tag: '',
  role: '',
  has_room_access: true,
  is_active: true,
};

const formatBoolean = (value: boolean | number) => (Boolean(value) ? 'Sim' : 'Nao');

const Dashboard: React.FC = () => {
  const [events, setEvents] = useState<RFIDEvent[]>([]);
  const [summary, setSummary] = useState<MonitoringSummary>(emptySummary);
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [formData, setFormData] = useState<CollaboratorFormData>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [activeView, setActiveView] = useState<ActiveView>('monitoring');
  const [connectionStatus, setConnectionStatus] = useState('Conectando...');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      navigate('/login', { replace: true });
    }
  }, [navigate]);

  const fetchEvents = async () => {
    const payload = await apiRequest<RFIDEvent[]>('/v1/access-events');
    setEvents(payload.data);
  };

  const fetchSummary = async () => {
    const payload = await apiRequest<MonitoringSummary>('/v1/monitoring/summary');
    setSummary(payload.data);
  };

  const fetchCollaborators = async () => {
    const payload = await apiRequest<Collaborator[]>('/v1/collaborators?limit=100');
    setCollaborators(payload.data);
  };

  const refreshAll = async () => {
    setError('');

    try {
      await Promise.all([fetchEvents(), fetchSummary(), fetchCollaborators()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar dados.');
    }
  };

  useEffect(() => {
    void refreshAll();

    const intervalId = window.setInterval(() => {
      void fetchSummary().catch(() => undefined);
    }, 10000);

    const pubnub = new PubNub({
      subscribeKey: PUBNUB_SUBSCRIBE_KEY,
      userId: 'rfid-dashboard-react',
    });

    pubnub.addListener({
      status: (statusEvent) => {
        if (statusEvent.category === 'PNConnectedCategory') {
          setConnectionStatus('Conectado em tempo real');
          setIsConnected(true);
        } else if (statusEvent.category === 'PNDisconnectedCategory') {
          setConnectionStatus('Desconectado');
          setIsConnected(false);
        }
      },
      message: (messageEvent) => {
        const payload = messageEvent.message as PubNubMessageEnvelope;
        const event = payload.data;

        if (event) {
          setEvents((prevEvents) => [event, ...prevEvents].slice(0, 50));
          void fetchSummary().catch(() => undefined);
        }
      },
    });

    pubnub.subscribe({ channels: [PUBNUB_CHANNEL] });

    return () => {
      window.clearInterval(intervalId);
      pubnub.unsubscribeAll();
    };
  }, []);

  const latestEvent = events[0];
  const stats = useMemo(() => {
    const entries = events.filter((event) => event.event_type === 'entrada').length;
    const exits = events.filter((event) => event.event_type === 'saida').length;
    const denied = events.filter((event) => event.event_type === 'acesso_negado').length;
    const intrusions = events.filter((event) => event.event_type === 'invasao').length;

    return { entries, exits, denied, intrusions };
  }, [events]);

  const resetForm = () => {
    setFormData(emptyForm);
    setEditingId(null);
  };

  const editCollaborator = (collaborator: Collaborator) => {
    setEditingId(collaborator.id);
    setFormData({
      name: collaborator.name,
      registration: collaborator.registration,
      rfid_tag: collaborator.rfid_tag || '',
      role: collaborator.role,
      has_room_access: Boolean(collaborator.has_room_access),
      is_active: Boolean(collaborator.is_active),
    });
    setActiveView('collaborators');
  };

  const submitCollaborator = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setNotice('');

    try {
      const method = editingId ? 'PUT' : 'POST';
      const path = editingId ? `/v1/collaborators/${editingId}` : '/v1/collaborators';

      await apiRequest<Collaborator>(path, {
        method,
        body: JSON.stringify(formData),
      });

      setNotice(editingId ? 'Colaborador atualizado.' : 'Colaborador cadastrado.');
      resetForm();
      await fetchCollaborators();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar colaborador.');
    } finally {
      setLoading(false);
    }
  };

  const disableCollaborator = async (collaboratorId: number) => {
    setError('');
    setNotice('');

    try {
      await apiRequest<void>(`/v1/collaborators/${collaboratorId}`, { method: 'DELETE' });
      setNotice('Colaborador marcado como inativo.');
      await fetchCollaborators();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao inativar colaborador.');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.logoWrapper}>
            <Shield size={24} className={styles.logoIcon} />
          </div>
          <div>
            <h1 className={styles.title}>HydraSensor</h1>
            <div className={styles.statusWrapper}>
              <span className={isConnected ? styles.statusDotConnected : styles.statusDotDisconnected} />
              <span className={styles.statusText}>{connectionStatus}</span>
            </div>
          </div>
        </div>
        <div className={styles.headerActions}>
          <Button variant="secondary" onClick={() => void refreshAll()}>
            <RefreshCw size={16} />
            <span>Atualizar</span>
          </Button>
          <Button variant="secondary" onClick={handleLogout} className={styles.logoutBtn}>
            <LogOut size={16} />
            <span>Sair</span>
          </Button>
        </div>
      </header>

      <main className={styles.main}>
        <nav className={styles.tabs} aria-label="Areas do painel">
          <button className={activeView === 'monitoring' ? styles.tabActive : styles.tab} onClick={() => setActiveView('monitoring')}>
            <Activity size={16} />
            Monitoramento
          </button>
          <button className={activeView === 'collaborators' ? styles.tabActive : styles.tab} onClick={() => setActiveView('collaborators')}>
            <Users size={16} />
            Colaboradores
          </button>
          <button className={activeView === 'logs' ? styles.tabActive : styles.tab} onClick={() => setActiveView('logs')}>
            <Download size={16} />
            Logs
          </button>
        </nav>

        {(error || notice) && (
          <div className={error ? styles.messageError : styles.messageSuccess}>
            {error || notice}
          </div>
        )}

        {activeView === 'monitoring' && (
          <div className={styles.monitoringLayout}>
            <section className={styles.metricsGrid}>
              <div className={styles.metric}>
                <DoorOpen size={18} />
                <span>Entradas</span>
                <strong>{stats.entries}</strong>
              </div>
              <div className={styles.metric}>
                <DoorClosed size={18} />
                <span>Saidas</span>
                <strong>{stats.exits}</strong>
              </div>
              <div className={styles.metric}>
                <UserCheck size={18} />
                <span>Na sala</span>
                <strong>{summary.people_inside.length}</strong>
              </div>
              <div className={styles.metricDanger}>
                <AlertTriangle size={18} />
                <span>Alertas</span>
                <strong>{stats.denied + stats.intrusions}</strong>
              </div>
            </section>

            <section className={styles.latestSection}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>Ultima leitura</h2>
              </div>
              {latestEvent ? (
                <EventCard event={latestEvent} highlight />
              ) : (
                <div className={styles.emptyState}>
                  <Activity size={40} className={styles.emptyIcon} />
                  <p>Aguardando aproximacao da tag.</p>
                </div>
              )}
            </section>

            <section className={styles.panel}>
              <h2 className={styles.sectionTitle}>Colaboradores dentro da sala</h2>
              <div className={styles.peopleList}>
                {summary.people_inside.length > 0 ? summary.people_inside.map((person) => (
                  <div className={styles.personRow} key={person.id}>
                    <div>
                      <strong>{person.name}</strong>
                      <span>{person.role} | {person.registration}</span>
                    </div>
                    <span className={styles.accessBadge}>Dentro</span>
                  </div>
                )) : (
                  <p className={styles.muted}>Nenhum colaborador registrado dentro da sala.</p>
                )}
              </div>
            </section>

            <section className={styles.eventColumns}>
              <EventList title="Entradas autorizadas" events={summary.latest_entries} />
              <EventList title="Saidas registradas" events={summary.latest_exits} />
              <EventList title="Acessos negados" events={summary.denied_attempts} />
              <EventList title="Tags desconhecidas" events={summary.intrusion_attempts} />
              <EventList title="Alertas recentes" events={summary.recent_alerts} />
            </section>
          </div>
        )}

        {activeView === 'collaborators' && (
          <div className={styles.managementGrid}>
            <section className={styles.panel}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>{editingId ? 'Editar colaborador' : 'Cadastrar colaborador'}</h2>
                {editingId && (
                  <Button type="button" variant="secondary" onClick={resetForm}>
                    Novo
                  </Button>
                )}
              </div>

              <form className={styles.form} onSubmit={submitCollaborator}>
                <Input label="Nome" value={formData.name} onChange={(event) => setFormData({ ...formData, name: event.target.value })} required />
                <Input label="Matricula" value={formData.registration} onChange={(event) => setFormData({ ...formData, registration: event.target.value })} required />
                <Input label="Tag RFID" value={formData.rfid_tag} onChange={(event) => setFormData({ ...formData, rfid_tag: event.target.value })} placeholder="Opcional" />
                <Input label="Cargo" value={formData.role} onChange={(event) => setFormData({ ...formData, role: event.target.value })} required />

                <label className={styles.checkboxRow}>
                  <input type="checkbox" checked={formData.has_room_access} onChange={(event) => setFormData({ ...formData, has_room_access: event.target.checked })} />
                  Possui acesso a sala do projeto
                </label>
                <label className={styles.checkboxRow}>
                  <input type="checkbox" checked={formData.is_active} onChange={(event) => setFormData({ ...formData, is_active: event.target.checked })} />
                  Colaborador ativo
                </label>

                <Button type="submit" disabled={loading}>
                  <Save size={16} />
                  {loading ? 'Salvando...' : 'Salvar'}
                </Button>
              </form>
            </section>

            <section className={styles.panel}>
              <h2 className={styles.sectionTitle}>Lista de colaboradores</h2>
              <div className={styles.tableWrap}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>Nome</th>
                      <th>Matricula</th>
                      <th>Tag</th>
                      <th>Acesso</th>
                      <th>Status</th>
                      <th>Acoes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {collaborators.map((collaborator) => (
                      <tr key={collaborator.id}>
                        <td>
                          <strong>{collaborator.name}</strong>
                          <span>{collaborator.role}</span>
                        </td>
                        <td>{collaborator.registration}</td>
                        <td>{collaborator.rfid_tag || '-'}</td>
                        <td>{formatBoolean(collaborator.has_room_access)}</td>
                        <td>{Boolean(collaborator.is_active) ? 'Ativo' : 'Inativo'}</td>
                        <td>
                          <div className={styles.rowActions}>
                            <button type="button" onClick={() => editCollaborator(collaborator)}>Editar</button>
                            <button type="button" onClick={() => void disableCollaborator(collaborator.id)}>Inativar</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}

        {activeView === 'logs' && (
          <div className={styles.logsLayout}>
            <section className={styles.panel}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>Logs de acesso</h2>
                <a className={styles.exportLink} href="/v1/access-events/export.csv">
                  <Download size={16} />
                  Exportar CSV
                </a>
              </div>
              <div className={styles.historyList}>
                {events.length > 0 ? events.map((event, index) => (
                  <EventCard key={`${event.tag_id}-${event.read_at}-${index}`} event={event} compact />
                )) : (
                  <div className={styles.emptyStateSmall}>
                    <p>Nenhum evento registrado.</p>
                  </div>
                )}
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
};

interface EventListProps {
  title: string;
  events: RFIDEvent[];
}

const EventList: React.FC<EventListProps> = ({ title, events }) => (
  <section className={styles.panel}>
    <h2 className={styles.sectionTitle}>{title}</h2>
    <div className={styles.compactList}>
      {events.length > 0 ? events.slice(0, 5).map((event, index) => (
        <EventCard key={`${event.tag_id}-${event.read_at}-${index}`} event={event} compact />
      )) : (
        <p className={styles.muted}>Sem registros.</p>
      )}
    </div>
  </section>
);

export default Dashboard;
