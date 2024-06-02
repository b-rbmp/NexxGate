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
#define HEARTBEAT_LINK "http://172.27.73.111:8000/nexxgate/api/v1/device_heartbeat/"
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
