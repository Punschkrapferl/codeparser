import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { PLATFORM_ID } from '@angular/core';
import { of } from 'rxjs';

import { JobPollingService } from './job-polling.service';
import {
    ApiService,
    JobStatusResponse,
} from './api.service';

describe('JobPollingService', () => {
    let service: JobPollingService;
    let apiSpy: jasmine.SpyObj<ApiService>;

    beforeEach(() => {
        apiSpy = jasmine.createSpyObj<ApiService>('ApiService', ['getJobStatus']);

        TestBed.configureTestingModule({
            providers: [
                JobPollingService,
                { provide: ApiService, useValue: apiSpy },
                // Simulate browser platform so polling is enabled
                { provide: PLATFORM_ID, useValue: 'browser' },
            ],
        });

        service = TestBed.inject(JobPollingService);
    });

    it('should be created', () => {
        expect(service).toBeTruthy();
    });

    it('pollJob should emit statuses and stop when done', fakeAsync(() => {
        const jobId = 'job-1';
        const emitted: JobStatusResponse[] = [];

        let callCount = 0;
        apiSpy.getJobStatus.and.callFake(() => {
            callCount += 1;
            if (callCount === 1) {
                return of({
                    job_id: jobId,
                    status: 'pending',
                    result: null,
                    error: null,
                } as JobStatusResponse);
            }
            return of({
                job_id: jobId,
                status: 'done',
                result: null,
                error: null,
            } as JobStatusResponse);
        });

        service.pollJob(jobId, 1000).subscribe((status) => {
            emitted.push(status);
        });

        // First tick -> pending
        tick(1000);
        // Second tick -> done (and stop)
        tick(1000);

        expect(emitted.length).toBe(2);
        expect(emitted[0].status).toBe('pending');
        expect(emitted[1].status).toBe('done');
        expect(apiSpy.getJobStatus).toHaveBeenCalledTimes(2);
    }));
});
