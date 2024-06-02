import {
  Box,
  Button,
  Flex,
  Skeleton,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "@chakra-ui/react";
import StatisticsCard from "../components/StatisticsCard";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  getAccessLogMetrics,
  getAccessLogs,
  getTotalAccesses,
} from "../fetching/api";
import { useMemo } from "react";
import { TAccessLogFrontEnd } from "../fetching/types";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';

function Dashboard() {
  const refreshInterval = 1000 * 5; // 5 seconds

  const { data: accessLogMetricsData, isFetching: accessLogMetricsIsFetching } =
    useQuery({ queryKey: ["accessLogMetrics"], queryFn: getAccessLogMetrics, refetchInterval: refreshInterval});
  const { data: totalAccessesData, isFetching: totalAccessesIsFetching } =
    useQuery({ queryKey: ["totalAccesses"], queryFn: getTotalAccesses, refetchInterval: refreshInterval});

  const accessLogMetricsDataFormatted = useMemo(() => {
    if (!accessLogMetricsData) return [];
    return accessLogMetricsData.map((item) => ({
      hour: item.hour.replace("T", " "),
      count: item.count,
    }));
  }, [accessLogMetricsData]);

  const last5AccessesParams = {
    skip: 0,
    limit: 5,
  };

  const { data: accessLogsData, isFetching: accessLogsIsFetching } = useQuery<
    TAccessLogFrontEnd[]
  >({
    queryKey: ["accessLogs", last5AccessesParams],
    queryFn: () => getAccessLogs(last5AccessesParams),
    refetchInterval: refreshInterval,
  });

  const statistics = useMemo(() => {
    if (!accessLogMetricsDataFormatted)
      return [
        { label: "Total accesses", count: 0 },
        { label: "Accesses in the last 24h", count: 0 },
        { label: "Devices connected in the last 24h", count: 0 },
        { label: "Servers connected in the last 24h", count: 0 },
      ];
    return [
      { label: "Total accesses", count: totalAccessesData },
      {
        label: "Accesses in the last 24h",
        count: accessLogMetricsDataFormatted.reduce((acc, item) => acc + item.count, 0),
      },
      { label: "Devices connected in the last 24h", count: 0 },
      { label: "Servers connected in the last 24h", count: 0 },
    ];
  }, [accessLogMetricsDataFormatted, totalAccessesData]);

  const isMetricsFetching = useMemo(
    () => accessLogMetricsIsFetching || totalAccessesIsFetching,
    [accessLogMetricsIsFetching, totalAccessesIsFetching]
  );

  const isMetricsAlreadyLoadedOnceBool = useMemo(() => {
    return accessLogMetricsDataFormatted !== undefined && totalAccessesData !== undefined;
  }
  , [accessLogMetricsDataFormatted, totalAccessesData]);

  const last5Accesses = useMemo(() => {
    if (!accessLogsData) return [];
    return accessLogsData;
  }, [accessLogsData]);

  // Helper function to format the date for Chart
const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return format(date, 'dd/MM HH:mm');
};

  return (
    <Box p="5">
      <Flex justifyContent="space-between">
        {statistics.map((stat, index) => (
          <Box key={index} width="23%">
            <Skeleton isLoaded={!isMetricsFetching || isMetricsAlreadyLoadedOnceBool} key={index}>
              <StatisticsCard
                label={stat.label}
                count={stat.count !== undefined ? stat.count : 0}
              />
            </Skeleton>
          </Box>
        ))}
      </Flex>
      <Box bg="white" p="5" borderRadius="md" boxShadow="md" mt="5">
        <Text fontSize="xl" fontWeight="bold" mb="5">
          Access Logs Metrics
        </Text>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart
            width={500}
            height={300}
            data={accessLogMetricsDataFormatted}
            
            margin={{
              top: 5,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" tickFormatter={formatDate} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="count" stroke="#8884d8" activeDot={{ r: 8 }} />
          </LineChart>
        </ResponsiveContainer>
      </Box>
      <Skeleton isLoaded={!accessLogsIsFetching || accessLogsData !== undefined}>
        <Box bg="white" p="5" borderRadius="md" boxShadow="md" mt="5">
          <Text fontSize="xl" fontWeight="bold" mb="5">
            Last 5 Attempts
          </Text>
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Device Node ID</Th>
                <Th>Timestamp</Th>
                <Th>UID</Th>
                <Th>Edge Server Name</Th>
                <Th>Access</Th>
              </Tr>
            </Thead>
            <Tbody>
              {last5Accesses.map((access) => (
                <Tr key={access.device_node_id}>
                  <Td>{access.device_node_id}</Td>
                  <Td>{access.timestamp.replace("T", " ")}</Td>
                  <Td>{access.uid}</Td>
                  <Td>{access.edge_server_name}</Td>
                  <Td>{access.granted ? "Granted" : "Denied"}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
          <Box textAlign="center" mt="5">
            <Button colorScheme="blue">
              <Link to="/history">See History</Link>
            </Button>
          </Box>
        </Box>
      </Skeleton>
    </Box>
  );
}

export default Dashboard;
