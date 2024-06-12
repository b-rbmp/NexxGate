#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "esp_system.h"
#include "nvs_flash.h"
#include "esp_event.h"
#include "esp_log.h"
#include "config.c"
#include "security.c"
#include "mqtt.c"
#include "esp_sntp.h"
#include "util.c"
#include <cJSON.h>
#include <inttypes.h>
#include "rc522.h"
#include "http.c"
#include "freertos/timers.h"
#include "esp_sleep.h"
#include "driver/uart.h"
#include "certs.c" // Include the certificates, won't be included in the repository to avoid leaking the certificates

static bool waiting_edge_response = false;
static bool waiting_edge_response_access_list = false;
static bool result_edge_response = false;
static bool authenticating = false;
static bool powersavings_active = false;

// Device Majorty Vote for Access List
static bool device_majority_vote = false; // Boolean to check if device voting is underway
static char majority_vote_uid_list[MAX_DEVICES_PARTICIPATING_MAJ_VOTE][MAX_UIDS][UID_LENGTH]; // Array to store UIDs for majority voting from at maximum 5 other devices
static int majority_vote_count = 0; // Counter for the number of devices participating in the majority voting procedure
// ----------------------------

static char waiting_uid[11];
spi_device_handle_t spi; // Handle for the SPI device

static rc522_handle_t scanner;

TimerHandle_t powerSavingIdleTimer;


void off_leds()
{
    gpio_set_level(LED_BLUE, 0);
    gpio_set_level(LED_RED, 0);
    gpio_set_level(LED_YELLOW, 0);
}

// Function to set up GPIO pins for LEDs as output
void init_leds()
{
    esp_rom_gpio_pad_select_gpio(LED_BLUE);
    gpio_set_direction(LED_YELLOW, GPIO_MODE_OUTPUT);
    gpio_set_direction(LED_RED, GPIO_MODE_OUTPUT);
    gpio_set_direction(LED_BLUE, GPIO_MODE_OUTPUT);

    gpio_set_level(LED_BLUE, 0);   // Turn off Blue LED
    gpio_set_level(LED_RED, 0);    // Turn off Red LED
    gpio_set_level(LED_YELLOW, 0); // Turn off the Yellow LED

    ESP_LOGI(CONFIG_TAG, "LEDs initialized.\n");
}

// Function to set up GPIO pin for Relay Control as output
void init_relay()
{
    esp_rom_gpio_pad_select_gpio(RELAY_CONTROL);
    gpio_set_direction(RELAY_CONTROL, GPIO_MODE_OUTPUT);
    gpio_set_level(RELAY_CONTROL, 0); // Turn off the relay
    ESP_LOGI(CONFIG_TAG, "Relay initialized.\n");
}

void setup_auth_data(const char *uid, const char *node_id, bool result, AuthenticateMessage *auth_data)
{
    char current_time[20];
    get_iso8601_time(current_time, sizeof(current_time));

    strncpy(auth_data->uid, uid, 11);
    auth_data->uid[10] = '\0'; // Ensure null termination

    strncpy(auth_data->node_id, node_id, 11);
    auth_data->node_id[10] = '\0'; // Ensure null termination

    strncpy(auth_data->date, current_time, 20);
    auth_data->date[19] = '\0'; // Ensure null termination

    auth_data->result = result;
}

// Helper function to compare two lists of UIDs
int compare_uid_lists(char list1[MAX_UIDS][UID_LENGTH], char list2[MAX_UIDS][UID_LENGTH]) {
    for (int i = 0; i < MAX_UIDS; i++) {
        if (strcmp(list1[i], list2[i]) != 0) {
            return 0; // Lists are not equal
        }
    }
    return 1; // Lists are equal
}

// Function to count votes for a particular UID list
int count_votes_for_list(char uid_list[MAX_UIDS][UID_LENGTH], int device_count) {
    int votes = 0;
    for (int i = 0; i < device_count; i++) {
        if (compare_uid_lists(uid_list, majority_vote_uid_list[i])) {
            votes++;
        }
    }
    return votes;
}

