import {
    ChangeDetectionStrategy,
    Component,
    inject,
} from '@angular/core';
import {
    Router,
    RouterLink,
    RouterLinkActive,
    RouterOutlet,
} from '@angular/router';
import { AuthStore } from '@core/auth/application/stores/auth.store';


@Component({
    selector: 'app-main-layout',
    standalone: true,
    imports: [
        RouterOutlet,
        RouterLink,
        RouterLinkActive,
    ],
    templateUrl: './main-layout.html',
    changeDetection:
        ChangeDetectionStrategy.OnPush,
})
export class MainLayout {
    private readonly router =
        inject(Router);
    readonly authStore =
        inject(AuthStore);
    async logout(): Promise<void> {
        this.authStore.logout();
        await this.router.navigate([
            '/login',
        ]);
    }
}