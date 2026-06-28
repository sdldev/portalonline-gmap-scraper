export interface UserResponse {
  user_id: string
  username: string
  role: string
  api_key: string
  active: boolean
  webhook_url: string | null
  webhook_events: string | null
  created_at: string
}

export interface LoginResponse {
  success: boolean
  token: string
  user_id: string
  username: string
  role: string
}

export interface DashboardStats {
  total_users: number
  total_jobs: number
  total_leads: number
  active_jobs: number
  queued_jobs: number
  recent_jobs: RecentJob[]
}

export interface RecentJob {
  job_id: string
  keyword: string
  location: string | null
  status: JobStatus
  leads_collected: number
  leads_total: number
  created_at: string
}

export type JobStatus = "queued" | "running" | "completed" | "failed" | "cancelled"

export interface JobResponse {
  job_id: string
  user_id: string
  username: string
  keyword: string
  location: string | null
  query: string
  status: JobStatus
  target: number
  smart: boolean
  queue_position: number | null
  leads_collected: number
  leads_total: number
  error: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface JobsPage {
  jobs: JobResponse[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface LeadResponse {
  id: number
  job_id: string
  user_id: string
  keyword: string
  name: string
  address: string
  phone: string
  website: string
  rating: string
  review_count: string
  scraped_at: string
}

export interface LeadsPage {
  results: LeadResponse[]
  total: number
  page: number
  limit: number
}

export interface SSEProgress {
  event: string
  job_id?: string
  leads_collected?: number
  total_leads?: number
  lead?: LeadResponse
  status?: JobStatus
  old?: JobStatus
  new?: JobStatus
}

export interface JobCreatePayload {
  keyword: string
  location?: string
  target?: number
  smart?: boolean
  category_variations?: string[]
  timeout_minutes?: number
}

export interface UserCreatePayload {
  username: string
  role?: string
}

export interface UserUpdatePayload {
  username?: string
  role?: string
  active?: boolean
}
