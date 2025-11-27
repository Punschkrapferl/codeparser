import { TestBed } from '@angular/core/testing';
import {
    HttpClientTestingModule,
    HttpTestingController,
} from '@angular/common/http/testing';

import {
    ApiService,
    GithubAnalyzeJobStartResponse,
    GithubAnalyzeRequest,
    FileAnalyzeJobStartResponse,
} from './services/api.service';

describe('ApiService', () => {
    let service: ApiService;
    let httpMock: HttpTestingController;

    const baseUrl = 'http://localhost:8000';

    beforeEach(() => {
        TestBed.configureTestingModule({
            imports: [HttpClientTestingModule],
            providers: [ApiService],
        });

        service = TestBed.inject(ApiService);
        httpMock = TestBed.inject(HttpTestingController);
    });

    afterEach(() => {
        httpMock.verify();
    });

    it('should be created', () => {
        expect(service).toBeTruthy();
    });

    it('healthCheck should call /health and map to void', () => {
        let completed = false;

        service.healthCheck().subscribe({
            next: (val) => {
                expect(val).toBeUndefined();
            },
            complete: () => {
                completed = true;
            },
        });

        const req = httpMock.expectOne(`${baseUrl}/health`);
        expect(req.request.method).toBe('GET');
        req.flush({ ok: true });

        expect(completed).toBeTrue();
    });

    it('startGithubRepoAnalysisJob should send repo_url and system_hint when provided', () => {
        const repoUrl = 'https://github.com/user/repo.git';
        const systemHint = 'please be gentle';

        let response: GithubAnalyzeJobStartResponse | undefined;

        service.startGithubRepoAnalysisJob(repoUrl, systemHint).subscribe((res) => {
            response = res;
        });

        const req = httpMock.expectOne(`${baseUrl}/analyze-github-job`);
        expect(req.request.method).toBe('POST');

        const body = req.request.body as GithubAnalyzeRequest;
        expect(body.repo_url).toBe(repoUrl);
        expect(body.system_hint).toBe(systemHint);

        const mockResponse: GithubAnalyzeJobStartResponse = { job_id: 'job-123' };
        req.flush(mockResponse);

        expect(response).toEqual(mockResponse);
    });

    it('startGithubRepoAnalysisJob should omit system_hint when empty', () => {
        const repoUrl = 'https://github.com/user/repo.git';

        service.startGithubRepoAnalysisJob(repoUrl, '').subscribe();

        const req = httpMock.expectOne(`${baseUrl}/analyze-github-job`);
        expect(req.request.method).toBe('POST');

        const body = req.request.body as GithubAnalyzeRequest;
        expect(body.repo_url).toBe(repoUrl);
        expect(body.system_hint).toBeUndefined();

        req.flush({ job_id: 'job-456' });
    });

    it('startFileAnalysisJob should POST FormData to /analyze-multi-job', () => {
        const formData = new FormData();
        formData.append('files', new Blob(['test']), 'file.txt');

        let response: FileAnalyzeJobStartResponse | undefined;

        service
            .startFileAnalysisJob(formData, 'hint me')
            .subscribe((res) => (response = res));

        const req = httpMock.expectOne(`${baseUrl}/analyze-multi-job`);
        expect(req.request.method).toBe('POST');
        expect(req.request.body instanceof FormData).toBeTrue();

        const mockResponse: FileAnalyzeJobStartResponse = { job_id: 'file-job-1' };
        req.flush(mockResponse);

        expect(response).toEqual(mockResponse);
    });

    it('getFileAnalysisJobStatus should call /analyze-multi-job/{id}', () => {
        const jobId = 'file-job-42';

        service.getFileAnalysisJobStatus(jobId).subscribe();

        const req = httpMock.expectOne(`${baseUrl}/analyze-multi-job/${jobId}`);
        expect(req.request.method).toBe('GET');
        req.flush({
            job_id: jobId,
            status: 'pending',
            result: null,
            error: null,
        });
    });

    it('getGithubRepoJobStatus should call /analyze-github-job/{id}', () => {
        const jobId = 'gh-job-99';

        service.getGithubRepoJobStatus(jobId).subscribe();

        const req = httpMock.expectOne(`${baseUrl}/analyze-github-job/${jobId}`);
        expect(req.request.method).toBe('GET');
        req.flush({
            job_id: jobId,
            status: 'pending',
            result: null,
            error: null,
        });
    });
});
