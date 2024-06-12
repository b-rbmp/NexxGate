# NexxGate
Next-generation gateway for secure keyless access, leveraging NFC and ESP32

## Team

| **Name / Surname** | **Linkedin** | **GitHub** |
| :---: | :---: | :---: |
| `Bernardo Perrone De Menezes Bulcao Ribeiro ` | [![name](https://github.com/b-rbmp/NexxGate/blob/main/docs/logos/linkedin.png)](https://www.linkedin.com/in/b-rbmp/) | [![name](https://github.com/b-rbmp/NexxGate/blob/main/docs/logos/github.png)](https://github.com/b-rbmp) |
| `Roberta Chissich ` | [![name](https://github.com/b-rbmp/NexxGate/blob/main/docs/logos/linkedin.png)](https://www.linkedin.com/in/roberta-chissich/) | [![name](https://github.com/b-rbmp/NexxGate/blob/main/docs/logos/github.png)](https://github.com/RobCTs) |


## Table of Contents
+ [About](#about)
+ [Features](#features)
+ [Architecture](#architecture)
+ [Backend](#backend)
+ [Frontend](#frontend)
+ [ESP32 Project](#esp32-project)
+ [Measurements](#measurements)
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

The NexxGate project consists of three main components: the Cloud Server, the Edge Server and the ESP32 Node. The Cloud Server is responsible for managing users, access lists, and logs, being composed of a backend server and a frontend web interface. The Backend Server is implemented using FastAPI (Python), while the Frontend is implemented using React (JavaScript). The Data is stored in a PostgreSQL database, and the communication between the Cloud Server and the Edge Servers is done using MQTT with TLS encryption and also HTTPS.

The Edge Server is responsible for managing the access control devices (ESP32 Nodes) in a local network, ensuring that the devices can operate autonomously even when the Cloud Server is offline. The Edge Server is implemented using Python, and multiples Edge Servers can be deployed in the same Edge Network to provide redundancy and fault tolerance. Edge Servers can cooperate with each other to define the access list and ensure that the devices can authenticate users even when the Cloud Server is down. It also implements a unique key lockout mechanism to prevent unauthorized access through cloned NFC tags and provides a SHA-256 digital signature to allow the ESP32 nodes to verify the authenticity and integrity of the cached UID list.

The ESP32 Node is the access control device that interacts with the NFC tags/cards and communicates with the Edge Server to authenticate users. The ESP32 Node is implemented using ESP-IDF (C), and it uses the ESP32's NFC capabilities to read the NFC tags/cards. The ESP32 Node stores a rolling list of recent and frequent user credentials, ensuring that it can authenticate known users even when the Edge Server is offline. The ESP32 Node also implements an energy-saving mode to reduce energy consumption during idle times. The communication between the ESP32 Node and the Edge Server is done using MQTT with TLS encryption. It has a signature verification mechanism to ensure the authenticity and integrity of the cached UID list by using the public key of the Edge Server to verify the signature sent along with the Access List. For the Prototype, the ESP32 Node is connected to a relay module and a Solenoid Lock to simulate the door lock mechanism.

The overall architecture of the NexxGate project is shown in the diagram below:

![NexxGate Architecture](/docs/images/architecture/overall_arch_dark.png "NexxGate Architecture")


### Solution Overview

The main goal of this project was to address the challenges and problems that are common in traditional access control systems and then problems that arise from the use of semi-autonomous IoT systems. The focus was on the problems listed in the "Objectives" section, and the solution was designed to address them.

Listed below are each of the solutions implemented in the NexxGate project, for each of the problems listed in the "Objectives" section:

1. **Reliability and Robustness of Access**: Centralized Edge Server or Cloud Server happens to go offline during a power outage or network failure, the access control system should still be able to operate autonomously, allowing authorized users to enter and exit the premises.
    - **Solution 1**: Persistent Rolling Access List - Each device contains a rolling list of recent and frequent user credentials, ensuring that when the server is down, the device can authenticate known users. The Edge Server periodically updates the device with the latest access lists containing the 100 most frequent users for that edge server region. The device stores the list in non-volatile memory, ensuring that the list is not lost during power outages.
    - **Solution 2**: ESP32 Node Cooperation - When the communication with the Edge Server is lost, the ESP32 nodes in the same Edge Network communicate with each other to generate a consensus on the access list. This ensures that even if the Edge Server is down, the devices can still authenticate users based on the consensus list generated by the ESP32 nodes, with each node voting using the access list stored in its non-volatile memory.

    
        A diagram showing the ESP32 Node Cooperation mechanism is shown below:

        ![Node Cooperation](/docs/images/architecture/device_reliability.png "Node Cooperation")

    - **Solution 3**: Edge Server Cooperation - When the communication with the Cloud Server is lost, the Edge Servers in the same Edge Network communicate with each other to generate a consensus on the access list. This ensures that even if the Cloud Server is down, the Edge Servers can still define the access list.


2. **Security**: 
    - **Tampering / Interception**: Unauthorized users may attempt to intercept packets and clone credentials to gain unauthorized access.
        - **Solution**: End-to-End Encryption - All communication between the ESP32 nodes and the Edge Server is done using MQTT with TLS encryption. This ensures that all data packets are encrypted and cannot be intercepted by unauthorized users.
    - **Data Integrity**: Data packets may be altered in transit, leading to unauthorized access or denial of service.
        - **Solution**: Using digital signatures to verify the authenticity and integrity of the cached UID list assymetrically -> The edge server signs the data with its private key before sending it to the NFC devices, and the devices uses the server's public key to verify the signature, ensuring that it has not been compromised, before updating the list.

            A diagram showing the Digital Signature Verification mechanism is shown below:

            ![Signature System](/docs/images/architecture/signature_system.png "Signature System")

    - **NFC UID cloning**: Unauthorized users may clone NFC tags to gain unauthorized access, and use this method for a coordinated attack to gain access through multiple nodes at the same time.
        - **Solution**: Implemented a Time-Based Unique Key Lockout Mechanism with a Counter on the Edge Server level, where when an UID is scanned, the device sends an Access request with a timestamp and the edge maintains a counter for each timestamp and checking the timestamp for each UID recently scanned with the previous timestamp it was scanned anywhere in the local network. If a new access request for the same UID comes in within a defined lockout period (10  seconds) from a different node, the edge server will flag the UID and block it, propagating the changes to other nodes in the local network

            A diagram showing the Unique Key Lockout Mechanism is shown below:

            ![Unique Key Lockout](/docs/images/architecture/Lockout.png "Unique Key Lockout")

3. **Energy Consumption during idle times**: The system should consume minimal energy when idle to reduce costs and environmental impact, example: Running during off-hours.
    - **Solution**: Implemented a Energy Savings Mode, where if 30 minutes passes without any scan being recorded, the ESP32 enters a sleep-wake cycle of 3s, where 3s passes being light sleep, and 1.5s passes being active. If an RFID is scanned during this 1.5s, the 30 minutes interval resets.


### Backend <a name = "backend"></a>

The backend server is implemented using FastAPI, a modern, fast (high-performance), web framework for building APIs based on standard Python type hints. The backend server is responsible for managing users, access lists, and logs, and it communicates with the Edge Servers using MQTT with TLS encryption. The backend server provides RESTful APIs for managing users, access lists, and logs, and it also provides APIs for real-time communication with the frontend web interface, and also for Heartbeat communication with the Edge Servers and the ESP32 Nodes.

It communicates with the PostgreSQL database to store and retrieve user information, access lists, and logs. The Access Lists are available for each Edge Server which obtains the list using the RESTful API provided by the backend server. The backend also listens to the cloud MQTT broker for authentication messages from the Edge Servers, which is used to instantly update the logs. There is also a fallback mechanism where regularly the Edge Servers send their local access logs to the backend server, which the difference between the logs is calculated and the logs are updated.

The Swagger interface with the API documentation is available at the endpoint provided in the Demo section, and can be seen in the image below:

![Swagger Interface](/docs/images/backend/swagger.png "Swagger Interface")

### Frontend <a name = "frontend"></a>

The frontend web interface is implemented using React, a popular JavaScript library for building user interfaces. The frontend provides a user-friendly interface for viewing key metrics and the access logs. Currently the management of users and access lists is done through the backend server, due to time constraints, but the frontend can be easily extended to provide these features. The frontend communicates with the backend server using RESTful APIs to retrieve the access logs and metrics.

A screenshot of the frontend web interface is shown below:

![Frontend Interface](/docs/images/frontend/dashboard.png "Frontend Interface")

### ESP32 Project <a name = "esp32-project"></a>

The ESP32 project is responsible for the firmware of the ESP32 microcontroller, which is the core of the NexxGate system. The ESP32 project is implemented using ESP-IDF. The Hardware list for the prototype is as follows:
- Heltec WiFi LoRa 32(V3) Development Board
- RC522 RFID Module
- Relay Module
- Solenoid Lock
- Red, Yellow and Blue LEDs
- 3 Resistors (2000 Ohm)
- 12V Power Supply
- 5V Power Supply

4 GPIOs (35, 34, 33, 47) were used to configure a SPI interface with the RC522 RFID Module, 3 GPIOs (45, 42, 43) were used to control the LEDs and 1 GPIO (7) was used to control the Relay. 

The ESP32 Node is responsible for reading the NFC tags/cards using the RC522 RFID Module, and it authenticates users by comparing the scanned UID with the access list stored in the ESP32's non-volatile memory.

The RC522 NFC Reader is interfaced using the [ESP-IDF-RC522 Library](https://github.com/abobija/esp-idf-rc522).

The Access List only has the 100 most frequent users in that Edge Server region, and in case a UID is not found in the list, the ESP32 Node sends an access request to the Edge Server using the /authenticate topic, which then checks the UID against the full access list and sends a response back to the ESP32 Node under the /allow_authentication topic. In case two different ESP32 Nodes scan the same UID within a defined lockout period (10 seconds), the Edge Server will block the UID and propagate the changes to the other nodes in the local network using the /remove_uid topic.

The access list is updated periodically by requesting it over the "/request_access_list" topic, where the Edge Server will send the updated list to the ESP32 Node under the "/response_access_list" topic. The ESP32 Node verifies assymetrically the authenticity and integrity of the access list by using the public key of the Edge Server to verify the signature sent along with the Access List with the mbedtls library, before saving it to the non-volatile memory.

In case the Edge Server is down, the ESP32 Node will communicate with other ESP32 Nodes in the same Edge Network to generate a consensus on the access list, where a node starts a majority vote process to determine the access list by sending a message to the "/device_majority_vote" topic, and the other nodes respond with their access list under the "/device_majority_response" topic, and the access list with the most votes is then used by the node.

It also sends a heartbeat message directly to the backend server using HTTP, in order to signal that the device is still operational, and the backend server can then use this information to keep track of the devices that are online.

Finally, the ESP32 Node implements an energy-saving mode to reduce energy consumption during idle times, where if 30 minutes passes without any scan being recorded, the ESP32 enters a sleep-wake cycle of 3s, where 3s passes being light sleep, and 1.5s passes being active. If an RFID is scanned during this 1.5s, the 30 minutes interval resets.


## Measurements <a name = "measurements"></a>


## Demo <a name = "demo"></a>

## Installation <a name = "installation"></a>


