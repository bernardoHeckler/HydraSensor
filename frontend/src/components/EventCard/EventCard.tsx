import React from 'react';
import clsx from 'clsx';
import { CheckCircle2, XCircle, Clock } from 'lucide-react';
import styles from './EventCard.module.css';

export interface RFIDEvent {
  collaborator_name: string;
  event_type: string;
  authorized: boolean;
  tag_id: string;
  message: string;
  read_at: string;
}

interface EventCardProps {
  event: RFIDEvent;
  highlight?: boolean;
}

const EventCard: React.FC<EventCardProps> = ({ event, highlight = false }) => {
  return (
    <div className={clsx(styles.card, highlight && styles.highlight)}>
      <div className={styles.header}>
        <div className={styles.titleWrapper}>
          <span className={styles.title}>{event.collaborator_name}</span>
          <span className={styles.subtitle}>{event.event_type}</span>
        </div>
        <div className={clsx(styles.badge, event.authorized ? styles.badgeSuccess : styles.badgeDanger)}>
          {event.authorized ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
          <span>{event.authorized ? 'Autorizado' : 'Negado'}</span>
        </div>
      </div>

      <div className={styles.body}>
        <div className={styles.infoRow}>
          <span className={styles.label}>Tag ID:</span>
          <span className={styles.value}>{event.tag_id}</span>
        </div>
        <div className={styles.infoRow}>
          <span className={styles.label}>Mensagem:</span>
          <span className={styles.value}>{event.message}</span>
        </div>
      </div>

      <div className={styles.footer}>
        <Clock size={14} className={styles.timeIcon} />
        <span className={styles.timeText}>{event.read_at}</span>
      </div>
    </div>
  );
};

export default EventCard;