// Function that concludes the majority voting procedure by checking the majority vote UID list and updating the access list, by comparing
// the array of UIDs for the 5 devices participating + the own device UID listin the majority voting procedure and updating the access list 
// with the list of UIDs that was voted for by the majority of the devices, by comparing if the lists are equal. If no majority is reached, 
// the access list is not updated.
void conclude_majority_voting() {
    int total_devices = majority_vote_count + 1; // Including the device itself
    int majority_threshold = total_devices / 2 + 1;
    int max_votes = 0;
    char majority_list[MAX_UIDS][UID_LENGTH];
    int majority_found = 0;

    for (int i = 0; i < majority_vote_count; i++) {
        int votes = 0;
        for (int j = 0; j < majority_vote_count; j++) {
            if (compare_uid_lists(majority_vote_uid_list[i], majority_vote_uid_list[j])) {
                votes++;
            }
        }
        // Compare with the device's own list
        if (compare_uid_lists(majority_vote_uid_list[i], valid_uids)) {
            votes++;
        }
        if (votes > max_votes) {
            max_votes = votes;
            memcpy(majority_list, majority_vote_uid_list[i], sizeof(majority_list));
        }
    }

    // Compare the device's own list with others
    int device_votes = 0;
    for (int i = 0; i < majority_vote_count; i++) {
        if (compare_uid_lists(valid_uids, majority_vote_uid_list[i])) {
            device_votes++;
        }
    }
    if (device_votes + 1 > max_votes) { // +1 for the device's own vote
        max_votes = device_votes + 1;
        memcpy(majority_list, valid_uids, sizeof(majority_list));
    }

    if (max_votes >= majority_threshold) {
        const char* uids[MAX_UIDS];
        for (int i = 0; i < MAX_UIDS; i++) {
            uids[i] = majority_list[i];
        }
        update_access_list(uids, MAX_UIDS);
        save_uids_to_nvs();

        majority_found = 1;
        ESP_LOGI(DEVICE_MAJORITY_VOTE_TAG, "Majority reached. Access list updated.\n");
    }

    if (!majority_found) {
        ESP_LOGI(DEVICE_MAJORITY_VOTE_TAG, "No majority reached. Access list not updated.\n");
    }
}


// Task that starts a majority voting procedure for the access list with this node_id by publishing at /device_majority_vote with the nodeId as the payload
static void majority_voting_task(void *pvParameters)
{
    if (!device_majority_vote) {

        // Reset the majority vote UID list to empty strings for all participating devices
        for (int i = 0; i < MAX_DEVICES_PARTICIPATING_MAJ_VOTE; i++)
        {
            for (int j = 0; j < MAX_UIDS; j++)
            {
                memset(majority_vote_uid_list[i][j], 0, UID_LENGTH);
            }
        }

        // Reset the majority vote count
        majority_vote_count = 0;

        device_majority_vote = true;
        // Publish the majority voting message to the /device_majority_vote topic
        char json[100];
        sprintf(json, "{\"node_id\":\"%s\"}", NODE_ID);
        mqtt_publish(DEVICE_MAJORITY_VOTE_TOPIC, json);


        ESP_LOGI(DEVICE_MAJORITY_VOTE_TAG, "Majority voting procedure started.\n");

        // Wait 10s for the response from the other devices by using 
        for (int i = 0; i < 20; i++)
        {
            vTaskDelay(500 / portTICK_PERIOD_MS);
            // Switch the Yellow LED on and off to indicate waiting for response, starting with off
            gpio_set_level(LED_YELLOW, i % 2);
            if (!device_majority_vote)
            {
                gpio_set_level(LED_YELLOW, 0);
                break;
            }
        }

        gpio_set_level(LED_YELLOW, 0);

        conclude_majority_voting();
    } else {
        ESP_LOGW(DEVICE_MAJORITY_VOTE_TAG, "Majority voting procedure already in progress.\n");
    }

    vTaskDelete(NULL);
}



