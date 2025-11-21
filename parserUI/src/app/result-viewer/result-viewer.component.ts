import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { HighlightPipe } from '../../highlight.pipe';

@Component({
  selector: 'app-result-viewer',
  standalone: true,
  imports: [CommonModule, FormsModule, HighlightPipe],
  templateUrl: './result-viewer.component.html',
  styleUrl: './result-viewer.component.scss',
})
export class ResultViewerComponent {
  @Input() title = 'Analysis';
  @Input() analysis: string | null = null;

  searchTerm = '';

  downloadTxt(): void {
    if (!this.analysis || !this.analysis.trim()) {
      return;
    }

    const fileNameBase =
      this.title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '') || 'analysis';

    const blob = new Blob([this.analysis], {
      type: 'text/plain;charset=utf-8',
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${fileNameBase}.txt`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
}
