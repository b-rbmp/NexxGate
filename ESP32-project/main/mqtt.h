
#include <stdbool.h>

// A struct used for passing the JSON message to the /Authenticate topic
typedef struct {
    char uid[11];       // UID with space for null-terminator
    char node_id[11];   // Node ID, assuming similar size as UID
    char date[20];      // Date in ISO8601 format compacted without timezone
    bool result;        // Result as boolean
} AuthenticateMessage;

typedef struct {
    char uid[11];       // UID with space for null-terminator
    char node_id[11];   // Node ID, assuming similar size as UID
    bool result;        // Result as boolean
} AuthenticatedMessage;

void log_error_if_nonzero(const char *message, int error_code);
void mqtt_publish(char *topic, char *data);