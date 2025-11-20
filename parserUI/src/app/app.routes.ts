//Concept:
// This says: when the URL path is /, show AppComponent.
// Any unknown path (**) redirects back to /.

import { Routes } from '@angular/router';
import { AppComponent } from './app';

export const routes: Routes = [
  { path: '', component: AppComponent },
  { path: '**', redirectTo: '' }
];
