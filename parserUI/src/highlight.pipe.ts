import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Pipe({
  name: 'highlight',
  standalone: true,
  pure: true,
})
export class HighlightPipe implements PipeTransform {
  constructor(private sanitizer: DomSanitizer) { }

  private escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  transform(
    text: string | null | undefined,
    search: string | null | undefined,
  ): SafeHtml {
    if (!text) {
      return '';
    }
    if (!search || !search.trim()) {
      // Should only be used when searchTerm is set,
      // but keep this as a safe default.
      return this.sanitizer.bypassSecurityTrustHtml(this.escapeHtml(text));
    }

    const escapedText = this.escapeHtml(text);
    const escapedSearch = search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(escapedSearch, 'gi');

    const highlighted = escapedText.replace(
      regex,
      match => `<mark>${match}</mark>`,
    );

    return this.sanitizer.bypassSecurityTrustHtml(highlighted);
  }
}
