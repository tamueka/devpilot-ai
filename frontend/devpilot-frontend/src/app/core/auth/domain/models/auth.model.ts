export interface AuthUser {
    id: string;
    email: string;
    isActive: boolean;
    createdAt: string;
}

export interface LoginCredentials {
    email: string;
    password: string;
}

export interface RegisterCredentials {
    email: string;
    password: string;
}

export interface AuthToken {
    accessToken: string;
    tokenType: string;
}