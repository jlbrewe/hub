/* tslint:disable */
/* eslint-disable */

/**
 * Stencila Hub Typescript Client
 *
 * This file is auto generated by OpenAPI Generator. Do not edit manually.
 */

import * as runtime from '../runtime';
import {
    InlineObject3,
    InlineObject3FromJSON,
    InlineObject3ToJSON,
    InlineObject4,
    InlineObject4FromJSON,
    InlineObject4ToJSON,
} from '../models';

export interface JobsPartialUpdateRequest {
    id: number;
    data: InlineObject4;
}

export interface JobsUpdateRequest {
    id: number;
    data: InlineObject3;
}

/**
 * 
 */
export class JobsApi extends runtime.BaseAPI {

    /**
     * This action is intended only to be used by the `overseer` service for it to update the details of a job based on events from the job queue.
     * Update a job.
     */
    async jobsPartialUpdateRaw(requestParameters: JobsPartialUpdateRequest): Promise<runtime.ApiResponse<InlineObject4>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling jobsPartialUpdate.');
        }

        if (requestParameters.data === null || requestParameters.data === undefined) {
            throw new runtime.RequiredError('data','Required parameter requestParameters.data was null or undefined when calling jobsPartialUpdate.');
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // Token authentication
        }

        const response = await this.request({
            path: `/jobs/{id}/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'PATCH',
            headers: headerParameters,
            query: queryParameters,
            body: InlineObject4ToJSON(requestParameters.data),
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => InlineObject4FromJSON(jsonValue));
    }

    /**
     * This action is intended only to be used by the `overseer` service for it to update the details of a job based on events from the job queue.
     * Update a job.
     */
    async jobsPartialUpdate(requestParameters: JobsPartialUpdateRequest): Promise<InlineObject4> {
        const response = await this.jobsPartialUpdateRaw(requestParameters);
        return await response.value();
    }

    /**
     * Requires that the user is a Stencila staff member. Does not require the `overseer` to know which project a job is associated with, or have project permission.
     * A view set intended for the `overseer` service to update the status of workers.
     */
    async jobsUpdateRaw(requestParameters: JobsUpdateRequest): Promise<runtime.ApiResponse<InlineObject3>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling jobsUpdate.');
        }

        if (requestParameters.data === null || requestParameters.data === undefined) {
            throw new runtime.RequiredError('data','Required parameter requestParameters.data was null or undefined when calling jobsUpdate.');
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // Token authentication
        }

        const response = await this.request({
            path: `/jobs/{id}/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'PUT',
            headers: headerParameters,
            query: queryParameters,
            body: InlineObject3ToJSON(requestParameters.data),
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => InlineObject3FromJSON(jsonValue));
    }

    /**
     * Requires that the user is a Stencila staff member. Does not require the `overseer` to know which project a job is associated with, or have project permission.
     * A view set intended for the `overseer` service to update the status of workers.
     */
    async jobsUpdate(requestParameters: JobsUpdateRequest): Promise<InlineObject3> {
        const response = await this.jobsUpdateRaw(requestParameters);
        return await response.value();
    }

}
