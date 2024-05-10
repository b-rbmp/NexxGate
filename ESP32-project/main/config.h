// Define GPIO pins for LED indicators
#define LED_YELLOW GPIO_NUM_45   // Line for Yellow
#define LED_BLUE GPIO_NUM_42  // Line for Blue
#define LED_RED GPIO_NUM_46  // Line for Red

#define MAX_UIDS 100  // Maximum number of UIDs we can store
#define UID_LENGTH 10 // Assuming UID length to be 10 characters

#define NODE_ID "node123456" // Node ID for the device (TODO: Do with certificates / safety?)