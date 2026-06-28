import api from "./api"
import type { JobCreatePayload, JobResponse, JobsPage, LeadResponse } from "@/types"

export async function createJob(payload: JobCreatePayload): Promise<JobResponse> {
  const { data } = await api.post("/jobs", payload)
  return data
}

export async function listJobs(params: {
  page?: number
  limit?: number
  status?: string
  keyword?: string
  user_id?: string
} = {}): Promise<JobsPage> {
  const { data } = await api.get("/jobs", { params })
  return data
}

export async function getJob(jobId: string): Promise<JobResponse> {
  const { data } = await api.get(`/jobs/${jobId}`)
  return data
}

export async function cancelJob(jobId: string): Promise<void> {
  await api.delete(`/jobs/${jobId}`)
}

export async function getJobResults(
  jobId: string,
  format: "json" | "csv" = "json"
): Promise<{ results: LeadResponse[]; total: number; job_id: string }> {
  const { data } = await api.get(`/jobs/${jobId}/results`, { params: { format } })
  return data
}

export function getJobStreamUrl(token: string, jobId: string): string {
  return `/api/v1/jobs/${jobId}/stream?token=${token}`
}


export async function deleteJob(jobId: string): Promise<void> {
  await api.delete(`/jobs/${jobId}`)
}
