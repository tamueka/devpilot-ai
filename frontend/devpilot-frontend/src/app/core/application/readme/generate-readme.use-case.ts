import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import {
    GeneratedReadme,
    GenerateReadmeRequest,
} from '@core/domain/readme/readme.model';
import { ReadmeRepository } from '@core/domain/readme/readme.repository';

@Injectable({
    providedIn: 'root',
})
export class GenerateReadmeUseCase {
    private readonly readmeRepository = inject(
        ReadmeRepository,
    );

    execute(
        request: GenerateReadmeRequest,
    ): Observable<GeneratedReadme> {
        return this.readmeRepository.generate(
            request,
        );
    }
}