import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Pipe({
  name: 'highlight',
  standalone: true,
})
export class HighlightPipe implements PipeTransform {
  constructor(private sanitizer: DomSanitizer) {}

  transform(text: string | null | undefined, search: string | null | undefined): SafeHtml {
    if (!text) {
      return '';
    }

    let result = text;

    // Very lightweight "syntax highlighting" for some common code-ish keywords
    const keywordPattern = /\b(def|class|function|if|else|for|while|return|async|await|try|catch)\b/g;
    result = result.replace(
      keywordPattern,
      '<span class="kw">$1</span>',
    );

    // Search term highlighting
    if (search && search.trim().length > 0) {
      const escaped = search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const searchRegex = new RegExp(escaped, 'gi');
      result = result.replace(
        searchRegex,
        match => `<mark>${match}</mark>`,
      );
    }

    return this.sanitizer.bypassSecurityTrustHtml(result);
  }
}
