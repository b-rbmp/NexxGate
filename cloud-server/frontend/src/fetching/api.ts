
import axios from "axios";
import { TAccessLogFrontEnd, TAccessLogMetricsItem } from "./types";

const API_URL = "http://34.228.42.62:8000/nexxgate/api/v1/";

export const getAccessLogMetrics = async() => {
    const { data }: {data: TAccessLogMetricsItem[]} = await axios.get(
        API_URL + "metrics/access-logs/"
      );
    return data;
}

export const getTotalAccesses = async() => {
    const { data }: {data: number} = await axios.get(
        API_URL + "metrics/all-accesses/"
      );
    return data;
}

interface GetAccessLogsParams {
    skip?: number;
    limit?: number;
    device_node_id?: number;
    timestamp_start?: string;
    timestamp_end?: string;
    uid?: string;
  }
  
  // Function to get access logs with parameters
  export const getAccessLogs = async (params: GetAccessLogsParams) => {
    const { data }: { data: TAccessLogFrontEnd[] } = await axios.get(
      API_URL + "access_logs_frontend/",
      { params }
    );
    return data;
  };