// Function that authenticates the user
void authenticate_NFC(char *uid)
{
    if (!authenticating)
    {
        authenticating = true;
        bool authenticated = false;
        // Turn on yellow LED
        off_leds();
        gpio_set_level(LED_YELLOW, 1);
        ESP_LOGI(AUTH_TAG, "Authenticating UID: %s\n", uid);
        if (uid != NULL)
        {
            if (is_valid_uid(uid))
            {
                ESP_LOGI(AUTH_TAG, "UID is recognized. Authentication successful.\n");
                if (mqtt_connected) {
                    // Convert the UID char * to a char[11] array to store in the struct
                    char uid_array[11];
                    strncpy(uid_array, uid, 11); // Assuming 'uid' is null-terminated and has appropriate length
                    uid_array[10] = '\0';        // Ensure null-termination

                    AuthenticateMessage authData;
                    setup_auth_data(uid_array, NODE_ID, true, &authData);

                    // Publish the authentication data to the /authenticate topic, converting the struct to JSON
                    char json[100];
                    sprintf(json, "{\"uid\":\"%s\",\"node_id\":\"%s\",\"date\":\"%s\",\"result\":%s}", authData.uid, authData.node_id, authData.date, authData.result ? "true" : "false");
                    mqtt_publish(AUTHENTICATE_TOPIC, json);
                    authenticated = true;
                } else {
                    ESP_LOGW(AUTH_TAG, "MQTT not connected. Access not forwarded.\n");
                }
            }
            else
            {
                if (mqtt_connected) {
                    ESP_LOGW(AUTH_TAG, "UID is not recognized. Checking over Edge Server.\n");
                    // Convert the UID char * to a char[11] array to store in the struct
                    char uid_array[11];
                    strncpy(uid_array, uid, 11); // Assuming 'uid' is null-terminated and has appropriate length
                    uid_array[10] = '\0';        // Ensure null-termination

                    AuthenticateMessage authData;

                    setup_auth_data(uid_array, NODE_ID, false, &authData);

                    // Publish the authentication data to the /authenticate topic, converting the struct to JSON
                    char json[100];
                    sprintf(json, "{\"uid\":\"%s\",\"node_id\":\"%s\",\"date\":\"%s\",\"result\":%s}", authData.uid, authData.node_id, authData.date, authData.result ? "true" : "false");

                    mqtt_publish(AUTHENTICATE_TOPIC, json);

                    // Wait 5 seconds for the response from the server
                    result_edge_response = false;
                    waiting_edge_response = true;
                    strncpy(waiting_uid, uid, 11); // Copy the UID to the waiting UID
                    for (int i = 0; i < 10; i++)
                    {
                        vTaskDelay(500 / portTICK_PERIOD_MS);
                        // Switch the Yellow LED on and off to indicate waiting for response, starting with off
                        gpio_set_level(LED_YELLOW, i % 2);
                        if (!waiting_edge_response)
                        {
                            gpio_set_level(LED_YELLOW, 0);
                            if (result_edge_response)
                            {
                                ESP_LOGI(AUTH_TAG, "UID is recognized. Authentication successful.\n");
                                authenticated = true;
                                break;
                            }
                            else
                            {
                                ESP_LOGW(AUTH_TAG, "UID is not recognized. Authentication failed.\n");
                                authenticated = false;
                                break;
                            }
                        }
                    }
                } else {
                    ESP_LOGW(AUTH_TAG, "MQTT not connected. Authentication Failed.\n");
                }
                
            }
        }
        else
        {
            ESP_LOGI(AUTH_TAG, "UID is invalid. Authentication failed.\n");
        }
        if (authenticated)
        {
            // Turn on Green LED
            off_leds();
            gpio_set_level(LED_BLUE, 1);
            gpio_set_level(RELAY_CONTROL, 1); // Turn on the relay
            ESP_LOGI(AUTH_TAG, "*****************CARD AUTHENTICATED*****************\r\n");

            for (int i=0; i<20; i++)
            {
                vTaskDelay(100 / portTICK_PERIOD_MS);
            }
            
            gpio_set_level(RELAY_CONTROL, 0); // Turn off the relay
            off_leds();
        }
        else
        {
            // Turn on Red LED
            off_leds();
            gpio_set_level(LED_RED, 1);
            ESP_LOGI(AUTH_TAG, "*****************CARD NOT AUTHENTICATED*****************\r\n");
            for (int i=0; i<20; i++)
            {
                vTaskDelay(100 / portTICK_PERIOD_MS);
            }
            off_leds();
        }
        authenticating = false;
    }
}


/*
 * @brief Event handler registered to receive MQTT events
 *
 *  This function is called by the MQTT client event loop.
 *
 * @param handler_args user data registered to the event.
 * @param base Event base for the handler(always MQTT Base in this example).
 * @param event_id The id for the received event.
 * @param event_data The data for the event, esp_mqtt_event_handle_t.
 */
