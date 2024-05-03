// Define GPIO pins for LED indicators
#define LED_YELLOW GPIO_NUM_45   // Line for Yellow
#define LED_BLUE GPIO_NUM_42  // Line for Blue
#define LED_RED GPIO_NUM_46  // Line for Red

// Define a list of valid UIDs
char* valid_uids[] = {
    "A5EF1877"
    // Add more UIDs as needed
};

int num_valid_uids = sizeof(valid_uids) / sizeof(valid_uids[0]);
