import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ProjectDocument } from '@core/domain/unit-tests/unit-test.model';
import { UnitTestRepository } from '@core/domain/unit-tests/unit-test.repository';

@Injectable({
    providedIn: 'root',
})
export class GetProjectDocumentsUseCase {
    private readonly unitTestRepository = inject(
        UnitTestRepository,
    );

    execute(
        projectId: string,
    ): Observable<readonly ProjectDocument[]> {
        return this.unitTestRepository.getProjectDocuments(
            projectId,
        );
    }
}