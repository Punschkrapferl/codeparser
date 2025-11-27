import { ApplicationConfig } from '@angular/core';
import {
  provideHttpClient,
  withFetch,
  withInterceptors,
} from '@angular/common/http';
import { provideServerRendering } from '@angular/platform-server';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { httpErrorInterceptor } from './interceptors/http-error.interceptor';

export const appConfigServer: ApplicationConfig = {
  providers: [
    provideServerRendering(),
    provideRouter(routes),
    // HttpClient for SSR using fetch + same interceptor
    provideHttpClient(
      withFetch(),
      withInterceptors([httpErrorInterceptor]),
    ),
  ],
};
