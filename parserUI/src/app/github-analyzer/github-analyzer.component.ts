import { CommonModule } from '@angular/common';
import {
    Component,
    Input,
    OnDestroy,
    OnInit,
    inject,
} from '@angular/core';
import {
    FormBuilder,
    FormGroup,
    ReactiveFormsModule,
    Validators,
} from '@angular/forms';
import { Subscription, interval, switchMap } from 'rxjs';

import {
    ApiService,
    GithubAnalyzeResponse,
    GithubAnalyzeJobStatusResponse,
} from '../services/api.service';
import { ResultViewerComponent } from '../result-viewer/result-viewer.component';

type JobUiStatus =
    | 'idle'
    | 'queued'
    | 'running'
    | 'done'
    | 'error'
    | 'cancelled';

@Component({
    selector: 'app-github-analyzer',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, ResultViewerComponent],
    templateUrl: './github-analyzer.component.html',
    styleUrl: './github-analyzer.component.scss',
})
export class GithubAnalyzerComponent implements OnInit, OnDestroy {
    @Input() healthOk: boolean | null = null;

    private api = inject(ApiService);
    private fb = inject(FormBuilder);

    form!: FormGroup;

    lastResult: GithubAnalyzeResponse | null = null;
    errorMessage: string | null = null;

    jobId: string | null = null;
    jobStatus: JobUiStatus = 'idle';
    isPolling = false;
    pollingMessage: string | null = null;
    private pollingSub: Subscription | null = null;

    ngOnInit(): void {
        this.form = this.fb.group({
            repoUrl: ['', [Validators.required, Validators.minLength(5)]],
            systemHint: [''],
        });
    }

    ngOnDestroy(): void {
        this.stopPolling();
    }

    get repoUrl() {
        return this.form.get('repoUrl');
    }

    get systemHint() {
        return this.form.get('systemHint');
    }

    plural(count: number | null | undefined, singular: string, plural: string): string {
        const n = count ?? 0;
        return n === 1 ? singular : plural;
    }

    onSubmit(): void {
        if (this.form.invalid) {
            this.form.markAllAsTouched();
            return;
        }
        if (!this.healthOk) {
            this.errorMessage = 'Backend is not reachable.';
            return;
        }

        this.errorMessage = null;
        this.lastResult = null;
        this.jobId = null;
        this.jobStatus = 'queued';
        this.pollingMessage = 'Submitting analysis job to the backend…';

        const repoUrlValue = this.repoUrl?.value ?? '';
        const systemHintValue = this.systemHint?.value ?? '';

        this.api.startGithubRepoAnalysisJob(repoUrlValue, systemHintValue).subscribe({
            next: (res) => {
                this.jobId = res.job_id;
                this.jobStatus = 'running';
                this.pollingMessage = 'Job started. Polling for results…';
                this.startPolling();
            },
            error: (err: unknown) => {
                this.jobStatus = 'error';
                const msg =
                    err instanceof Error ? err.message : 'Failed to start analysis job.';
                this.errorMessage = msg;
                this.pollingMessage = 'Could not start job.';
            },
        });
    }

    onCancelPolling(): void {
        this.stopPolling();
        this.jobStatus = 'cancelled';
        this.pollingMessage = 'Polling cancelled by user.';
    }

    resetGithubAnalyzer(): void {
        this.form.reset({
            repoUrl: '',
            systemHint: '',
        });
        this.form.markAsPristine();
        this.form.markAsUntouched();

        this.errorMessage = null;
        this.lastResult = null;

        this.jobId = null;
        this.jobStatus = 'idle';
        this.pollingMessage = null;
        this.stopPolling();
    }

    private startPolling(): void {
        if (!this.jobId) {
            return;
        }

        this.stopPolling();
        this.isPolling = true;

        this.pollingSub = interval(2000)
            .pipe(
                switchMap(() =>
                    this.api.getGithubRepoJobStatus(this.jobId as string),
                ),
            )
            .subscribe({
                next: (res: GithubAnalyzeJobStatusResponse) => {
                    if (res.status === 'pending') {
                        this.jobStatus = 'queued';
                        this.pollingMessage = 'Job is queued on the server…';
                        return;
                    }

                    if (res.status === 'running') {
                        this.jobStatus = 'running';
                        this.pollingMessage = 'Job is running on the server…';
                        return;
                    }

                    if (res.status === 'done') {
                        this.jobStatus = 'done';
                        this.isPolling = false;
                        this.stopPolling();
                        this.lastResult = res.result ?? null;
                        this.pollingMessage = 'Analysis completed successfully.';
                        return;
                    }

                    if (res.status === 'error') {
                        this.jobStatus = 'error';
                        this.isPolling = false;
                        this.stopPolling();
                        this.errorMessage = res.error || 'Job failed on the server.';
                        this.pollingMessage = 'Job failed.';
                        return;
                    }

                    if (res.status === 'cancelled') {
                        this.jobStatus = 'cancelled';
                        this.isPolling = false;
                        this.stopPolling();
                        this.pollingMessage = 'Job was cancelled on the server.';
                    }
                },
                error: (err: unknown) => {
                    this.jobStatus = 'error';
                    this.isPolling = false;
                    this.stopPolling();
                    const msg =
                        err instanceof Error ? err.message : 'Error while polling job status.';
                    this.errorMessage = msg;
                    this.pollingMessage = 'Lost connection while polling job.';
                },
            });
    }

    private stopPolling(): void {
        if (this.pollingSub) {
            this.pollingSub.unsubscribe();
            this.pollingSub = null;
        }
        this.isPolling = false;
    }
}
