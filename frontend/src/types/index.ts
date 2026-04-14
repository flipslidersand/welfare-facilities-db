export interface Corporation {
  corporation_id: string
  name: string
  type?: string
  prefecture?: string
  city?: string
  address?: string
  updated_at: string
}

export interface Facility {
  facility_id: string
  name: string
  corporation_id?: string
  service_type?: string
  capacity?: number
  prefecture?: string
  city?: string
  updated_at: string
}

export interface CorporationFinancial {
  id: number
  corporation_id: string
  fiscal_year: number
  revenue?: number
  ordinary_profit?: number
  net_assets?: number
  total_assets?: number
  employees?: number
  collected_at: string
}

export interface RankingItem {
  rank: number
  corporation_id: string
  name: string
  prefecture?: string
  revenue?: number
  facility_count: number
  total_capacity: number
}

export interface RegionalSummary {
  prefecture: string
  corporation_count: number
  facility_count: number
  total_capacity: number
  avg_facility_capacity: number
  total_revenue?: number
}

export interface CollectionLog {
  id: number
  script_name: string
  status: 'running' | 'success' | 'failed' | 'skipped'
  records_processed: number
  error_message?: string
  started_at: string
  completed_at?: string
  created_at: string
}

export interface BackupFile {
  filename: string
  size_bytes: number
  created_at: string
}

export interface SystemMetrics {
  timestamp: string
  memory_rss_mb: number
  uptime_seconds?: number
  backup_files: BackupFile[]
  latest_backup?: BackupFile
  prometheus_url: string
  grafana_url: string
}
