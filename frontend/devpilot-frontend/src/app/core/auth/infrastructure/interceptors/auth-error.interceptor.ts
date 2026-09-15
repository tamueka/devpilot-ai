import {
    HttpErrorResponse,
    HttpInterceptorFn,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthStore } from '../../application/stores/auth.store';


export const authErrorInterceptor: HttpInterceptorFn = (
    request,
    next,
) => {
    const authStore = inject(AuthStore);
    const router = inject(Router);

    return next(request).pipe(
        catchError(
            (error: HttpErrorResponse) => {
                if (
                    error.status === 401
                    && !request.url.includes(
                        '/auth/login',
                    )
                ) {
                    authStore.logout();
                    void router.navigate([
                        '/login',
                    ]);
                }
                return throwError(
                    () => error,
                );
            },
        ),
    );
};