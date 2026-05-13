import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PubNub from 'pubnub';
import { LogOut, Activity } from 'lucide-react';
import EventCard, { RFIDEvent } from '../../components/EventCard/EventCard';
import Button from '../../components/Button/Button';
import styles from './Dashboard.module.css';

const PUBNUB_SUBSCRIBE_KEY = 'sub-c-7830b8bc-9ccc-4f70-b89d-0a22951b20a8';
const PUBNUB_CHANNEL = 'meu_canal';

type AccessEventsResponse = {
  data?: RFIDEvent[];
};

type PubNubMessageEnvelope = {
  data?: RFIDEvent;
};

const Dashboard: React.FC = () => {
  const [events, setEvents] = useState<RFIDEvent[]>([]);
  const [connectionStatus, setConnectionStatus] = useState('Conectando...');
  const [isConnected, setIsConnected] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch('/v1/access-events');
        const data = (await res.json()) as AccessEventsResponse;

        if (res.ok && Array.isArray(data.data)) {
          setEvents(data.data);
        }
      } catch (err) {
        console.error('Erro ao buscar historico inicial', err);
      }
    };

    fetchHistory();

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
          setEvents((prevEvents) => [event, ...prevEvents]);
        }
      },
    });

    pubnub.subscribe({ channels: [PUBNUB_CHANNEL] });

    return () => {
      pubnub.unsubscribeAll();
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const latestEvent = events[0];
  const historyEvents = events.slice(1);

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.logoWrapper}>
            <Activity size={24} className={styles.logoIcon} />
          </div>
          <div>
            <h1 className={styles.title}>Monitor de Acessos</h1>
            <div className={styles.statusWrapper}>
              <span className={isConnected ? styles.statusDotConnected : styles.statusDotDisconnected} />
              <span className={styles.statusText}>{connectionStatus}</span>
            </div>
          </div>
        </div>
        <Button variant="secondary" onClick={handleLogout} className={styles.logoutBtn}>
          <LogOut size={16} />
          <span>Sair</span>
        </Button>
      </header>

      <main className={styles.main}>
        <div className={styles.grid}>
          <section className={styles.latestSection}>
            <h2 className={styles.sectionTitle}>Ultima Leitura</h2>
            {latestEvent ? (
              <EventCard event={latestEvent} highlight />
            ) : (
              <div className={styles.emptyState}>
                <Activity size={48} className={styles.emptyIcon} />
                <p>Aguardando aproximacao da tag...</p>
              </div>
            )}
          </section>

          <section className={styles.historySection}>
            <h2 className={styles.sectionTitle}>Historico de leituras</h2>
            <div className={styles.historyList}>
              {historyEvents.length > 0 ? (
                historyEvents.map((ev, index) => (
                  <EventCard key={`${ev.tag_id}-${index}`} event={ev} />
                ))
              ) : (
                <div className={styles.emptyStateSmall}>
                  <p>Nenhum evento anterior registrado.</p>
                </div>
              )}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
