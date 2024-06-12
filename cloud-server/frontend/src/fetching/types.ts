
/**
 * Represents an item in the access log metrics.
 */
export type TAccessLogMetricsItem = {
    hour: string;
    count: number;
}

/**
 * Represents an item in the access log.
 */
export type TAccessLogFrontEnd = {
    device_node_id: string;
    timestamp: string;
    uid: string;
    edge_server_name: string;
    granted: boolean;
}