
export type TAccessLogMetricsItem = {
    hour: string;
    count: number;
}

export type TAccessLogFrontEnd = {
    device_node_id: string;
    timestamp: string;
    uid: string;
    edge_server_name: string;
    granted: boolean;
}