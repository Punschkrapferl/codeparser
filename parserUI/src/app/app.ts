// Concept:
// @Component defines a component.
// standalone: true means it doesn’t need an NgModule.
// imports lists other Angular features this component uses:
// CommonModule gives you *ngIf, *ngFor, etc.

import {
  Component,
  ElementRef,
  OnInit,
  ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';

import {
  ApiService,
  GithubAnalyzeResponse,
  FileAnalyzeResponse,
} from './services/api.service';

// NEW: Result viewer component
import { ResultViewerComponent } from './result-viewer/result-viewer.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ResultViewerComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class AppComponent implements OnInit {
  title = 'Code Parser UI';

  healthOk: boolean | null = null;

  form!: FormGroup;
  isLoading = false;
  errorMessage: string | null = null;
  lastResult: GithubAnalyzeResponse | null = null;

  selectedFiles: File[] = [];
  isFileLoading = false;
  fileError: string | null = null;
  fileResult: FileAnalyzeResponse | null = null;
  isDragActive = false;
  showFileSummaries = false;

  @ViewChild('fileInput') fileInput?: ElementRef<HTMLInputElement>;
  @ViewChild('folderInput') folderInput?: ElementRef<HTMLInputElement>;

  constructor(
    private api: ApiService,
    private fb: FormBuilder,
  ) { }

  ngOnInit(): void {
    this.api.health().subscribe(ok => (this.healthOk = ok));

    this.form = this.fb.group({
      repoUrl: ['', [Validators.required, Validators.minLength(5)]],
      systemHint: [''],
    });
  }

  get repoUrl() {
    return this.form.get('repoUrl');
  }

  get systemHint() {
    return this.form.get('systemHint');
  }

  /** Simple pluralization helper used in the template. */
  plural(count: number | null | undefined, singular: string, plural: string): string {
    const n = count ?? 0;
    return n === 1 ? singular : plural;
  }

  // ---------- GitHub analyzer ----------

  onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    if (!this.healthOk) {
      this.errorMessage = 'Backend is not reachable.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;
    this.lastResult = null;

    const repoUrlValue = this.repoUrl?.value ?? '';
    const systemHintValue = this.systemHint?.value ?? '';

    this.api.analyzeGithubRepo(repoUrlValue, systemHintValue).subscribe({
      next: res => {
        this.isLoading = false;
        this.lastResult = res;
      },
      error: err => {
        this.isLoading = false;
        const msg =
          err instanceof Error ? err.message : 'Unexpected error during analysis.';
        this.errorMessage = msg;
      },
    });
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
  }

  // ---------- File / folder analyzer ----------

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

    const systemHintValue = this.systemHint?.value ?? '';

    const formData = new FormData();
    this.selectedFiles.forEach(file => {
      formData.append('files', file, file.name);
    });

    this.isFileLoading = true;
    this.fileError = null;
    this.fileResult = null;

    this.api.analyzeFiles(formData, systemHintValue).subscribe({
      next: res => {
        this.isFileLoading = false;
        this.fileResult = res;
      },
      error: err => {
        this.isFileLoading = false;
        const msg =
          err instanceof Error ? err.message : 'Error during file analysis';
        this.fileError = msg;
      },
    });
  }
}

// alias used by tests / bootstrap
export const App = AppComponent;
