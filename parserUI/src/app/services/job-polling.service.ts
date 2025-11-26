import { inject, Injectable, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import {
    interval,
    Observable,
    Subject,
    Subscription,
    switchMap,
    takeUntil,
} from 'rxjs';

import { ApiService, JobStatusResponse } from './api.service';

@Injectable({
    providedIn: 'root',
})
export class JobPollingService {
    private readonly platformId = inject(PLATFORM_ID);
    private readonly api = inject(ApiService);

    private stop$ = new Subject<void>();
    private pollingSub?: Subscription;

    /**
     * Poll a job until it reaches a final state.
     * Final states: 'done', 'error', 'cancelled'.
     */
    pollJob(jobId: string, intervalMs = 3000): Observable<JobStatusResponse> {
        const result$ = new Subject<JobStatusResponse>();

        // Never poll on the server (SSR)
        if (!isPlatformBrowser(this.platformId)) {
            return result$.asObservable();
        }

        this.stopPolling();

        this.pollingSub = interval(intervalMs)
            .pipe(
                takeUntil(this.stop$),
                switchMap(() => this.api.getJobStatus(jobId)),
            )
            .subscribe({
                next: (status) => {
                    result$.next(status);

                    if (
                        status.status === 'done' ||
                        status.status === 'error' ||
                        status.status === 'cancelled'
                    ) {
                        this.stopPolling();
                    }
                },
                error: (err) => {
                    console.error('Polling error:', err);
                    this.stopPolling();
                },
            });

        return result$.asObservable();
    }

    stopPolling(): void {
        if (this.pollingSub) {
            this.stop$.next();
            this.pollingSub.unsubscribe();
            this.pollingSub = undefined;
        }
    }
}
