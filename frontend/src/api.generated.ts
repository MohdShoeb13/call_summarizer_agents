export interface paths {
    "/api/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["health_api_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/samples": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Samples */
        get: operations["list_samples_api_samples_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/calls": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Calls */
        get: operations["list_calls_api_calls_get"];
        put?: never;
        /** Create Call */
        post: operations["create_call_api_calls_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/calls/{call_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Call */
        get: operations["get_call_api_calls__call_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/calls/{call_id}/export": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Export Call */
        get: operations["export_call_api_calls__call_id__export_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** Body_create_call_api_calls_post */
        Body_create_call_api_calls_post: {
            /** File */
            file?: string | null;
            /** Sample Id */
            sample_id?: string | null;
            /**
             * Demo
             * @default false
             */
            demo: boolean;
            /**
             * Simulate Failure
             * @default false
             */
            simulate_failure: boolean;
        };
        /** CallResult */
        CallResult: {
            /** Id */
            id: string;
            /** Title */
            title: string;
            /** Created At */
            created_at: string;
            /**
             * Status
             * @enum {string}
             */
            status: "queued" | "processing" | "completed" | "failed" | "interrupted";
            /** Stage */
            stage: string;
            /**
             * Demo
             * @default false
             */
            demo: boolean;
            /** Transcript */
            transcript?: components["schemas"]["Segment"][];
            summary?: components["schemas"]["Summary"] | null;
            quality?: components["schemas"]["Quality"] | null;
            /** Overall Score */
            overall_score?: number | null;
            /** Events */
            events?: components["schemas"]["Event"][];
            /** Error */
            error?: string | null;
            /**
             * Elapsed Seconds
             * @default 0
             */
            elapsed_seconds: number;
        };
        /** Dimension */
        Dimension: {
            /**
             * Name
             * @enum {string}
             */
            name: "empathy" | "professionalism" | "tone" | "resolution";
            /** Score */
            score: number | null;
            /** Rationale */
            rationale: string;
            /** Evidence Ids */
            evidence_ids: number[];
        };
        /** Event */
        Event: {
            /** Stage */
            stage: string;
            /** Message */
            message: string;
            /** Model */
            model?: string | null;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** Health */
        Health: {
            /** Ready */
            ready: boolean;
            /**
             * Provider
             * @default OpenAI
             */
            provider: string;
        };
        /** Quality */
        Quality: {
            /** Dimensions */
            dimensions: components["schemas"]["Dimension"][];
        };
        /** SampleInfo */
        SampleInfo: {
            /** Id */
            id: string;
            /** Title */
            title: string;
            /** Scenario */
            scenario: string;
        };
        /** Segment */
        Segment: {
            /** Id */
            id: number;
            /**
             * Speaker
             * @default Unknown
             */
            speaker: string;
            /** Text */
            text: string;
        };
        /** Summary */
        Summary: {
            /** Issue */
            issue: string;
            /** Key Points */
            key_points: string[];
            /**
             * Resolution
             * @enum {string}
             */
            resolution: "resolved" | "unresolved" | "escalated" | "unknown";
            /** Resolution Details */
            resolution_details: string;
            /** Action Items */
            action_items: string[];
            /** Tags */
            tags: string[];
            /** Evidence Ids */
            evidence_ids: number[];
        };
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    health_api_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Health"];
                };
            };
        };
    };
    list_samples_api_samples_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SampleInfo"][];
                };
            };
        };
    };
    list_calls_api_calls_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallResult"][];
                };
            };
        };
    };
    create_call_api_calls_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: {
            content: {
                "multipart/form-data": components["schemas"]["Body_create_call_api_calls_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_call_api_calls__call_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    export_call_api_calls__call_id__export_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
}
