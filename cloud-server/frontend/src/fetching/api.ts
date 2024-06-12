import axios from "axios";
import { TAccessLogFrontEnd, TAccessLogMetricsItem } from "./types";

// URL of the API (backend)
const API_URL = "https://nexxgate-backend.onrender.com/nexxgate/api/v1/";

/**
 * Retrieves access log metrics from the server.
 * @returns A promise that resolves to an array of access log metrics.
 */
export const getAccessLogMetrics = async () => {
  const { data }: { data: TAccessLogMetricsItem[] } = await axios.get(
    API_URL + "metrics/access-logs/"
  );
  return data;
};

/**
 * Fetches the total number of accesses from the server.
 * @returns A promise that resolves to the total number of accesses.
 */
export const getTotalAccesses = async () => {
  const { data }: { data: number } = await axios.get(
    API_URL + "metrics/all-accesses/"
  );
  return data;
};

/**
 * Represents the parameters for fetching access logs.
 */
interface GetAccessLogsParams {
  skip?: number;
  limit?: number;
  device_node_id?: number;
  timestamp_start?: string;
  timestamp_end?: string;
  uid?: string;
}

/**
 * Retrieves access logs from the server.
 *
 * @param params - The parameters for the access logs request.
 * @returns A promise that resolves to an array of access logs.
 */
export const getAccessLogs = async (params: GetAccessLogsParams) => {
  const { data }: { data: TAccessLogFrontEnd[] } = await axios.get(
    API_URL + "access_logs_frontend/",
    { params }
  );
  return data;
};
