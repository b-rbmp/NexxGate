
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useQuery } from "@tanstack/react-query";
import { getAccessLogs } from "../fetching/api";
import { useMemo, useState } from "react";
import { TAccessLogFrontEnd } from "../fetching/types";
import {
  Box,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Spinner,
  Center,
  Text
} from "@chakra-ui/react";

/**
 * Renders a table displaying the history of access logs.
 * 
 * @returns JSX.Element
 */
function History() {
  const [pageIndex, setPageIndex] = useState(0);
  const pageSize = 10;

  const lastAccessesParams = {
    skip: 0,
    limit: 1000,
  };

  const { data: accessLogsData, isFetching: accessLogsIsFetching } = useQuery<
    TAccessLogFrontEnd[]
  >({
    queryKey: ["accessLogs", lastAccessesParams],
    queryFn: () => getAccessLogs(lastAccessesParams),
  });

  const tableData = useMemo<TAccessLogFrontEnd[]>(() => {
    if (!accessLogsData) return [];
    return accessLogsData;
  }, [accessLogsData]);

  const pageCount = useMemo(
    () => Math.ceil(tableData.length / pageSize),
    [tableData.length, pageSize]
  );

  const currentPageData = useMemo(() => {
    const start = pageIndex * pageSize;
    const end = start + pageSize;
    return tableData.slice(start, end);
  }, [tableData, pageIndex, pageSize]);

  return accessLogsIsFetching ? (
    <Center>
      <Spinner />
    </Center>
  ) : accessLogsData === undefined ? (
    <Box>No data</Box>
  ) : (
    <Box bg="white" p="5" borderRadius="md" boxShadow="md" mt="5">
          <Text fontSize="xl" fontWeight="bold" mb="5">
            History of Access Logs
          </Text>
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Device Node ID</Th>
            <Th>Timestamp</Th>
            <Th>UID</Th>
            <Th>Edge Server Name</Th>
            <Th>Granted</Th>
          </Tr>
        </Thead>
        <Tbody>
          {currentPageData.map((log) => (
            <Tr key={log.timestamp}>
              <Td>{log.device_node_id}</Td>
              <Td>{log.timestamp}</Td>
              <Td>{log.uid}</Td>
              <Td>{log.edge_server_name}</Td>
              <Td>{log.granted ? "Yes" : "No"}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
      <Box
        mt={4}
        display="flex"
        justifyContent="space-between"
        alignItems="center"
      >
        <Button onClick={() => setPageIndex(0)} disabled={pageIndex === 0}>
          {"<<"}
        </Button>
        <Button
          onClick={() => 
            {
              if (pageIndex > 0) {
                setPageIndex(pageIndex - 1);
            }
          }
          }
          disabled={pageIndex === 0}
        >
          {"<"}
        </Button>
        <Box>
          Page{" "}
          <strong>
            {pageIndex + 1} of {pageCount}
          </strong>{" "}
        </Box>
        <Button
          onClick={() => {
            if (pageIndex < pageCount - 1) {
              setPageIndex(pageIndex + 1);
            }
          }}
          disabled={pageIndex === pageCount - 1}
        >
          {">"}
        </Button>
        <Button
          onClick={() => setPageIndex(pageCount - 1)}
          disabled={pageIndex === pageCount - 1}
        >
          {">>"}
        </Button>
      </Box>
    </Box>
  );
}

export default History;
