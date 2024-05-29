import { Box, Button, Flex, Table, Tbody, Td, Text, Th, Thead, Tr } from "@chakra-ui/react";
import StatisticsCard from "../components/StatisticsCard";
import { Link } from "react-router-dom";

const statistics = [
 { label: "Total accesses", count: 15000 },
  { label: "Accesses in the last 24h", count: 1200 },
  { label: "Devices connected in the last 24h", count: 85 },
  { label: "Servers connected in the last 24h", count: 15 },
];

const last5Accesses = [
    { device_node_id: 1, timestamp: '2024-05-25 14:30:00', uid: 'UID12345', edge_server_name: 'EdgeServer1' },
    { device_node_id: 2, timestamp: '2024-05-25 14:28:00', uid: 'UID12346', edge_server_name: 'EdgeServer2' },
    { device_node_id: 3, timestamp: '2024-05-25 14:25:00', uid: 'UID12347', edge_server_name: 'EdgeServer1' },
    { device_node_id: 4, timestamp: '2024-05-25 14:20:00', uid: 'UID12348', edge_server_name: 'EdgeServer3' },
    { device_node_id: 5, timestamp: '2024-05-25 14:18:00', uid: 'UID12349', edge_server_name: 'EdgeServer2' },
  ];

function Dashboard() {
  return (
    <Box p="5">
      <Flex justifyContent="space-between">
        {statistics.map((stat, index) => (
          <Box key={index} width="23%">
            <StatisticsCard label={stat.label} count={stat.count} />
          </Box>
        ))}
      </Flex>
      <Box bg="white" p="5" borderRadius="md" boxShadow="md" mt="5">
        <Text fontSize="xl" fontWeight="bold" mb="5">Last 10 Accesses</Text>
        <Table variant="simple">
          <Thead>
            <Tr>
              <Th>Device Node ID</Th>
              <Th>Timestamp</Th>
              <Th>UID</Th>
              <Th>Edge Server Name</Th>
            </Tr>
          </Thead>
          <Tbody>
            {last5Accesses.map((access) => (
              <Tr key={access.device_node_id}>
                <Td>{access.device_node_id}</Td>
                <Td>{access.timestamp}</Td>
                <Td>{access.uid}</Td>
                <Td>{access.edge_server_name}</Td>
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
    </Box>
  );
}

export default Dashboard;
