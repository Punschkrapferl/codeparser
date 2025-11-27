import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { GithubAnalyzerComponent } from './github-analyzer.component';
import {
    ApiService,
    GithubAnalyzeJobStartResponse,
} from '../services/api.service';

describe('GithubAnalyzerComponent', () => {
    let component: GithubAnalyzerComponent;
    let fixture: ComponentFixture<GithubAnalyzerComponent>;
    let apiSpy: jasmine.SpyObj<ApiService>;

    beforeEach(async () => {
        apiSpy = jasmine.createSpyObj<ApiService>(
            'ApiService',
            [
                'startGithubRepoAnalysisJob',
                'getGithubRepoJobStatus',
                'healthCheck',
            ],
        );

        await TestBed.configureTestingModule({
            imports: [GithubAnalyzerComponent],
            providers: [{ provide: ApiService, useValue: apiSpy }],
        }).compileComponents();

        fixture = TestBed.createComponent(GithubAnalyzerComponent);
        component = fixture.componentInstance;
        component.healthOk = true;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('should mark form as touched and not start job on invalid submit', () => {
        // initially empty => invalid
        component.healthOk = true;
        fixture.detectChanges();

        expect(component.form.invalid).toBeTrue();

        component.onSubmit();

        expect(component.form.touched).toBeTrue();
        expect(apiSpy.startGithubRepoAnalysisJob).not.toHaveBeenCalled();
    });

    it('should set errorMessage if backend not reachable on submit', () => {
        component.healthOk = false;
        fixture.detectChanges();

        // fill in values to make form valid
        component.form.setValue({
            repoUrl: 'https://github.com/user/repo.git',
            systemHint: '',
        });

        component.onSubmit();

        expect(component.errorMessage).toBe('Backend is not reachable.');
        expect(apiSpy.startGithubRepoAnalysisJob).not.toHaveBeenCalled();
    });

    it('should start GitHub job and call startPolling on success', () => {
        component.healthOk = true;
        fixture.detectChanges();

        const startResponse: GithubAnalyzeJobStartResponse = {
            job_id: 'job-123',
        };

        apiSpy.startGithubRepoAnalysisJob.and.returnValue(of(startResponse));

        // Spy on private method via cast
        const startPollingSpy = spyOn<any>(
            component as any,
            'startPolling',
        ).and.callFake(() => { });

        component.form.setValue({
            repoUrl: 'https://github.com/user/repo.git',
            systemHint: 'explain simply',
        });

        component.onSubmit();

        expect(apiSpy.startGithubRepoAnalysisJob).toHaveBeenCalledOnceWith(
            'https://github.com/user/repo.git',
            'explain simply',
        );
        expect(component.jobId).toBe('job-123');
        expect(component.jobStatus).toBe('running');
        expect(component.pollingMessage).toContain('Job started');
        expect(startPollingSpy).toHaveBeenCalled();
    });

    it('should handle error when starting GitHub job fails', () => {
        component.healthOk = true;
        fixture.detectChanges();

        apiSpy.startGithubRepoAnalysisJob.and.returnValue(
            throwError(() => new Error('boom')),
        );

        component.form.setValue({
            repoUrl: 'https://github.com/user/repo.git',
            systemHint: '',
        });

        component.onSubmit();

        expect(apiSpy.startGithubRepoAnalysisJob).toHaveBeenCalled();
        expect(component.jobStatus).toBe('error');
        expect(component.errorMessage).toBe('boom');
        expect(component.pollingMessage).toBe('Could not start job.');
    });

    it('resetGithubAnalyzer should reset form and state', () => {
        component.errorMessage = 'some error';
        component.lastResult = {
            analysis: 'text',
            batches: 1,
            num_parts: 2,
            languages: ['python'],
        };
        component.jobId = 'job-1';
        component.jobStatus = 'running';
        component.pollingMessage = 'Polling…';

        component.resetGithubAnalyzer();

        expect(component.form.value.repoUrl).toBe('');
        expect(component.form.value.systemHint).toBe('');
        expect(component.errorMessage).toBeNull();
        expect(component.lastResult).toBeNull();
        expect(component.jobId).toBeNull();
        expect(component.jobStatus).toBe('idle');
        expect(component.pollingMessage).toBeNull();
    });

    it('plural() should return singular or plural correctly', () => {
        expect(component.plural(1, 'file', 'files')).toBe('file');
        expect(component.plural(2, 'file', 'files')).toBe('files');
        expect(component.plural(0, 'file', 'files')).toBe('files');
        expect(component.plural(null, 'file', 'files')).toBe('files');
    });
});
