import { Box, Stack } from '@chakra-ui/react';
import styled from '@emotion/styled';
import { Link, useLocation } from 'react-router-dom';
import { RxDashboard } from "react-icons/rx";
import { RiHistoryFill } from "react-icons/ri";
import { RiSettings2Line } from "react-icons/ri";
import logo from "../images/logo.png";

const Logo = styled.img`
    width: 18vw;
    margin-top: 30px;
    margin-left: 10px;
`

const NavButton = styled("div")<{selected?: boolean}>`
  display: flex;
  color: ${props => props.selected ? "#004aad" : "white"};
  background-color: ${props => props.selected ? "white" : "none"};
  align-items: center;
  padding: 1rem 0px 1rem 2rem;
  margin: 0px 15px 0px 30px;
  border-radius: 15px;
  cursor: pointer;
  transition: all 0.25s ease;

  &:hover {
    background-color: white;
    color: #004aad";
  }
`
const Button = styled.a`
  font-size: 20px;
  margin-left: 10px;
`

function Navbar() {
    const location = useLocation();

    return ( 
        <Box 
          sx={{
            flex:"1",
            height: "100vh",
          }}
        >
          <Logo src={logo} alt="Logo"/>
          <Stack spacing="5">
            <Link to="/" style={{textDecoration: "none"}}>
                <NavButton selected={location.pathname === "/"}>
                  <RxDashboard fontSize='large'/>
                  <Button>Dashboard</Button>
                </NavButton>
              </Link>
              <Link to="/history" style={{textDecoration: "none"}}>
                <NavButton selected={location.pathname === "/history"}>
                  <RiHistoryFill fontSize='large'/>
                  <Button>History</Button>
                </NavButton>
              </Link>
          </Stack>
      </Box>
     );
}

export default Navbar;