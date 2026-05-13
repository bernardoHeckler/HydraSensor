export interface RFIDEvent {
  collaborator_id?: number | null;
  collaborator_name: string;
  registration?: string | null;
  event_type: 'entrada' | 'saida' | 'acesso_negado' | 'invasao' | string;
  authorized: boolean | number;
  tag_id: string;
  origin?: string;
  message: string;
  read_at: string;
  created_at?: string;
  synced?: boolean | number;
}

export interface Collaborator {
  id: number;
  name: string;
  registration: string;
  rfid_tag?: string | null;
  role: string;
  has_room_access: boolean | number;
  is_active: boolean | number;
  created_at?: string;
  updated_at?: string;
}

export interface MonitoringSummary {
  latest_entries: RFIDEvent[];
  latest_exits: RFIDEvent[];
  denied_attempts: RFIDEvent[];
  intrusion_attempts: RFIDEvent[];
  people_inside: Collaborator[];
  recent_alerts: RFIDEvent[];
}

export type CollaboratorFormData = {
  name: string;
  registration: string;
  rfid_tag: string;
  role: string;
  has_room_access: boolean;
  is_active: boolean;
};

