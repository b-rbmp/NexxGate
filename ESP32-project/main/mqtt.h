
#include <stdbool.h>
#include <security.h>

#define REQUEST_ACCESS_LIST_TOPIC "/request_access_list"
#define RESPONSE_ACCESS_LIST_TOPIC "/response_access_list"
#define AUTHENTICATE_TOPIC "/authenticate"
#define ACCESS_LIST_TOPIC "/access_list"
#define ALLOW_AUTHENTICATE_TOPIC "/allow_authenticate"



// A struct used for passing the JSON message to the /Authenticate topic
typedef struct {
    char encrypted_uid[ENCRYPTED_UID_LENGTH*2+1];       // UID with space for null-terminator
    char node_id[11];   // Node ID, assuming similar size as UID
    char date[20];      // Date in ISO8601 format compacted without timezone
    bool result;        // Result as boolean
} AuthenticateMessage;

typedef struct {
    char encrypted_uid[ENCRYPTED_UID_LENGTH*2+1];       // UID with space for null-terminator
    char node_id[11];   // Node ID, assuming similar size as UID
    bool result;        // Result as boolean
} AuthenticatedMessage;

void mqtt_app_start(void);