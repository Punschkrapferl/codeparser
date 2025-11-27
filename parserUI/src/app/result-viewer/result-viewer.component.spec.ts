import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ResultViewerComponent } from './result-viewer.component';

describe('ResultViewerComponent', () => {
    let component: ResultViewerComponent;
    let fixture: ComponentFixture<ResultViewerComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [ResultViewerComponent],
        }).compileComponents();

        fixture = TestBed.createComponent(ResultViewerComponent);
        component = fixture.componentInstance;
        component.title = 'Test Analysis';
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('should show empty state when no analysis', () => {
        component.analysis = null;
        fixture.detectChanges();

        const compiled = fixture.nativeElement as HTMLElement;
        const emptyTitle = compiled.querySelector('.empty-title');
        expect(emptyTitle?.textContent).toContain('Test Analysis');
    });

    it('should render analysis text when present', () => {
        component.analysis = 'Some analysis text';
        fixture.detectChanges();

        const compiled = fixture.nativeElement as HTMLElement;
        const pre = compiled.querySelector('pre.analysis-pre');
        expect(pre?.textContent).toContain('Some analysis text');
    });

    it('should update view when searchTerm is set', () => {
        component.analysis = 'foo bar baz';
        fixture.detectChanges();

        component.searchTerm = 'bar';
        fixture.detectChanges();

        const compiled = fixture.nativeElement as HTMLElement;
        const pre = compiled.querySelector('pre.analysis-pre');
        expect(pre?.innerHTML || '').toContain('bar');
    });

    it('downloadTxt should do nothing if analysis is empty', () => {
        component.analysis = '   ';
        spyOn(document, 'createElement');

        component.downloadTxt();

        expect(document.createElement).not.toHaveBeenCalled();
    });

    it('downloadTxt should create an anchor element when analysis is present', () => {
        component.analysis = 'Download me';
        const createElementSpy = spyOn(document, 'createElement').and.callThrough();
        const appendChildSpy = spyOn(document.body, 'appendChild').and.callThrough();
        const removeChildSpy = spyOn(document.body, 'removeChild').and.callThrough();

        component.downloadTxt();

        expect(createElementSpy).toHaveBeenCalledWith('a');
        expect(appendChildSpy).toHaveBeenCalled();
        expect(removeChildSpy).toHaveBeenCalled();
    });
});
