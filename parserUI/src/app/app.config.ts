// Explanation (concept):
// provideRouter(routes) tells Angular which routes exist.
// provideClientHydration() is for SSR.
// provideHttpClient() enables Angular’s HTTP API in the whole app.

import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideClientHydration } from '@angular/platform-browser';
import { provideHttpClient, withFetch } from '@angular/common/http';

import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideClientHydration(),
    provideHttpClient(withFetch())
  ]
};

