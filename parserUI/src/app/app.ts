import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';

import { GithubAnalyzerComponent } from './github-analyzer/github-analyzer.component';
import { FileAnalyzerComponent } from './file-analyzer/file-analyzer.component';
import { ApiService } from './services/api.service';
import { ToastContainerComponent } from './toast-container/toast-container.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    GithubAnalyzerComponent,
    FileAnalyzerComponent,
    ToastContainerComponent,
  ],
  templateUrl: './app.html',
  styleUrls: ['./app.scss'],
})
export class AppComponent implements OnInit {
  private readonly api = inject(ApiService);

  title = 'parserUI';
  healthOk: boolean | null = null;

  ngOnInit(): void {
    this.api.healthCheck().subscribe({
      next: () => {
        this.healthOk = true;
      },
      error: () => {
        this.healthOk = false;
      },
    });
  }
}
