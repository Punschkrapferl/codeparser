import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';

export type JobUiStatus =
  | 'idle'
  | 'pending'   // ← add this
  | 'queued'
  | 'running'
  | 'done'
  | 'error'
  | 'cancelled';

export interface HealthResponse {
  ok: boolean;
}

export interface GithubAnalyzeRequest {
  repo_url: string;
  system_hint?: string | null;
}

export interface GithubAnalyzeJobStartResponse {
  job_id: string;
}

export interface GithubAnalyzeJobStatusResponse {
  job_id: string;
  status: JobUiStatus;
  result?: GithubAnalyzeResponse | null;
  error?: string | null;
}

export interface GithubAnalyzeResponse {
  analysis: string;
  batches: number;
  num_parts?: number;
  num_files?: number;
  total_parts?: number;
  languages: string[];
  repo_path?: string;
  source_file?: string;
}

// alias for job-polling.service.ts
export type JobStatusResponse = GithubAnalyzeJobStatusResponse;

export interface FileSummary {
  filename: string;
  num_parts: number;
}

export interface FileAnalyzeResponse {
  analysis: string;
  batches: number;
  num_parts?: number;
  total_parts?: number;
  num_files?: number;
  languages: string[];
  file_summaries?: FileSummary[];
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000';

  // used by AppComponent
  healthCheck(): Observable<void> {
    return this.http
      .get<HealthResponse>(`${this.baseUrl}/health`)
      .pipe(map(() => void 0));
  }

  // ---------- GitHub job endpoints ----------

  startGithubJob(
    payload: GithubAnalyzeRequest
  ): Observable<GithubAnalyzeJobStartResponse> {
    return this.http.post<GithubAnalyzeJobStartResponse>(
      `${this.baseUrl}/analyze-github-job`,
      payload
    );
  }

  getGithubJobStatus(
    jobId: string
  ): Observable<GithubAnalyzeJobStatusResponse> {
    return this.http.get<GithubAnalyzeJobStatusResponse>(
      `${this.baseUrl}/analyze-github-job/${jobId}`
    );
  }

  /**
   * Wrapper methods so existing components don't need to change names.
   */
  startGithubRepoAnalysisJob(
    repoUrl: string,
    systemHint?: string | null
  ): Observable<GithubAnalyzeJobStartResponse> {
    const payload: GithubAnalyzeRequest = { repo_url: repoUrl };
    if (systemHint && systemHint.trim().length > 0) {
      payload.system_hint = systemHint;
    }
    return this.startGithubJob(payload);
  }

  getGithubRepoJobStatus(
    jobId: string
  ): Observable<GithubAnalyzeJobStatusResponse> {
    return this.getGithubJobStatus(jobId);
  }

  /**
   * Generic job status getter for JobPollingService.
   */
  getJobStatus(jobId: string): Observable<JobStatusResponse> {
    return this.getGithubJobStatus(jobId);
  }

  // ---------- File analysis endpoints ----------

  analyzeSingleFile(
    file: File,
    systemHint: string | null
  ): Observable<FileAnalyzeResponse> {
    const form = new FormData();
    form.append('file', file);
    if (systemHint && systemHint.trim().length > 0) {
      form.append('system_hint', systemHint);
    }
    return this.http.post<FileAnalyzeResponse>(
      `${this.baseUrl}/analyze`,
      form
    );
  }

  analyzeMultipleFiles(
    files: File[],
    systemHint: string | null
  ): Observable<FileAnalyzeResponse> {
    const form = new FormData();
    for (const f of files) {
      form.append('files', f);
    }
    if (systemHint && systemHint.trim().length > 0) {
      form.append('system_hint', systemHint);
    }
    return this.http.post<FileAnalyzeResponse>(
      `${this.baseUrl}/analyze-multi`,
      form
    );
  }

  /**
   * Wrapper used by FileAnalyzerComponent (expects FormData + hint).
   */
  analyzeFiles(
    formData: FormData,
    systemHint: string | null
  ): Observable<FileAnalyzeResponse> {
    if (systemHint && systemHint.trim().length > 0) {
      formData.append('system_hint', systemHint);
    }
    return this.http.post<FileAnalyzeResponse>(
      `${this.baseUrl}/analyze-multi`,
      formData
    );
  }
}
