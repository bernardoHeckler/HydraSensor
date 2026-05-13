import React from 'react';
import clsx from 'clsx';
import { CheckCircle2, Clock, DoorClosed, DoorOpen, ShieldAlert, XCircle } from 'lucide-react';
import { RFIDEvent } from '../../types';
import styles from './EventCard.module.css';

interface EventCardProps {
  event: RFIDEvent;
  highlight?: boolean;
  compact?: boolean;
}

const eventLabels: Record<string, string> = {
  entrada: 'Entrada',
  saida: 'Saida',
  acesso_negado: 'Acesso negado',
  invasao: 'Invasao',
};

const getEventIcon = (eventType: string) => {
  if (eventType === 'entrada') return <DoorOpen size={16} />;
  if (eventType === 'saida') return <DoorClosed size={16} />;
  if (eventType === 'invasao') return <ShieldAlert size={16} />;
  return <XCircle size={16} />;
};

const formatDate = (value: string) => {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(date);
};

const EventCard: React.FC<EventCardProps> = ({ event, highlight = false, compact = false }) => {
  const authorized = Boolean(event.authorized);
  const eventLabel = eventLabels[event.event_type] || event.event_type;

  return (
    <div className={clsx(styles.card, highlight && styles.highlight, compact && styles.compact)}>
      <div className={styles.header}>
        <div className={styles.titleWrapper}>
          <span className={styles.title}>{event.collaborator_name || 'Desconhecido'}</span>
          <span className={styles.subtitle}>
            {getEventIcon(event.event_type)}
            {eventLabel}
          </span>
        </div>
        <div className={clsx(styles.badge, authorized ? styles.badgeSuccess : styles.badgeDanger)}>
          {authorized ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
          <span>{authorized ? 'Autorizado' : 'Negado'}</span>
        </div>
      </div>

      <div className={styles.body}>
        <div className={styles.infoRow}>
          <span className={styles.label}>Tag</span>
          <span className={styles.value}>{event.tag_id}</span>
        </div>
        {event.registration && (
          <div className={styles.infoRow}>
            <span className={styles.label}>Matricula</span>
            <span className={styles.value}>{event.registration}</span>
          </div>
        )}
        <div className={styles.infoRow}>
          <span className={styles.label}>Mensagem</span>
          <span className={styles.value}>{event.message}</span>
        </div>
      </div>

      <div className={styles.footer}>
        <Clock size={14} className={styles.timeIcon} />
        <span className={styles.timeText}>{formatDate(event.read_at)}</span>
        {event.origin && <span className={styles.origin}>{event.origin}</span>}
      </div>
    </div>
  );
};

export default EventCard;
