import { Injectable } from '@angular/core';

@Injectable({
    providedIn: 'root',
})
export class AuthTokenStorage {
    private readonly storageKey =
        'devpilot_access_token';

    getToken(): string | null {
        if (
            typeof sessionStorage ===
            'undefined'
        ) {
            return null;
        }

        return sessionStorage.getItem(
            this.storageKey,
        );
    }

    setToken(token: string): void {
        if (
            typeof sessionStorage ===
            'undefined'
        ) {
            return;
        }

        sessionStorage.setItem(
            this.storageKey,
            token,
        );
    }

    clearToken(): void {
        if (
            typeof sessionStorage ===
            'undefined'
        ) {
            return;
        }

        sessionStorage.removeItem(
            this.storageKey,
        );
    }
}