import {
    CommonModule,
    NgIf,
    NgForOf,
} from '@angular/common';
import {
    Component,
    ElementRef,
    Input,
    ViewChild,
    OnDestroy,
    inject,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subscription, interval, switchMap } from 'rxjs';

import {
    ApiService,
    FileAnalyzeResponse,
    FileAnalyzeJobStatusResponse,
    JobUiStatus,
} from '../services/api.service';
import { ResultViewerComponent } from '../result-viewer/result-viewer.component';

@Component({
    selector: 'app-file-analyzer',
    standalone: true,
    imports: [
        CommonModule,
        NgIf,
        NgForOf,
        FormsModule,
        ResultViewerComponent,
    ],
    templateUrl: './file-analyzer.component.html',
    styleUrl: './file-analyzer.component.scss',
})
export class FileAnalyzerComponent implements OnDestroy {
    @Input() healthOk: boolean | null = null;

    selectedFiles: File[] = [];
    isFileLoading = false;
    fileError: string | null = null;
    fileResult: FileAnalyzeResponse | null = null;
    isDragActive = false;
    showFileSummaries = false;
    fileSystemHint = '';

    // Job/polling state (mirrors GitHub analyser)
    jobId: string | null = null;
    jobStatus: JobUiStatus = 'idle';
    pollingMessage: string | null = null;
    private pollingSub: Subscription | null = null;

    @ViewChild('fileInput') fileInput?: ElementRef<HTMLInputElement>;
    @ViewChild('folderInput') folderInput?: ElementRef<HTMLInputElement>;

    private api = inject(ApiService);

    ngOnDestroy(): void {
        this.stopPolling();
    }

    onClickFileInput(): void {
        this.fileInput?.nativeElement.click();
    }

    onClickFolderInput(): void {
        this.folderInput?.nativeElement.click();
    }

    onFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        if (!input.files) return;
        this.selectedFiles = Array.from(input.files);
        this.fileError = null;
        this.fileResult = null;
    }

    onFolderSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        if (!input.files) return;
        this.selectedFiles = Array.from(input.files);
        this.fileError = null;
        this.fileResult = null;
    }

    onFileDragOver(event: DragEvent): void {
        event.preventDefault();
        this.isDragActive = true;
    }

    onFileDragLeave(event: DragEvent): void {
        event.preventDefault();
        this.isDragActive = false;
    }

    onFileDrop(event: DragEvent): void {
        event.preventDefault();
        this.isDragActive = false;

        if (!event.dataTransfer || !event.dataTransfer.files?.length) {
            return;
        }
        this.selectedFiles = Array.from(event.dataTransfer.files);
        this.fileError = null;
        this.fileResult = null;
    }

    fileDisplayName(f: File): string {
        const anyFile = f as any;
        return anyFile.webkitRelativePath || f.name;
    }

    get hasFilesSelected(): boolean {
        return this.selectedFiles.length > 0;
    }

    get folderFileCount(): number {
        return this.selectedFiles.length;
    }

    resetFileAnalyzer(): void {
        this.selectedFiles = [];
        this.fileResult = null;
        this.fileError = null;
        this.isFileLoading = false;
        this.showFileSummaries = false;
        this.fileSystemHint = '';

        this.jobId = null;
        this.jobStatus = 'idle';
        this.pollingMessage = null;
        this.stopPolling();

        if (this.fileInput?.nativeElement) {
            this.fileInput.nativeElement.value = '';
        }
        if (this.folderInput?.nativeElement) {
            this.folderInput.nativeElement.value = '';
        }
    }

    onAnalyzeFiles(): void {
        if (!this.selectedFiles.length) {
            this.fileError = 'Please select at least one file or folder.';
            return;
        }
        if (!this.healthOk) {
            this.fileError = 'Backend is not reachable.';
            return;
        }

        const systemHintValue = this.fileSystemHint ?? '';

        const formData = new FormData();
        this.selectedFiles.forEach((file) => {
            formData.append('files', file, file.name);
        });

        this.isFileLoading = true;
        this.fileError = null;
        this.fileResult = null;

        this.jobId = null;
        this.jobStatus = 'queued';
        this.pollingMessage = 'Submitting analysis job to the backend…';

        this.api.startFileAnalysisJob(formData, systemHintValue).subscribe({
            next: (res) => {
                this.jobId = res.job_id;
                this.jobStatus = 'running';
                this.pollingMessage = 'Job started. Polling for results…';
                this.startPolling();
            },
            error: (err: unknown) => {
                this.jobStatus = 'error';
                this.isFileLoading = false;
                const msg =
                    err instanceof Error
                        ? err.message
                        : 'Error during file analysis job start.';
                this.fileError = msg;
                this.pollingMessage = 'Could not start file analysis job.';
            },
        });
    }

    onCancelPolling(): void {
        this.stopPolling();
        this.jobStatus = 'cancelled';
        this.pollingMessage = 'Polling cancelled by user.';
    }

    private startPolling(): void {
        if (!this.jobId) {
            return;
        }

        this.stopPolling();
        this.isFileLoading = true;

        this.pollingSub = interval(2000)
            .pipe(
                switchMap(() =>
                    this.api.getFileAnalysisJobStatus(this.jobId as string),
                ),
            )
            .subscribe({
                next: (res: FileAnalyzeJobStatusResponse) => {
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
                        this.isFileLoading = false;
                        this.stopPolling();
                        this.fileResult = res.result ?? null;
                        this.pollingMessage = 'Analysis completed successfully.';
                        return;
                    }

                    if (res.status === 'error') {
                        this.jobStatus = 'error';
                        this.isFileLoading = false;
                        this.stopPolling();
                        this.fileError = res.error || 'Job failed on the server.';
                        this.pollingMessage = 'Job failed.';
                        return;
                    }

                    if (res.status === 'cancelled') {
                        this.jobStatus = 'cancelled';
                        this.isFileLoading = false;
                        this.stopPolling();
                        this.pollingMessage = 'Job was cancelled on the server.';
                    }
                },
                error: (err: unknown) => {
                    this.jobStatus = 'error';
                    this.isFileLoading = false;
                    this.stopPolling();
                    const msg =
                        err instanceof Error
                            ? err.message
                            : 'Error while polling file job status.';
                    this.fileError = msg;
                    this.pollingMessage = 'Lost connection while polling job.';
                },
            });
    }

    private stopPolling(): void {
        if (this.pollingSub) {
            this.pollingSub.unsubscribe();
            this.pollingSub = null;
        }
        this.isFileLoading = false;
    }
}
