import { CommonModule, NgForOf, NgIf, NgClass } from '@angular/common';
import { Component, inject } from '@angular/core';

import { ToastService, Toast } from '../services/toast.service';

@Component({
    selector: 'app-toast-container',
    standalone: true,
    imports: [CommonModule, NgIf, NgForOf, NgClass],
    templateUrl: './toast-container.component.html',
    styleUrl: './toast-container.component.scss',
})
export class ToastContainerComponent {
    // Inject service via inject()
    private readonly toastService = inject(ToastService);

    // Now toastService is definitely initialized before this runs
    readonly toasts$ = this.toastService.toasts$;

    trackById(_index: number, toast: Toast): number {
        return toast.id;
    }

    dismiss(id: number): void {
        this.toastService.dismiss(id);
    }
}
