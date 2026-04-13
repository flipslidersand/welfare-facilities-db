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
}

export default client
