import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { FileAnalyzerComponent } from './file-analyzer.component';
import {
    ApiService,
    FileAnalyzeJobStartResponse,
} from '../services/api.service';

describe('FileAnalyzerComponent', () => {
    let component: FileAnalyzerComponent;
    let fixture: ComponentFixture<FileAnalyzerComponent>;
    let apiSpy: jasmine.SpyObj<ApiService>;

    beforeEach(async () => {
        apiSpy = jasmine.createSpyObj<ApiService>(
            'ApiService',
            ['startFileAnalysisJob', 'getFileAnalysisJobStatus'],
        );

        await TestBed.configureTestingModule({
            imports: [FileAnalyzerComponent],
            providers: [{ provide: ApiService, useValue: apiSpy }],
        }).compileComponents();

        fixture = TestBed.createComponent(FileAnalyzerComponent);
        component = fixture.componentInstance;
        component.healthOk = true;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('hasFilesSelected should reflect selectedFiles length', () => {
        expect(component.hasFilesSelected).toBeFalse();
        component.selectedFiles = [new File(['test'], 'a.txt')];
        expect(component.hasFilesSelected).toBeTrue();
    });

    it('onFileSelected should populate selectedFiles and clear errors and result', () => {
        const file = new File(['content'], 'a.txt');

        const event = {
            target: { files: { length: 1, 0: file, item: () => file } as any },
        } as unknown as Event;

        component.fileError = 'error';
        component.fileResult = {
            analysis: 'test',
            batches: 1,
            languages: ['ts'],
        };

        component.onFileSelected(event);

        expect(component.selectedFiles.length).toBe(1);
        expect(component.selectedFiles[0].name).toBe('a.txt');
        expect(component.fileError).toBeNull();
        expect(component.fileResult).toBeNull();
    });

    it('onAnalyzeFiles should set error if no files selected', () => {
        component.selectedFiles = [];
        component.healthOk = true;

        component.onAnalyzeFiles();

        expect(component.fileError).toBe(
            'Please select at least one file or folder.',
        );
        expect(apiSpy.startFileAnalysisJob).not.toHaveBeenCalled();
    });

    it('onAnalyzeFiles should set error if backend not reachable', () => {
        component.selectedFiles = [new File(['x'], 'a.txt')];
        component.healthOk = false;

        component.onAnalyzeFiles();

        expect(component.fileError).toBe('Backend is not reachable.');
        expect(apiSpy.startFileAnalysisJob).not.toHaveBeenCalled();
    });

    it('onAnalyzeFiles should start file job and call startPolling on success', () => {
        component.selectedFiles = [new File(['x'], 'a.txt')];
        component.healthOk = true;
        component.fileSystemHint = 'hint';

        const startResponse: FileAnalyzeJobStartResponse = { job_id: 'file-job' };

        apiSpy.startFileAnalysisJob.and.returnValue(of(startResponse));

        const startPollingSpy = spyOn<any>(
            component as any,
            'startPolling',
        ).and.callFake(() => { });

        component.onAnalyzeFiles();

        expect(apiSpy.startFileAnalysisJob).toHaveBeenCalled();
        expect(component.jobId).toBe('file-job');
        expect(component.jobStatus).toBe('running');
        expect(component.pollingMessage).toContain('Job started');
        expect(startPollingSpy).toHaveBeenCalled();
    });

    it('onAnalyzeFiles should handle error when starting job fails', () => {
        component.selectedFiles = [new File(['x'], 'a.txt')];
        component.healthOk = true;

        apiSpy.startFileAnalysisJob.and.returnValue(
            throwError(() => new Error('boom')),
        );

        component.onAnalyzeFiles();

        expect(component.jobStatus).toBe('error');
        expect(component.isFileLoading).toBeFalse();
        expect(component.fileError).toBe('boom');
        expect(component.pollingMessage).toBe('Could not start file analysis job.');
    });

    it('resetFileAnalyzer should reset state and inputs', () => {
        component.selectedFiles = [new File(['x'], 'a.txt')];
        component.fileResult = {
            analysis: 'x',
            batches: 1,
            languages: ['ts'],
        };
        component.fileError = 'err';
        component.isFileLoading = true;
        component.showFileSummaries = true;
        component.fileSystemHint = 'hint';
        component.jobId = 'job';
        component.jobStatus = 'running';
        component.pollingMessage = 'Polling…';

        component.resetFileAnalyzer();

        expect(component.selectedFiles.length).toBe(0);
        expect(component.fileResult).toBeNull();
        expect(component.fileError).toBeNull();
        expect(component.isFileLoading).toBeFalse();
        expect(component.showFileSummaries).toBeFalse();
        expect(component.fileSystemHint).toBe('');
        expect(component.jobId).toBeNull();
        expect(component.jobStatus).toBe('idle');
        expect(component.pollingMessage).toBeNull();
    });

    it('onCancelPolling should stop polling and set cancelled status', () => {
        const stopPollingSpy = spyOn<any>(
            component as any,
            'stopPolling',
        ).and.callThrough();

        component.isFileLoading = true;
        component.onCancelPolling();

        expect(stopPollingSpy).toHaveBeenCalled();
        expect(component.jobStatus).toBe('cancelled');
        expect(component.pollingMessage).toBe('Polling cancelled by user.');
    });
});