static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data)
{
    ESP_LOGD(MQTT_TAG, "Event dispatched from event loop base=%s, event_id=%" PRIi32, base, event_id);
    esp_mqtt_event_handle_t event = event_data;
    esp_mqtt_client_handle_t client = event->client;
    switch ((esp_mqtt_event_id_t)event_id)
    {
    case MQTT_EVENT_CONNECTED:
        ESP_LOGI(MQTT_TAG, "MQTT_EVENT_CONNECTED");
        mqtt_connected = true;
        // You can also move subscription logic here if subscriptions need to be reinstated upon reconnection
        esp_mqtt_client_subscribe(client, ALLOW_AUTHENTICATION_TOPIC, 0);
        esp_mqtt_client_subscribe(client, ACCESS_LIST_TOPIC, 0);
        esp_mqtt_client_subscribe(client, RESPONSE_ACCESS_LIST_TOPIC, 0);
        esp_mqtt_client_subscribe(client, DEVICE_MAJORITY_VOTE_TOPIC, 0);
        esp_mqtt_client_subscribe(client, DEVICE_MAJORITE_RESPONSE_TOPIC, 0);
        esp_mqtt_client_subscribe(client, REMOVE_UID_TOPIC, 0);

        break;
    case MQTT_EVENT_DISCONNECTED:
        ESP_LOGI(MQTT_TAG, "MQTT_EVENT_DISCONNECTED");
        mqtt_connected = false;
        break;

    case MQTT_EVENT_SUBSCRIBED:
        ESP_LOGI(MQTT_TAG, "MQTT_EVENT_SUBSCRIBED, msg_id=%d", event->msg_id);
        break;
    case MQTT_EVENT_UNSUBSCRIBED:
        ESP_LOGI(MQTT_TAG, "MQTT_EVENT_UNSUBSCRIBED, msg_id=%d", event->msg_id);
        break;
    case MQTT_EVENT_PUBLISHED:
        ESP_LOGI(MQTT_TAG, "MQTT_EVENT_PUBLISHED, msg_id=%d", event->msg_id);
        break;
    case MQTT_EVENT_DATA:
        ESP_LOGI(MQTT_TAG, "MQTT_EVENT_DATA");
        printf("TOPIC=%.*s\r\n", event->topic_len, event->topic);
        printf("DATA=%.*s\r\n", event->data_len, event->data);

        // Check if Topic is /allow_authentication
        if (strncmp(event->topic, ALLOW_AUTHENTICATION_TOPIC, event->topic_len) == 0) {
            if (waiting_edge_response)
            {
                // Check if the message is a JSON message
                if (event->data[0] == '{')
                {
                    // Parse the JSON message
                    cJSON *root = cJSON_Parse(event->data);
                    cJSON *result = cJSON_GetObjectItem(root, "result");
                    cJSON *uid = cJSON_GetObjectItem(root, "uid");
                    cJSON *node_id = cJSON_GetObjectItem(root, "node_id");
                    cJSON *signature = cJSON_GetObjectItem(root, "signature");

                    if (!cJSON_IsString(uid) || !cJSON_IsString(signature)) {
                        ESP_LOGE(MQTT_TAG, "Invalid JSON format.");
                        cJSON_Delete(root);
                        return;
                    } else {
                        const char *signature_str = signature->valuestring;
                        const char *uid_str = uid->valuestring;
                        if (verify_signature(uid_str, signature_str) == 0) {
                            if (result != NULL)
                            {
                                // Compare the UID in the response with the waiting UID and also the node ID with the current node ID
                                if (strcmp(uid->valuestring, waiting_uid) == 0 && strcmp(node_id->valuestring, NODE_ID) == 0)
                                {
                                    if (result->type == cJSON_True)
                                    {
                                        // Add the UID to the list of recognized UIDs locally (removed and now using bulk access list update)
                                        // add_uid(uid->valuestring);
                                        result_edge_response = true;
                                    }
                                    else
                                    {
                                        result_edge_response = false;
                                    }
                                    waiting_edge_response = false;
                                }
                                else
                                {
                                    ESP_LOGW(MQTT_TAG, "Received response for a different UID or node ID.\n");
                                }
                            }
                            else
                            {
                                ESP_LOGE(MQTT_TAG, "Invalid JSON message received.\n");
                            }
                            cJSON_Delete(root);
                                } else {
                                    ESP_LOGE(MQTT_TAG, "Invalid signature.");
                                    cJSON_Delete(root);
                                    return;
                                }
                            }
                }
            }
        } else if (strncmp(event->topic, RESPONSE_ACCESS_LIST_TOPIC, event->topic_len) == 0) {
            if (waiting_edge_response_access_list) {
                waiting_edge_response_access_list = false;
                // Check if the message is a JSON message
                if (event->data[0] == '{') {
                    // The message has the format: { "uids": ["str1", "str2", ...], "signature": "str" }
                    // and update the access list by calling void update_access_list(const char* uids[], int count);
                    cJSON *root = cJSON_Parse(event->data);
                    if (root == NULL) {
                        ESP_LOGE(MQTT_TAG, "Error parsing JSON\n");
                        return;
                    }

                    cJSON *uids_json = cJSON_GetObjectItem(root, "uids");
                    cJSON *signature = cJSON_GetObjectItem(root, "signature");

                    if (!cJSON_IsArray(uids_json) || !cJSON_IsString(signature)) {
                        ESP_LOGE(MQTT_TAG, "Invalid JSON format.");
                        cJSON_Delete(root);
                        return;
                    }

                    const char *signature_str = signature->valuestring;
                    char *uids_str = cJSON_PrintUnformatted(uids_json);
                    if (uids_str == NULL) {
                        ESP_LOGE(MQTT_TAG, "Failed to print JSON.");
                        cJSON_Delete(root);
                        return;
                    }
  
                    if (verify_signature(uids_str, signature_str) == 0) {

                        
                        int count = cJSON_GetArraySize(uids_json);
                        const char *uids[count];
                        for (int i = 0; i < count; i++) {
                            cJSON *item = cJSON_GetArrayItem(uids_json, i);
                            if (cJSON_IsString(item)) {
                                uids[i] = item->valuestring;
                            } else {
                                uids[i] = "";
                            }
                        }
                        
                        update_access_list(uids, count);
                        cJSON_Delete(root);

                        // Save UIDs to NVS periodically
                        save_uids_to_nvs();

                        ESP_LOGI(MQTT_TAG, "Access list updated.\n");
                    } else {
                        ESP_LOGE(MQTT_TAG, "UID list verification failed.");
                        cJSON_Delete(root);
                        return;
                    }
                }
            }
        } else if (strncmp(event->topic, ACCESS_LIST_TOPIC, event->topic_len) == 0) {
            // Check if the message is a JSON message
            if (event->data[0] == '{') {
                // The message has the format: { "uids": ["str1", "str2", ...], "signature": "str" }
                // and update the access list by calling void update_access_list(const char* uids[], int count);
                cJSON *root = cJSON_Parse(event->data);
                if (root == NULL) {
                    ESP_LOGE(MQTT_TAG, "Error parsing JSON\n");
                    return;
                }

                cJSON *uids_json = cJSON_GetObjectItem(root, "uids");
                cJSON *signature = cJSON_GetObjectItem(root, "signature");

                if (!cJSON_IsArray(uids_json) || !cJSON_IsString(signature)) {
                    ESP_LOGE(MQTT_TAG, "Invalid JSON format.");
                    cJSON_Delete(root);
                    return;
                }

                const char *signature_str = signature->valuestring;
                char *uids_str = cJSON_PrintUnformatted(uids_json);
                if (uids_str == NULL) {
                    ESP_LOGE(MQTT_TAG, "Failed to print JSON.");
                    cJSON_Delete(root);
                    return;
                }

                if (verify_signature(uids_str, signature_str) == 0) {

                    
                    int count = cJSON_GetArraySize(uids_json);
                    const char *uids[count];
                    for (int i = 0; i < count; i++) {
                        cJSON *item = cJSON_GetArrayItem(uids_json, i);
                        if (cJSON_IsString(item)) {
                            uids[i] = item->valuestring;
                        } else {
                            uids[i] = "";
                        }
                    }
                    
                    update_access_list(uids, count);
                    cJSON_Delete(root);

                    // Save UIDs to NVS periodically
                    save_uids_to_nvs();

                    ESP_LOGI(MQTT_TAG, "Access list updated.\n");
                } else {
                    ESP_LOGE(MQTT_TAG, "UID list verification failed.");
                    cJSON_Delete(root);
                    return;
                }
            }
        } else if (strncmp(event->topic, DEVICE_MAJORITY_VOTE_TOPIC, event->topic_len) == 0) {
            // Check if the message is a JSON message
            if (event->data[0] == '{') {
                // The message has the format: {"node_id":"str"}
                // Check if the node_id is the same as the current node_id
                cJSON *root = cJSON_Parse(event->data);
                if (root == NULL) {
                    ESP_LOGE(MQTT_TAG, "Error parsing JSON\n");
                    return;
                }
                
                cJSON *node_id = cJSON_GetObjectItem(root, "node_id");
                if (node_id != NULL && cJSON_IsString(node_id)) {
                    if (strcmp(node_id->valuestring, NODE_ID) != 0) {
                        // Publish your vote directed at the node_id that sent the original message by publishing with the format: {"node_id":"str","uids":["str1","str2",...]}
                        cJSON *uids = cJSON_CreateArray();
                        for (int i = 0; i < MAX_UIDS; i++) {
                            cJSON *uid = cJSON_CreateString(valid_uids[i]);
                            cJSON_AddItemToArray(uids, uid);
                        }
                        cJSON *vote = cJSON_CreateObject();
                        cJSON_AddStringToObject(vote, "node_id", NODE_ID);
                        cJSON_AddItemToObject(vote, "uids", uids);
                        char *vote_str = cJSON_Print(vote);
                        ESP_LOGI(MQTT_TAG, "Sending majority voting message to %s\n", node_id->valuestring);
                        mqtt_publish(DEVICE_MAJORITE_RESPONSE_TOPIC, vote_str);
                        cJSON_Delete(vote);
                        free(vote_str);
                    } else {
                        ESP_LOGW(MQTT_TAG, "Received majority voting message from the same node. Ignoring.\n");
                    }
                } else {
                    ESP_LOGE(MQTT_TAG, "Invalid JSON message received.\n");
                }
                cJSON_Delete(root);
            }
        } else if (strncmp(event->topic, DEVICE_MAJORITE_RESPONSE_TOPIC, event->topic_len) == 0) {
            if (device_majority_vote) {
                // Check if the message is a JSON message
                if (event->data[0] == '{') {
                    // The message has the format: {"node_id":"str","uids":["str1","str2",...]}
                    // and store the received UID list in the majority_vote_uid_list array
                    cJSON *root = cJSON_Parse(event->data);
                    if (root == NULL) {
                        ESP_LOGE(MQTT_TAG, "Error parsing JSON\n");
                        return;
                    }
                    
                    cJSON *node_id = cJSON_GetObjectItem(root, "node_id");
                    cJSON *uids = cJSON_GetObjectItem(root, "uids");
                    if (node_id != NULL && cJSON_IsString(node_id) && uids != NULL && cJSON_IsArray(uids)) {
                        cJSON *uid;
                        int i = 0;
                        cJSON_ArrayForEach(uid, uids) {
                            if (cJSON_IsString(uid)) {
                                strcpy(majority_vote_uid_list[majority_vote_count][i], uid->valuestring);
                                i++;
                            }
                        }
                        majority_vote_count++;
                        ESP_LOGI(MQTT_TAG, "Received majority voting message");
                    } else {
                        ESP_LOGE(MQTT_TAG, "Invalid JSON message received.\n");
                    }
                    cJSON_Delete(root);
                }
            }
        } else if (strncmp(event->topic, REMOVE_UID_TOPIC, event->topic_len) == 0) {
            // Check if the message is a JSON message
            if (event->data[0] == '{') {
                // The message has the format: { "uid": "str", "signature": "str" }, knowing it can have a maximum of 10 characters but less than that too.
                // and remove the UID from the access list by calling void remove_uid(const char* uid);

                cJSON *root = cJSON_Parse(event->data);
                if (root == NULL) {
                    ESP_LOGE(MQTT_TAG, "Error parsing JSON\n");
                    return;
                }

                cJSON *uid = cJSON_GetObjectItem(root, "uid");
                cJSON *signature = cJSON_GetObjectItem(root, "signature");

                if (!cJSON_IsString(uid) || !cJSON_IsString(signature)) {
                    ESP_LOGE(MQTT_TAG, "Invalid JSON format.");
                    cJSON_Delete(root);
                    return;
                }

                const char *signature_str = signature->valuestring;
                if (verify_signature(uid->valuestring, signature_str) == 0) {
                    char *uid_str = uid->valuestring;
                    remove_uid(uid_str);
                    save_uids_to_nvs();
                    ESP_LOGI(MQTT_TAG, "UID: %s removed from access list by the Lockout Mechanism.\n", uid_str);
                } else {
                    ESP_LOGE(MQTT_TAG, "Invalid signature.");
                    cJSON_Delete(root);
                    return;
                }
            }
        
        }
        break;
    case MQTT_EVENT_ERROR:
        ESP_LOGI(MQTT_TAG, "MQTT_EVENT_ERROR");
        if (event->error_handle->error_type == MQTT_ERROR_TYPE_TCP_TRANSPORT)
        {
            log_error_if_nonzero("reported from esp-tls", event->error_handle->esp_tls_last_esp_err);
            log_error_if_nonzero("reported from tls stack", event->error_handle->esp_tls_stack_err);
            log_error_if_nonzero("captured as transport's socket errno", event->error_handle->esp_transport_sock_errno);
            ESP_LOGI(MQTT_TAG, "Last errno string (%s)", strerror(event->error_handle->esp_transport_sock_errno));
        }
        break;
    default:
        ESP_LOGI(MQTT_TAG, "Other event id:%d", event->event_id);
        break;
    }
}

