import { Routes } from '@angular/router';
import { authGuard } from '@core/auth/application/guards/auth.guard';


export const routes: Routes = [
    {
        path: 'login',
        loadComponent: () =>
            import(
                './features/auth/login/login'
            ).then(
                (module) => module.Login,
            ),
    },
    {
        path: 'register',
        loadComponent: () =>
            import(
                './features/auth/register/register'
            ).then(
                (module) => module.Register,
            ),
    },
    {
        path: '',
        canActivate: [
            authGuard,
        ],
        loadComponent: () =>
            import(
                './main-layout/main-layout'
            ).then(
                (module) => module.MainLayout,
            ),
        children: [
            {
                path: '',
                pathMatch: 'full',
                redirectTo: 'projects',
            },
            {
                path: 'projects',
                loadComponent: () =>
                    import(
                        './features/projects/projects'
                    ).then(
                        (module) => module.Projects,
                    ),
            },
            {
                path: 'chat',
                loadComponent: () =>
                    import(
                        './features/chat/chat'
                    ).then(
                        (module) => module.Chat,
                    ),
            },
        ],
    },
    {
        path: '**',
        redirectTo: 'projects',
    },
];