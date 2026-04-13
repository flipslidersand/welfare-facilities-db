import axios from 'axios'
import type { Corporation, Facility, RankingItem, RegionalSummary } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const corporationsAPI = {
  list: (skip = 0, limit = 100, prefecture?: string, type?: string) =>
    client.get<Corporation[]>('/corporations', {
      params: { skip, limit, prefecture, type },
    }),

  detail: (id: string) =>
    client.get<Corporation>(`/corporations/${id}`),

  financials: (id: string, years?: string) =>
    client.get(`/corporations/${id}/financials`, {
      params: { years },
    }),

  facilities: (id: string) =>
    client.get(`/corporations/${id}/facilities`),
}

export const facilitiesAPI = {
  list: (skip = 0, limit = 100, prefecture?: string, serviceType?: string) =>
    client.get<Facility[]>('/facilities', {
      params: { skip, limit, prefecture, service_type: serviceType },
    }),

  detail: (id: string) =>
    client.get<Facility>(`/facilities/${id}`),

  prefectureSummary: (prefecture: string) =>
    client.get(`/facilities/prefecture/${prefecture}/summary`),
}

export const analyticsAPI = {
  ranking: (fiscalYear: number, limit = 20) =>
    client.get<{ fiscal_year: number; timestamp: string; data: RankingItem[] }>(
      '/analytics/ranking',
      { params: { fiscal_year: fiscalYear, limit } }
    ),

  regional: (fiscalYear?: number) =>
    client.get<{ fiscal_year?: number; timestamp: string; data: RegionalSummary[] }>(
      '/analytics/regional',
      { params: { fiscal_year: fiscalYear } }
    ),

  summary: () =>
    client.get('/analytics/summary'),

  serviceTypeStats: (fiscalYear?: number, prefecture?: string) =>
    client.get('/analytics/service-type-stats', {
      params: { fiscal_year: fiscalYear, prefecture }
    }),

  yearCompare: (corporationId?: string, prefecture?: string) =>
    client.get('/analytics/year-compare', {
      params: { corporation_id: corporationId, prefecture }
    }),

  topPrefectures: (fiscalYear: number, metric: string = 'revenue', limit = 10) =>
    client.get('/analytics/top-prefectures', {
      params: { fiscal_year: fiscalYear, metric, limit }
    }),
}

export const collectionAPI = {
  list: (skip = 0, limit = 100, scriptName?: string, status?: string) =>
    client.get('/collection-logs', {
      params: { skip, limit, script_name: scriptName, status }
    }),

  detail: (logId: number) =>
    client.get(`/collection-logs/${logId}`),

  trigger: (scriptName: string) =>
    client.post(`/collection-logs/trigger/${scriptName}`),

  stats: () =>
    client.get('/collection-logs/stats/summary'),
}

export default client