static void heartbeat_cloud(esp_http_client_config_t config)
{
    esp_http_client_handle_t client = esp_http_client_init(&config);

    // GET
    esp_err_t err = esp_http_client_perform(client);
    if (err == ESP_OK)
    {
        ESP_LOGI(HTTP_TAG, "HTTP GET Status = %d, content_length = %" PRId64,
                    esp_http_client_get_status_code(client),
                    esp_http_client_get_content_length(client));
    }
    else
    {
        ESP_LOGE(HTTP_TAG, "HTTP GET request failed: %s", esp_err_to_name(err));
    }

    esp_http_client_cleanup(client);
}

void mqtt_app_start(void)
{
    const esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = mqtt_address,
        .broker.verification.certificate = ca_cert,
        .credentials = {
            .authentication = {
                .certificate = client_cert,
                .key = client_key,
            },
        },
        .network.timeout_ms = 10000,
    };

    client = esp_mqtt_client_init(&mqtt_cfg);
    /* The last argument may be used to pass data to the event handler, in this example mqtt_event_handler */
    esp_mqtt_client_register_event(client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(client);
}

static void wake_up_from_power_savings()
{
    powersavings_active = false;
    esp_wifi_start();
    esp_wifi_set_mode(WIFI_MODE_STA);
    // 4- Wi-Fi Connect Phase
    esp_wifi_connect();

    // Flash the Yellow LED to indicate waking up from power savings for 5 seconds also to allow the connection to stabilize
    for (int i = 0; i < 10; i++)
    {
        gpio_set_level(LED_YELLOW, i % 2);
        vTaskDelay(500 / portTICK_PERIOD_MS);
    }

    // Set the led to off
    gpio_set_level(LED_YELLOW, 0);

    ESP_LOGI(POWER_SAVING_TAG, "WIFI RESTARTED\n");

    esp_mqtt_client_start(client);

    // Flash the Blue Led for 5 seconds to indicate the MQTT connection is being established
    for (int i = 0; i < 10; i++)
    {
        gpio_set_level(LED_BLUE, i % 2);
        vTaskDelay(500 / portTICK_PERIOD_MS);
    }

    // Set the led to off
    gpio_set_level(LED_BLUE, 0);

    ESP_LOGI(POWER_SAVING_TAG,"MQTT RESTARTED\n");

}

