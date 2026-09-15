import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import {
    GeneratedUnitTests,
    GenerateUnitTestsRequest,
    ProjectDocument,
} from '@core/domain/unit-tests/unit-test.model';
import { UnitTestRepository } from '@core/domain/unit-tests/unit-test.repository';
import { environment } from '@env/environment';
import {
    GenerateUnitTestsRequestDto,
    GenerateUnitTestsResponseDto,
    ProjectDocumentResponseDto,
} from './unit-test-api.dto';

@Injectable()
export class UnitTestApiRepository
    extends UnitTestRepository {
    private readonly http = inject(HttpClient);
    private readonly apiUrl = environment.apiUrl;

    override getProjectDocuments(
        projectId: string,
    ): Observable<readonly ProjectDocument[]> {
        return this.http
            .get<readonly ProjectDocumentResponseDto[]>(
                `${this.apiUrl}/projects/${projectId}/documents`,
            )
            .pipe(
                map((documents) =>
                    documents.map((document) =>
                        this.toProjectDocumentDomain(
                            document,
                        ),
                    ),
                ),
            );
    }

    override generate(
        request: GenerateUnitTestsRequest,
    ): Observable<GeneratedUnitTests> {
        const requestDto: GenerateUnitTestsRequestDto = {
            project_id: request.projectId,
            document_id: request.documentId,
            framework: request.framework ?? null,
        };

        return this.http
            .post<GenerateUnitTestsResponseDto>(
                `${this.apiUrl}/projects/${request.projectId}/unit-tests`,
                requestDto,
            )
            .pipe(
                map((response) =>
                    this.toGeneratedUnitTestsDomain(
                        response,
                    ),
                ),
            );
    }

    private toProjectDocumentDomain(
        document: ProjectDocumentResponseDto,
    ): ProjectDocument {
        return {
            id: document.id,
            projectId: document.project_id,
            path: document.path,
            filename: document.filename,
            extension: document.extension,
            language: document.language,
            size: document.size,
        };
    }

    private toGeneratedUnitTestsDomain(
        response: GenerateUnitTestsResponseDto,
    ): GeneratedUnitTests {
        return {
            content: response.content,
            suggestedFilename:
                response.suggested_filename,

            sources: response.sources.map(
                (source) => ({
                    path: source.path,
                    language: source.language,
                }),
            ),
        };
    }
}