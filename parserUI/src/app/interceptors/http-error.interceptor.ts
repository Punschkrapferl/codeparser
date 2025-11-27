import { inject } from '@angular/core';
import {
    HttpErrorResponse,
    HttpInterceptorFn,
} from '@angular/common/http';
import { catchError, throwError } from 'rxjs';

import { ToastService } from '../services/toast.service';

export const httpErrorInterceptor: HttpInterceptorFn = (req, next) => {
    const toast = inject(ToastService);

    return next(req).pipe(
        catchError((error: unknown) => {
            if (error instanceof HttpErrorResponse) {
                const message = mapHttpErrorToMessage(error);
                toast.showError(message);
            } else {
                toast.showError('Unexpected error occurred.');
            }

            // Let the component still see the error if it has its own handling.
            return throwError(() => error);
        }),
    );
};

function mapHttpErrorToMessage(err: HttpErrorResponse): string {
    const detail =
        (err.error && (err.error.detail || err.error.message)) ?? '';

    // Network / CORS / backend offline
    if (err.status === 0) {
        return 'Cannot reach backend API. Is the FastAPI server running on http://localhost:8000?';
    }

    const d = String(detail).toLowerCase();

    // Invalid / missing repo URL
    if (d.includes('repo_url invalid') || d.includes('repo_url required')) {
        return 'The repository URL is invalid. Please check it and try again.';
    }

    // Git / clone / parser issues
    if (
        d.includes('git not found') ||
        d.includes('git error') ||
        d.includes('cannot read output file') ||
        d.includes('go run error')
    ) {
        return 'Failed to analyze the repository. Check that Git and the Go parser are installed and working.';
    }

    // LLM issues coming from backend messages
    if (
        d.includes('[llm request error]') ||
        d.includes('[llm http error') ||
        d.includes('[llm json error]') ||
        d.includes('[llm error]')
    ) {
        return 'The AI analysis failed. Please verify your local LLM configuration and try again.';
    }

    // If backend returned a detail message, surface it directly
    if (detail) {
        return String(detail);
    }

    return `Request failed with status ${err.status}.`;
}