static void rc522_handler(void *arg, esp_event_base_t base, int32_t event_id, void *event_data)
{
    rc522_event_data_t *data = (rc522_event_data_t *)event_data;

    switch (event_id)
    {
    case RC522_EVENT_TAG_SCANNED:
    {
        rc522_tag_t *tag = (rc522_tag_t *)data->ptr;

        // Convert the serial number to a uint32_t to reverse the byte order
        uint32_t serial_number_32 = (uint32_t)tag->serial_number;

        // Reverse the byte order to match the desired hex output
        uint32_t reversed_serial_number = reverse_byte_order(serial_number_32);

        // Allocate memory for the hex string
        char hex_uid[9]; // 8 characters for the hex value + 1 for null terminator
        sprintf(hex_uid, "%08X", (unsigned int)reversed_serial_number);

        // Print the hexadecimal serial number
        ESP_LOGI(RC522_TAG, "Tag scanned (sn: %s)", hex_uid);

        // Reset the Power Savings Timer
        if (POWER_SAVINGS_MODE)
        {
            xTimerReset(powerSavingIdleTimer, 0);

            if (powersavings_active)
            {
                wake_up_from_power_savings();
            }
        }

        authenticate_NFC(hex_uid);
    }
    break;
    }
}

static void light_sleep_task(void *pvParameters)
{
    powersavings_active = true;
    u_int8_t i = 0;
    u_int8_t task_delay = 100;
    // Number of iterations to reach SLEEP_WAKE_INTERVAL using the DUTY_CYCLE
    u_int8_t num_iterations = (u_int8_t)((SLEEP_WAKE_INTERVAL * (DUTY_CYCLE / 100.0)) / task_delay);

    // Disable WIFI and MQTT
    esp_mqtt_client_stop(client);
    esp_wifi_stop();

    while (1)
    {
        ESP_LOGI(POWER_SAVING_TAG, "Entering light sleep\n");
        /* To make sure the complete line is printed before entering sleep mode,
         * need to wait until UART TX FIFO is empty:
         */
        uart_wait_tx_idle_polling(CONFIG_ESP_CONSOLE_UART_NUM);
        /* Enter sleep mode */
        esp_sleep_enable_timer_wakeup(SLEEP_WAKE_INTERVAL * 1000); // Configure wake-up interval in microseconds

        esp_light_sleep_start();

        ESP_LOGI(POWER_SAVING_TAG, "Woke up from light sleep\n");
        
        i = 0;
        while (i < num_iterations)
        {
            vTaskDelay(task_delay / portTICK_PERIOD_MS); // Delay to allow the system to stabilize
            i++;
        }

        if (powersavings_active == false)
        {
            break;
        }      

         
    }
    vTaskDelete(NULL);
}

