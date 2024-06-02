import { Box, Text } from "@chakra-ui/react";


function StatisticsCard({ label, count }: { label: string, count: number }) {
    return (
      <Box
        p="5"
        bg="#004aad"
        borderRadius="xl"
        boxShadow="lg"
        textAlign="center"
        width="100%"
      >
        <Text fontSize="2xl" fontWeight="bold" textColor="white">
          {count}
        </Text>
        <Text textColor="gray.100">{label}</Text>
      </Box>
    );
  }

export default StatisticsCard;