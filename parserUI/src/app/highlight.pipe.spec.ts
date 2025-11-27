import { TestBed } from '@angular/core/testing';
import { DomSanitizer } from '@angular/platform-browser';
import { HighlightPipe } from '../highlight.pipe';

describe('HighlightPipe', () => {
    let pipe: HighlightPipe;

    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [
                HighlightPipe,
                {
                    provide: DomSanitizer,
                    useValue: {
                        bypassSecurityTrustHtml: (v: string) => v,
                    },
                },
            ],
        });

        pipe = TestBed.inject(HighlightPipe);
    });

    it('should return empty string when text is null', () => {
        const result = pipe.transform(null, 'x') as string;
        expect(result).toBe('');
    });

    it('should return escaped HTML when no search term', () => {
        const result = pipe.transform('<b>test</b>', '') as string;
        expect(result).toBe('&lt;b&gt;test&lt;/b&gt;');
    });

    it('should wrap matches in <mark> tags', () => {
        const result = pipe.transform('foo bar foo', 'foo') as string;
        expect(result).toContain('<mark>foo</mark> bar <mark>foo</mark>');
    });

    it('should escape HTML before highlighting', () => {
        const result = pipe.transform('<script>alert(1)</script>', 'alert') as string;
        expect(result).toContain('&lt;script&gt;<mark>alert</mark>(1)&lt;/script&gt;');
    });
});
