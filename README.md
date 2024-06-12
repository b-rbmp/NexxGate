# NexxGate
Next-generation gateway for secure access

## Team

| **Name / Surname** | **Linkedin** | **GitHub** |
| :---: | :---: | :---: |
| `Bernardo Perrone De Menezes Bulcao Ribeiro ` | [![name](https://github.com/b-rbmp/NexxGate/blob/main/docs/logos/linkedin.png)](https://www.linkedin.com/in/b-rbmp/) | [![name](https://github.com/b-rbmp/NexxGate/blob/main/docs/logos/github.png)](https://github.com/b-rbmp) |
| `Roberta Chissich ` | [![name](https://github.com/b-rbmp/NexxGate/blob/main/docs/logos/linkedin.png)](https://www.linkedin.com/in/roberta-chissich/) | [![name](https://github.com/b-rbmp/NexxGate/blob/main/docs/logos/github.png)](https://github.com/RobCTs) |


## Table of Contents
+ [About](#about)
+ [Features](#features)
+ [Architecture](#architecture)
+ [Cloud Server](#cloud-server)
+ [Frontend](#frontend)
+ [ESP32 Project](#esp32-project)
+ [Demo](#demo)
+ [Installation](#installation)


## About <a name = "about"></a>
NexxGate is an innovative access control solution designed to enhance security and flexibility across various environments. Leveraging the power of NFC (Near Field Communication) technology and the robust ESP32 microcontroller, NexxGate enables secure, keyless entry to buildings, rooms, and other secure areas. This project combines the convenience of NFC tags/cards with MQTT communication, also implementing a web interface for user management and access control. NexxGate is a versatile solution that can be easily adapted to different scenarios, such as homes, offices, metro stations, and industrial facilities.

### Why IoT?

Modern access control systems face bottlenecks, vulnerabilities, and latency due to reliance on centralized servers.

IoT offers semi-autonomous operation, local decision-making, and synchronization with broader networks, allowing for more reliable and robust access control systems, at the expense of increased complexity and potential security risks. This project aims to explore that trade-off and develop a secure, efficient, and scalable access control system using IoT technologies.

### Objectives

Develop a secure, reliable, and efficient access control solution, targeting corporate environments. The system should be able to fulfill the following requirements:
- Fast, reliable access decisions.
- High uptime (>99.9%).
- Efficient energy consumption.
- Effective synchronization of access lists and logs.
- Cloud-based management dashboard
- Access through NFC tags

And also address the following challenges and problems that are common in traditional access control systems:
1. Reliability and Robustness of Access: Centralized Edge Server or Cloud Server happens to go offline during a power outage or network failure, the access control system should still be able to operate autonomously, allowing authorized users to enter and exit the premises.
2. Security: 
    - Tampering / Interception: Unauthorized users may attempt to intercept packets and clone credentials to gain unauthorized access.
    - Data Integrity: Data packets may be altered in transit, leading to unauthorized access or denial of service.
    - NFC UID cloning: Unauthorized users may clone NFC tags to gain unauthorized access, and use this method for a coordinated attack to gain access through multiple nodes at the same time.
3. Energy Consumption during idle times: The system should consume minimal energy when idle to reduce costs and environmental impact, example: Running during off-hours.


## Features <a name = "features"></a>

- **Secure Access Control**: NexxGate uses NFC technology to provide secure, keyless access to buildings and rooms.
- **Reliable and Robust**: The system is designed to operate autonomously even when the edge server or cloud server is offline, ensuring high uptime and reliability.
- **End-to-End Encryption**: All communication between devices and the server is encrypted using TLS, ensuring data privacy and integrity.
- **Energy-Efficient Operation**: NexxGate minimizes energy consumption during idle times, reducing costs and environmental impact.
- **Cloud-Based Management**: The system includes a web interface for managing users, access lists, and logs, providing real-time insights and control.
- **Scalable and Versatile**: NexxGate can be easily adapted to different environments, such as homes, offices, metro stations, and industrial facilities.


### Architecture <a name = "architecture"></a>



### Solution Overview

The main goal of this project was to address the challenges and problems that are common in traditional access control systems and then problems that arise from the use of semi-autonomous IoT systems. The focus was on the problems listed in the "Objectives" section, and the solution was designed to address them.

Listed below are each of the solutions implemented in the NexxGate project, for each of the problems listed in the "Objectives" section:

1. **Reliability and Robustness of Access**: Centralized Edge Server or Cloud Server happens to go offline during a power outage or network failure, the access control system should still be able to operate autonomously, allowing authorized users to enter and exit the premises.
    - **Solution 1**: Persistent Rolling Access List - Each device contains a rolling list of recent and frequent user credentials, ensuring that when the server is down, the device can authenticate known users. The Edge Server periodically updates the device with the latest access lists containing the 100 most frequent users for that edge server region. The device stores the list in non-volatile memory, ensuring that the list is not lost during power outages.
    - **Solution 2**: ESP32 Node Cooperation - When the communication with the Edge Server is lost, the ESP32 nodes in the same Edge Network communicate with each other to generate a consensus on the access list. This ensures that even if the Edge Server is down, the devices can still authenticate users based on the consensus list generated by the ESP32 nodes, with each node voting using the access list stored in its non-volatile memory.
    - **Solution 3**: Edge Server Cooperation - When the communication with the Cloud Server is lost, the Edge Servers in the same Edge Network communicate with each other to generate a consensus on the access list. This ensures that even if the Cloud Server is down, the Edge Servers can still define the access list.

2. **Security**: 
    - **Tampering / Interception**: Unauthorized users may attempt to intercept packets and clone credentials to gain unauthorized access.
        - **Solution**: End-to-End Encryption - All communication between the ESP32 nodes and the Edge Server is done using MQTT with TLS encryption. This ensures that all data packets are encrypted and cannot be intercepted by unauthorized users.
    - **Data Integrity**: Data packets may be altered in transit, leading to unauthorized access or denial of service.
        - **Solution**: Using digital signatures to verify the authenticity and integrity of the cached UID list -> The edge server signs the data with its private key before sending it to the NFC devices, and the devices uses the server's public key to verify the signature, ensuring that it has not been compromised, before updating the list.
    - **NFC UID cloning**: Unauthorized users may clone NFC tags to gain unauthorized access, and use this method for a coordinated attack to gain access through multiple nodes at the same time.
        - **Solution**: Implemented a Time-Based Unique Key Lockout Mechanism with a Counter on the Edge Server level, where when an UID is scanned, the device sends an Access request with a timestamp and the edge maintains a counter for each timestamp and checking the timestamp for each UID recently scanned with the previous timestamp it was scanned anywhere in the local network. If a new access request for the same UID comes in within a defined lockout period (10  seconds) from a different node, the edge server will flag the UID and block it, propagating the changes to other nodes in the local network

3. **Energy Consumption during idle times**: The system should consume minimal energy when idle to reduce costs and environmental impact, example: Running during off-hours.
    - **Solution**: Implemented a Energy Savings Mode, where if 30 minutes passes without any scan being recorded, the ESP32 enters a sleep-wake cycle of 3s, where 3s passes being light sleep, and 1.5s passes being active. If an RFID is scanned during this 1.5s, the 30 minutes interval resets.

### Detailed Architecture

### Cloud Server <a name = "cloud-server"></a>

### Frontend <a name = "frontend"></a>

### ESP32 Project <a name = "esp32-project"></a>


## Demo <a name = "demo"></a>

## Installation <a name = "installation"></a>


