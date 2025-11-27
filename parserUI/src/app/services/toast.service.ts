import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export type ToastType = 'info' | 'success' | 'warning' | 'error';

export interface Toast {
    id: number;
    type: ToastType;
    message: string;
}

@Injectable({
    providedIn: 'root',
})
export class ToastService {
    private readonly toastsSubject = new BehaviorSubject<Toast[]>([]);
    readonly toasts$ = this.toastsSubject.asObservable();

    private nextId = 1;

    show(message: string, type: ToastType = 'info', autoCloseMs = 5000): void {
        const toast: Toast = {
            id: this.nextId++,
            type,
            message,
        };

        const current = this.toastsSubject.value;
        this.toastsSubject.next([...current, toast]);

        if (autoCloseMs > 0) {
            setTimeout(() => this.dismiss(toast.id), autoCloseMs);
        }
    }

    showInfo(message: string, autoCloseMs = 4000): void {
        this.show(message, 'info', autoCloseMs);
    }

    showSuccess(message: string, autoCloseMs = 4000): void {
        this.show(message, 'success', autoCloseMs);
    }

    showWarning(message: string, autoCloseMs = 6000): void {
        this.show(message, 'warning', autoCloseMs);
    }

    showError(message: string, autoCloseMs = 7000): void {
        this.show(message, 'error', autoCloseMs);
    }

    dismiss(id: number): void {
        const current = this.toastsSubject.value;
        this.toastsSubject.next(current.filter((t) => t.id !== id));
    }

    clearAll(): void {
        this.toastsSubject.next([]);
    }
}