void enter_light_sleep()
{
    xTaskCreate(light_sleep_task, "light_sleep_task", 2048, NULL, 5, NULL);
}

void obtain_access_list() {
    bool use_nvs = false;
    if (mqtt_connected) {
        waiting_edge_response_access_list = true;
    
        mqtt_publish(REQUEST_ACCESS_LIST_TOPIC, "update");

        // Wait 5 seconds for the response from the server and flash yellow LED
        for (int i = 0; i < 10; i++) {
            vTaskDelay(500 / portTICK_PERIOD_MS);
            // Switch the Yellow LED on and off to indicate waiting for response, starting with off
            gpio_set_level(LED_YELLOW, i % 2);
            if (!waiting_edge_response_access_list) {
                gpio_set_level(LED_YELLOW, 0);
                break;
            }
        }

        if (waiting_edge_response_access_list) {
            ESP_LOGW(MQTT_TAG, "No response received for the access list. Using NVS stored access list.\n");
            waiting_edge_response_access_list = false;
            use_nvs = true;
        }
    } else {
        ESP_LOGW(MQTT_TAG, "MQTT not connected. Using NVS stored access list.\n");
        use_nvs = true;
    }

    if (use_nvs) {
        // Load UIDs from NVS
        load_uids_from_nvs();

        // Start the majority voting task
        xTaskCreate(majority_voting_task, "majority_voting_task", 4096, NULL, 5, NULL);
    }
    

    // Turn off the Yellow LED
    gpio_set_level(LED_YELLOW, 0);
}



