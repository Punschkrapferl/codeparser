// Concept:
// This is a reusable “bridge” between Angular and your backend.
// Components will not call HttpClient directly, but go through this service.

import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';

export interface GithubAnalyzeResponse {
  analysis: string;
  batches: number;
  num_parts: number;
  languages: string[];
  repo_path: string;
  source_file: string;
}

export interface FileSummary {
  filename: string;
  num_parts: number;
}

export interface FileAnalyzeResponse {
  // Shared
  analysis: string;
  batches: number;
  languages: string[];

  // Single-file /analyze
  num_parts?: number;
  filename?: string;

  // Multi-file /analyze-multi
  num_files?: number;
  total_parts?: number;
  file_summaries?: FileSummary[];
}

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private readonly baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  health(): Observable<boolean> {
    return this.http
      .get<{ ok: boolean }>(`${this.baseUrl}/health`)
      .pipe(map(r => !!r.ok));
  }

  analyzeGithubRepo(
    repoUrl: string,
    systemHint: string,
  ): Observable<GithubAnalyzeResponse> {
    let params = new HttpParams().set('repo_url', repoUrl);
    if (systemHint) {
      params = params.set('system_hint', systemHint);
    }

    return this.http.post<GithubAnalyzeResponse>(
      `${this.baseUrl}/github/analyze`,
      {},
      { params },
    );
  }

  analyzeFile(
    file: File,
    systemHint: string,
  ): Observable<FileAnalyzeResponse> {
    const formData = new FormData();
    formData.append('file', file, file.name);

    let params = new HttpParams();
    if (systemHint) {
      params = params.set('system_hint', systemHint);
    }

    return this.http.post<FileAnalyzeResponse>(
      `${this.baseUrl}/analyze`,
      formData,
      { params },
    );
  }

  analyzeFiles(
    formData: FormData,
    systemHint: string,
  ): Observable<FileAnalyzeResponse> {
    let params = new HttpParams();
    if (systemHint) {
      params = params.set('system_hint', systemHint);
    }

    return this.http.post<FileAnalyzeResponse>(
      `${this.baseUrl}/analyze-multi`,
      formData,
      { params },
    );
  }
}
