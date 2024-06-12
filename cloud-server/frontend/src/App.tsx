
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Box, ChakraProvider, Flex } from '@chakra-ui/react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import {
  Route,
  Routes,
} from "react-router-dom";

// Create a client
const queryClient = new QueryClient()

/**
 * Main component of the application.
 * 
 * @returns JSX.Element
 */
function App() {
  return (
      <QueryClientProvider client={queryClient}>
          <ChakraProvider>
            <Flex minH="100vh" w="100vw" backgroundColor="#004aad">
              
                <Navbar />
              <Box width="80%" bg="gray.100" p="5" borderLeftRadius="40">
                <Routes>
                  <Route path='/' element={<Dashboard/>}/>
                  <Route path='/history' element={<History/>}/>
                </Routes>
              </Box>
            </Flex>

            
          </ChakraProvider>
      </QueryClientProvider>  
    
  );
}

export default App;
