// Define GPIO pins for LED indicators
#define LED_YELLOW GPIO_NUM_45   // Line for Yellow
#define LED_BLUE GPIO_NUM_42  // Line for Blue
#define LED_RED GPIO_NUM_46  // Line for Red

// define GPIO pins for RFID
#define PIN_NUM_MISO GPIO_NUM_35
#define PIN_NUM_MOSI GPIO_NUM_34
#define PIN_NUM_CLK  GPIO_NUM_33
#define PIN_NUM_CS   GPIO_NUM_47

// Define GPIO for Relay Control (Solenoid)
#define RELAY_CONTROL GPIO_NUM_7

#define MAX_UIDS 100  // Maximum number of UIDs we can store
#define UID_LENGTH 10 // Assuming UID length to be 10 characters

#define NODE_ID "node123456" // Node ID for the device 
#define HEARTBEAT_LINK "http://54.235.119.167:8000/nexxgate/api/v1/device_heartbeat/"
#define API_KEY "ADK109CAmakd" // API Key for the device 

// Power saving mode
#define POWER_SAVINGS_MODE 1 // Enable power savings mode
#define INITIAL_IDLE_PERIOD 30*60 // Initial idle period in seconds (30 minutes)
#define SLEEP_WAKE_INTERVAL 3000 // Sleep-wake interval in milliseconds (3 seconds)
#define DUTY_CYCLE 50 // Duty cycle in percentage (50% of SLEEP_WAKE_INTERVAL will be active during the wake period)

// LOGGING
#define RC522_TAG "rc522"
#define AUTH_TAG "AUTH"
#define MQTT_TAG "MQTT"
#define POWER_SAVING_TAG "POWER_SAVING"
#define HTTP_TAG "HTTP_CLIENT"
#define NVS_TAG "NVS"
#define DEVICE_MAJORITY_VOTE_TAG "DEVICE_MAJORITY_VOTE"
#define SECURITY_TAG "SECURITY"

// MQTT
#define ALLOW_AUTHENTICATION_TOPIC "/allow_authentication"
#define ACCESS_LIST_TOPIC "/access_list"
#define RESPONSE_ACCESS_LIST_TOPIC "/response_access_list"
#define REQUEST_ACCESS_LIST_TOPIC "/request_access_list"
#define AUTHENTICATE_TOPIC "/authenticate"
#define DEVICE_MAJORITY_VOTE_TOPIC "/device_majority_vote"
#define DEVICE_MAJORITE_RESPONSE_TOPIC "/device_majority_response"
#define REMOVE_UID_TOPIC "/remove_uid"

// NVS
#define STORAGE_NAMESPACE "storage"
#define UIDS_STORAGE_KEYS "uids"

// MAJORITY VOTING PROCEDURE
#define MAX_DEVICES_PARTICIPATING_MAJ_VOTE 5 // Maximum number of devices participating in the majority voting procedure
