import { inject } from '@angular/core';
import {
    CanActivateFn,
    Router,
} from '@angular/router';
import { AuthStore } from '../stores/auth.store';


export const authGuard: CanActivateFn =
    async () => {
        const authStore =
            inject(AuthStore);
        const router =
            inject(Router);

        if (!authStore.token()) {
            return router.createUrlTree([
                '/login',
            ]);
        }
        if (!authStore.user()) {
            await authStore.loadCurrentUser();
        }
        if (
            !authStore.isAuthenticated()
            || !authStore.user()
        ) {
            return router.createUrlTree([
                '/login',
            ]);
        }
        return true;
    };