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
    inject,
} from '@angular/core';
import { FormsModule } from '@angular/forms';

import {
    ApiService,
    FileAnalyzeResponse,
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
export class FileAnalyzerComponent {
    @Input() healthOk: boolean | null = null;

    selectedFiles: File[] = [];
    isFileLoading = false;
    fileError: string | null = null;
    fileResult: FileAnalyzeResponse | null = null;
    isDragActive = false;
    showFileSummaries = false;
    fileSystemHint = '';

    @ViewChild('fileInput') fileInput?: ElementRef<HTMLInputElement>;
    @ViewChild('folderInput') folderInput?: ElementRef<HTMLInputElement>;

    private api = inject(ApiService);

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

        this.api.analyzeFiles(formData, systemHintValue).subscribe({
            next: (res: FileAnalyzeResponse) => {
                this.isFileLoading = false;
                this.fileResult = res;
            },
            error: (err: unknown) => {
                this.isFileLoading = false;
                const msg =
                    err instanceof Error ? err.message : 'Error during file analysis';
                this.fileError = msg;
            },
        });
    }
}
