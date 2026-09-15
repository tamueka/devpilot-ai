import {
    HttpInterceptorFn,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthTokenStorage } from '../storage/auth-token.storage';


export const authInterceptor: HttpInterceptorFn = (
    request,
    next,
) => {
    const tokenStorage = inject(
        AuthTokenStorage,
    );
    const token =
        tokenStorage.getToken();

    if (!token) {
        return next(request);
    }
    const authenticatedRequest =
        request.clone({
            setHeaders: {
                Authorization:
                    `Bearer ${token}`,
            },
        });

    return next(
        authenticatedRequest,
    );
};
