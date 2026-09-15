import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import {
    GeneratedReadme,
    GenerateReadmeRequest,
} from '@core/domain/readme/readme.model';
import { ReadmeRepository } from '@core/domain/readme/readme.repository';
import { environment } from '@env/environment';
import {
    GenerateReadmeRequestDto,
    GenerateReadmeResponseDto,
} from './readme-api.dto';

@Injectable()
export class ReadmeApiRepository
    extends ReadmeRepository {
    private readonly http = inject(HttpClient);
    private readonly apiUrl = environment.apiUrl;

    override generate(
        request: GenerateReadmeRequest,
    ): Observable<GeneratedReadme> {
        const requestDto: GenerateReadmeRequestDto = {
            project_id: request.projectId,
            language: request.language,
        };

        return this.http
            .post<GenerateReadmeResponseDto>(
                `${this.apiUrl}/projects/${request.projectId}/readme`,
                requestDto,
            )
            .pipe(
                map((response) => ({
                    content: response.content,
                    sources: response.sources.map(
                        (source) => ({
                            path: source.path,
                            language: source.language,
                        }),
                    ),
                })),
            );
    }
}