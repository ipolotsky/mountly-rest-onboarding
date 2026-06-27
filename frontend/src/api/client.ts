import axios from "axios";
import type { AxiosInstance } from "axios";
import type {
  AdminFeedbackRow,
  AdminMetrics,
  AdminOnboardingRow,
  AnalyticsEvent,
  BankingBlock,
  Device,
  FeedbackPayload,
  LegalBlock,
  Locale,
  MenuBlock,
  Onboarding,
  Step,
} from "@/types/contract";

const API_BASE = (import.meta.env.VITE_API_BASE ?? "") + "/api";

function buildHttp(): AxiosInstance {
  return axios.create({
    baseURL: API_BASE,
    headers: { "Content-Type": "application/json" },
    timeout: 60000,
  });
}

const http = buildHttp();

function buildFormData(files: File[], note: string | null): FormData {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  if (note != null && note.length > 0) {
    form.append("note", note);
  }
  return form;
}

export const apiBaseUrl = API_BASE;

export async function createOnboarding(locale: Locale, device: Device): Promise<{ id: string }> {
  const response = await http.post<{ id: string }>("/onboarding", { locale, device });
  return response.data;
}

export async function fetchOnboarding(id: string): Promise<Onboarding> {
  const response = await http.get<Onboarding>(`/onboarding/${id}`);
  return response.data;
}

export async function fetchRestaurant(id: string): Promise<Onboarding> {
  const response = await http.get<Onboarding>(`/onboarding/${id}/restaurant`);
  return response.data;
}

export async function parseLegal(id: string, files: File[], note: string | null): Promise<LegalBlock> {
  const response = await http.post<LegalBlock>(`/onboarding/${id}/legal/parse`, buildFormData(files, note), {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function saveLegal(id: string, block: LegalBlock): Promise<LegalBlock> {
  const response = await http.put<LegalBlock>(`/onboarding/${id}/legal`, block);
  return response.data;
}

export async function parseBanking(id: string, files: File[], note: string | null): Promise<BankingBlock> {
  const response = await http.post<BankingBlock>(`/onboarding/${id}/banking/parse`, buildFormData(files, note), {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function saveBanking(id: string, block: BankingBlock): Promise<BankingBlock> {
  const response = await http.put<BankingBlock>(`/onboarding/${id}/banking`, block);
  return response.data;
}

export async function parseMenu(id: string, files: File[], note: string | null): Promise<MenuBlock> {
  const response = await http.post<MenuBlock>(`/onboarding/${id}/menu/parse`, buildFormData(files, note), {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function saveMenu(id: string, block: MenuBlock): Promise<MenuBlock> {
  const response = await http.put<MenuBlock>(`/onboarding/${id}/menu`, block);
  return response.data;
}

export async function confirmStep(id: string, step: Step): Promise<Onboarding> {
  const response = await http.post<Onboarding>(`/onboarding/${id}/confirm`, { step });
  return response.data;
}

export async function publishOnboarding(id: string): Promise<Onboarding> {
  const response = await http.post<Onboarding>(`/onboarding/${id}/publish`);
  return response.data;
}

export async function submitFeedback(id: string, payload: FeedbackPayload): Promise<{ ok: true }> {
  const response = await http.post<{ ok: true }>(`/onboarding/${id}/feedback`, payload);
  return response.data;
}

export async function sendEvents(events: AnalyticsEvent[]): Promise<void> {
  await http.post("/events", { events });
}

export async function fetchAdminOnboardings(): Promise<AdminOnboardingRow[]> {
  const response = await http.get<AdminOnboardingRow[]>("/admin/onboardings");
  return response.data;
}

export async function fetchAdminMetrics(): Promise<AdminMetrics> {
  const response = await http.get<AdminMetrics>("/admin/metrics");
  return response.data;
}

export async function fetchAdminFeedback(): Promise<AdminFeedbackRow[]> {
  const response = await http.get<AdminFeedbackRow[]>("/admin/feedback");
  return response.data;
}
