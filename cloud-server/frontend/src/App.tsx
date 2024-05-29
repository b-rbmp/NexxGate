
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Box, ChakraProvider, Divider, Flex, Progress, Stack, Text } from '@chakra-ui/react';
import Navbar from './components/Navbar';
import { FaShoppingCart, FaBus, FaHome, FaUtensils, FaFilm } from 'react-icons/fa';
import Dashboard from './pages/Dashboard';
import {
  BrowserRouter,
  createBrowserRouter,
  Route,
  RouterProvider,
  Routes,
} from "react-router-dom";


const queryClient = new QueryClient()



function App() {
  return (
      <QueryClientProvider client={queryClient}>
          <ChakraProvider>
            <Flex height="100vh" w="100vw" backgroundColor="#004aad">
              
                <Navbar />
              <Box width="80%" bg="gray.100" p="5" borderLeftRadius="40">
                <Routes>
                  <Route path='/' element={<Dashboard/>}/>
                </Routes>
              </Box>
            </Flex>

            
          </ChakraProvider>
      </QueryClientProvider>  
    
  );
}

export default App;
