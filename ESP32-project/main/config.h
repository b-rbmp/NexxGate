// Define GPIO pins for LED indicators
#define LED_YELLOW GPIO_NUM_45   // Line for Yellow
#define LED_BLUE GPIO_NUM_42  // Line for Blue
#define LED_RED GPIO_NUM_46  // Line for Red

// define GPIO pins for RFID
#define PIN_NUM_MISO GPIO_NUM_35
#define PIN_NUM_MOSI GPIO_NUM_34
#define PIN_NUM_CLK  GPIO_NUM_33
#define PIN_NUM_CS   GPIO_NUM_47

#define MAX_UIDS 100  // Maximum number of UIDs we can store
#define UID_LENGTH 10 // Assuming UID length to be 10 characters

#define NODE_ID "node123456" // Node ID for the device 
#define HEARTBEAT_LINK "http://172.27.73.111:8000/nexxgate/api/v1/device_heartbeat/"
#define API_KEY "ADK109CAmakd" // API Key for the device 