// Main application function
void app_main()
{
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND)
    {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    wifi_connection();                      // Connects to wifi
    vTaskDelay(20000 / portTICK_PERIOD_MS); // delay is important cause we need to let it connect to wifi

    obtain_time(); // Obtain time from the NTP server

    mqtt_app_start(); // MQTT start app as shown above most important code for MQTT

    vTaskDelay(5000 / portTICK_PERIOD_MS); // delay is important cause we need to let it connect

    init_leds();  // Initialize LEDs for signaling
    init_relay(); // Initialize relay control

    obtain_access_list(); // Request the access list from the edge server

    vTaskDelay(1000 / portTICK_PERIOD_MS); //

    rc522_config_t config = {
        .spi.host = SPI3_HOST,
        .spi.miso_gpio = PIN_NUM_MISO,
        .spi.mosi_gpio = PIN_NUM_MOSI,
        .spi.sck_gpio = PIN_NUM_CLK,
        .spi.sda_gpio = PIN_NUM_CS,
    };

    rc522_create(&config, &scanner);
    rc522_register_events(scanner, RC522_EVENT_ANY, rc522_handler, NULL);

    // Wait 5s for the RC522 to start up
    rc522_start(scanner);

    if (POWER_SAVINGS_MODE)
    {
        // Create a timer to enter light sleep after the initial idle period
        powerSavingIdleTimer = xTimerCreate("powerSavingIdleTimer", INITIAL_IDLE_PERIOD * 1000 / portTICK_PERIOD_MS, pdFALSE, (void *)0, enter_light_sleep);
        xTimerStart(powerSavingIdleTimer, 0);
    }


    // HTTP Heartbeat
    char local_response_buffer[256] = {0};
    // Endpoint is HEARTBEAT_LINK + API_KEY.
    char http_heartbeat_endpoint[100];
    sprintf(http_heartbeat_endpoint, "%s%s", HEARTBEAT_LINK, API_KEY);

    esp_http_client_config_t esp_http_config = {
        .url = http_heartbeat_endpoint,
        .event_handler = _http_event_handler,
        .user_data = local_response_buffer,
        .disable_auto_redirect = true,
    };

    // Periodically send heartbeat to the cloud
    while (1)
    {
        heartbeat_cloud(esp_http_config);
        // Delay for 30 minutes (1800 seconds)
        vTaskDelay(30 * 60 * 60 / portTICK_PERIOD_MS);
    }

    print_memory_info("app_main");
}
