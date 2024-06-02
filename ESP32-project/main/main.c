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

static const char* RC522_TAG = "rc522";

static bool waiting_edge_response_allow_auth = false;
static bool result_edge_response_allow_auth = false;
static bool waiting_edge_response_access_list = false;
static bool to_be_authenticated = false;
static char hex_uid_to_be_authenticated[9] = "00000000";
static bool authenticating = false;
static char waiting_uid[ENCRYPTED_UID_LENGTH+1]; // Buffer to store the UID while waiting for the response
spi_device_handle_t spi; // Handle for the SPI device

static rc522_handle_t scanner;

void off_leds() {
    gpio_set_level(LED_BLUE, 0);
    gpio_set_level(LED_RED, 0);
    gpio_set_level(LED_YELLOW, 0);
}

// Function to set up GPIO pins for LEDs as output
void init_leds() {
    esp_rom_gpio_pad_select_gpio(LED_BLUE);
    gpio_set_direction(LED_YELLOW, GPIO_MODE_OUTPUT);
    gpio_set_direction(LED_RED, GPIO_MODE_OUTPUT);
    gpio_set_direction(LED_BLUE, GPIO_MODE_OUTPUT);

    gpio_set_level(LED_BLUE, 0); // Turn off Blue LED
    gpio_set_level(LED_RED, 0);   // Turn off Red LED
    gpio_set_level(LED_YELLOW, 0); // Turn off the Yellow LED

    printf("LEDs initialized.\n");
}

// Function to set up GPIO pin for Relay Control as output
void init_relay() {
    esp_rom_gpio_pad_select_gpio(RELAY_CONTROL);
    gpio_set_direction(RELAY_CONTROL, GPIO_MODE_OUTPUT);
    gpio_set_level(RELAY_CONTROL, 0); // Turn off the relay
    printf("Relay initialized.\n");
}

void setup_auth_data(const char* encrypted_uid, const char* node_id, bool result, AuthenticateMessage *auth_data) {
    char current_time[20];
    get_iso8601_time(current_time, sizeof(current_time));

    strncpy(auth_data->encrypted_uid, encrypted_uid, ENCRYPTED_UID_LENGTH*2+1);
    auth_data->encrypted_uid[ENCRYPTED_UID_LENGTH*2+1] = '\0'; // Ensure null termination

    strncpy(auth_data->node_id, node_id, 11);
    auth_data->node_id[10] = '\0'; // Ensure null termination

    strncpy(auth_data->date, current_time, 20);
    auth_data->date[19] = '\0'; // Ensure null termination

    auth_data->result = result;
}

// Function that authenticates the user
void authenticate_NFC(char* uid) {
    if (!authenticating) {
        authenticating = true;
        bool authenticated = false;
        // Turn on yellow LED
        off_leds();
        gpio_set_level(LED_YELLOW, 1);
        printf("Authenticating UID: %s\n", uid);
        if (uid != NULL) {
            char encrypted_uid[ENCRYPTED_UID_LENGTH*2];

            // Encrypt the incoming UID
            if (encrypt_uid(uid, encrypted_uid) != 0) {
                ESP_LOGI(TAG, "Failed to encrypt UID.");
                authenticated = false;
            } else {
                printf("Encrypted UID: %s\n", encrypted_uid);
                if (is_valid_uid(encrypted_uid)) {
                    printf("UID is recognized. Authentication successful.\n");
                    // Convert the encrypted UID char * to a char[ENCRYPTED_UID_LENGTH+1] array to store in the struct
                    char encrypted_uid_str[ENCRYPTED_UID_LENGTH*2+1];
                    strncpy(encrypted_uid_str, encrypted_uid, ENCRYPTED_UID_LENGTH*2+1); // Assuming 'uid' is null-terminated and has appropriate length
                    encrypted_uid_str[ENCRYPTED_UID_LENGTH*2+1] = '\0'; // Ensure null-termination
                
                    AuthenticateMessage authData;
                    setup_auth_data(encrypted_uid_str, NODE_ID, true, &authData);

                    // Publish the authentication data to the /authenticate topic, converting the struct to JSON
                    char json[600];
                    sprintf(json, "{\"encrypted_uid\":\"%s\",\"node_id\":\"%s\",\"date\":\"%s\",\"result\":%s}", authData.encrypted_uid, authData.node_id, authData.date, authData.result ? "true" : "false");
                    mqtt_publish(AUTHENTICATE_TOPIC, json);
                    authenticated = true;
                } else {
                    printf("UID is not recognized. Checking over Edge Server.\n");
                    // Convert the encrypted UID char * to a char[ENCRYPTED_UID_LENGTH+1] array to store in the struct
                    char encrypted_uid_str[ENCRYPTED_UID_LENGTH*2+1];
                    strncpy(encrypted_uid_str, encrypted_uid, ENCRYPTED_UID_LENGTH*2+1); // Assuming 'uid' is null-terminated and has appropriate length
                    encrypted_uid_str[ENCRYPTED_UID_LENGTH*2+1] = '\0'; // Ensure null-termination

                    AuthenticateMessage authData;

                    setup_auth_data(encrypted_uid_str, NODE_ID, false, &authData);

                    // Publish the authentication data to the /authenticate topic, converting the struct to JSON
                    char json[600];
                    sprintf(json, "{\"encrypted_uid\":\"%s\",\"node_id\":\"%s\",\"date\":\"%s\",\"result\":%s}", authData.encrypted_uid, authData.node_id, authData.date, authData.result ? "true" : "false");

                    mqtt_publish(AUTHENTICATE_TOPIC, json);

                    // Wait 5 seconds for the response from the server
                    result_edge_response_allow_auth = false;
                    waiting_edge_response_allow_auth = true;
                    strncpy(waiting_uid, uid, ENCRYPTED_UID_LENGTH+1); // Copy the Encrypted UID to the waiting UID
                    for (int i = 0; i < 10; i++) {
                        vTaskDelay(500 / portTICK_PERIOD_MS);
                        // Switch the Yellow LED on and off to indicate waiting for response, starting with off
                        gpio_set_level(LED_YELLOW, i % 2);
                        if (!waiting_edge_response_allow_auth) {
                            gpio_set_level(LED_YELLOW, 0);
                            if (result_edge_response_allow_auth) {
                                printf("UID is recognized. Authentication successful.\n");
                                authenticated = true;
                                break;
                            } else {
                                printf("UID is not recognized. Authentication failed.\n");
                                authenticated = false;
                                break;
                            }
                        }
                    }
                }
            }

            
        } else {
            printf("UID is invalid. Authentication failed.\n");
        }
        if (authenticated) {
            // Turn on Green LED
            off_leds();
            gpio_set_level(LED_BLUE, 1);
            gpio_set_level(RELAY_CONTROL, 1); // Turn on the relay
            printf("*****************CARD AUTHENTICATED*****************\r\n");
            vTaskDelay(2000 / portTICK_PERIOD_MS);
            gpio_set_level(RELAY_CONTROL, 0); // Turn off the relay
            off_leds();
        } else {
            // Turn on Red LED
            off_leds();
            gpio_set_level(LED_RED, 1);
            printf("*****************CARD NOT AUTHENTICATED*****************\r\n");
            vTaskDelay(2000 / portTICK_PERIOD_MS);
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
    ESP_LOGD(TAG, "Event dispatched from event loop base=%s, event_id=%" PRIi32, base, event_id);
    esp_mqtt_event_handle_t event = event_data;
    esp_mqtt_client_handle_t client = event->client;
    switch ((esp_mqtt_event_id_t)event_id)
    {
    case MQTT_EVENT_CONNECTED:
        ESP_LOGI(TAG, "MQTT_EVENT_CONNECTED");
        mqtt_connected = true;
        // You can also move subscription logic here if subscriptions need to be reinstated upon reconnection
        esp_mqtt_client_subscribe(client, ALLOW_AUTHENTICATE_TOPIC, 0);
        esp_mqtt_client_subscribe(client, ACCESS_LIST_TOPIC, 0);
        esp_mqtt_client_subscribe(client, RESPONSE_ACCESS_LIST_TOPIC, 0);
        break;
    case MQTT_EVENT_DISCONNECTED:
        ESP_LOGI(TAG, "MQTT_EVENT_DISCONNECTED");
        mqtt_connected = false;
        break;

    case MQTT_EVENT_SUBSCRIBED:
        ESP_LOGI(TAG, "MQTT_EVENT_SUBSCRIBED, msg_id=%d", event->msg_id);
        break;
    case MQTT_EVENT_UNSUBSCRIBED:
        ESP_LOGI(TAG, "MQTT_EVENT_UNSUBSCRIBED, msg_id=%d", event->msg_id);
        break;
    case MQTT_EVENT_PUBLISHED:
        ESP_LOGI(TAG, "MQTT_EVENT_PUBLISHED, msg_id=%d", event->msg_id);
        break;
    case MQTT_EVENT_DATA:
        ESP_LOGI(TAG, "MQTT_EVENT_DATA");
        printf("TOPIC=%.*s\r\n", event->topic_len, event->topic);
        printf("DATA=%.*s\r\n", event->data_len, event->data);

        // Check if Topic is /allow_authentication
        if (strncmp(event->topic, ALLOW_AUTHENTICATE_TOPIC, event->topic_len) == 0) {
            if (waiting_edge_response_allow_auth) {
                // Check if the message is a JSON message
                if (event->data[0] == '{') {
                    // Parse the JSON message
                    cJSON *root = cJSON_Parse(event->data);
                    cJSON *result = cJSON_GetObjectItem(root, "result");
                    cJSON *uid = cJSON_GetObjectItem(root, "uid");
                    cJSON *node_id = cJSON_GetObjectItem(root, "node_id");
                    if (result != NULL) {
                        // Compare the UID in the response with the waiting UID and also the node ID with the current node ID
                        if (strcmp(uid->valuestring, waiting_uid) == 0 && strcmp(node_id->valuestring, NODE_ID) == 0) {
                            if (result->type == cJSON_True) {
                                result_edge_response_allow_auth = true;
                            } else {
                                result_edge_response_allow_auth = false;
                            }
                            waiting_edge_response_allow_auth = false;
                        } else {
                            printf("Received response for a different UID or node ID.\n");
                        }
                        
                    } else {
                        printf("Invalid JSON message received.\n");
                    }
                    cJSON_Delete(root);
                }
            }
        } else if (strncmp(event->topic, RESPONSE_ACCESS_LIST_TOPIC, event->topic_len) == 0) {
            if (waiting_edge_response_access_list) {
                waiting_edge_response_access_list = false;
                // Check if the message is a JSON message
                if (event->data[0] == '{') {
                    // The message has the format: {"access_list": ["str1", "str2", ...], "public_key": "str"}
                    // and update the access list by calling void update_access_list(const char* encrypted_uids[], int count);
                    cJSON *root = cJSON_Parse(event->data);
                    cJSON *access_list = cJSON_GetObjectItem(root, "access_list");
                    cJSON *public_key = cJSON_GetObjectItem(root, "public_key");

                    if (access_list != NULL && cJSON_IsArray(access_list) && public_key != NULL && cJSON_IsString(public_key)) {
                        int count = cJSON_GetArraySize(access_list);
                        const char* encrypted_uids[count];
                        for (int i = 0; i < count; i++) {
                            cJSON *item = cJSON_GetArrayItem(access_list, i);
                            if (cJSON_IsString(item)) {
                                encrypted_uids[i] = item->valuestring;
                            } else {
                                printf("Invalid access list item.\n");
                                cJSON_Delete(root);
                                return;
                            }
                        }
                        // Update the access list
                        update_access_list(encrypted_uids, count);
                        // Update the public key
                        update_public_key(public_key->valuestring);
                        printf("Access list updated.\n");
                    } else {
                        printf("Invalid JSON message received.\n");
                    }
                }
            }
        } else if (strncmp(event->topic, ACCESS_LIST_TOPIC, event->topic_len) == 0) {
            // Check if the message is a JSON message
            if (event->data[0] == '{') {
                // The message has the format: {"access_list": ["str1", "str2", ...], "public_key": "str"}
                // and update the access list by calling void update_access_list(const char* encrypted_uids[], int count);
                cJSON *root = cJSON_Parse(event->data);
                cJSON *access_list = cJSON_GetObjectItem(root, "access_list");
                cJSON *public_key = cJSON_GetObjectItem(root, "public_key");

                if (access_list != NULL && cJSON_IsArray(access_list) && public_key != NULL && cJSON_IsString(public_key)) {
                    int count = cJSON_GetArraySize(access_list);
                    const char* encrypted_uids[count];
                    for (int i = 0; i < count; i++) {
                        cJSON *item = cJSON_GetArrayItem(access_list, i);
                        if (cJSON_IsString(item)) {
                            encrypted_uids[i] = item->valuestring;
                        } else {
                            printf("Invalid access list item.\n");
                            cJSON_Delete(root);
                            return;
                        }
                    }
                    // Update the access list
                    update_access_list(encrypted_uids, count);
                    // Update the public key
                    update_public_key(public_key->valuestring);
                    printf("Access list updated.\n");
                } else {
                    printf("Invalid JSON message received.\n");
                }
            }
        }
        break;
    case MQTT_EVENT_ERROR:
        ESP_LOGI(TAG, "MQTT_EVENT_ERROR");
        if (event->error_handle->error_type == MQTT_ERROR_TYPE_TCP_TRANSPORT)
        {
            log_error_if_nonzero("reported from esp-tls", event->error_handle->esp_tls_last_esp_err);
            log_error_if_nonzero("reported from tls stack", event->error_handle->esp_tls_stack_err);
            log_error_if_nonzero("captured as transport's socket errno", event->error_handle->esp_transport_sock_errno);
            ESP_LOGI(TAG, "Last errno string (%s)", strerror(event->error_handle->esp_transport_sock_errno));
        }
        break;
    default:
        ESP_LOGI(TAG, "Other event id:%d", event->event_id);
        break;
    }
}

static void heartbeat_cloud_task(void *pvParameters)
{
    char local_response_buffer[MAX_HTTP_OUTPUT_BUFFER + 1] = {0};
    // Endpoint is HEARTBEAT_LINK + API_KEY.
    char endpoint[100];
    sprintf(endpoint, "%s%s", HEARTBEAT_LINK, API_KEY);

    esp_http_client_config_t config = {
        .url = endpoint,
        .event_handler = _http_event_handler,
        .user_data = local_response_buffer,        
        .disable_auto_redirect = true,
    };

    while(1) {
        esp_http_client_handle_t client = esp_http_client_init(&config);

        // GET
        esp_err_t err = esp_http_client_perform(client);
        if (err == ESP_OK) {
            ESP_LOGI(TAG, "HTTP GET Status = %d, content_length = %"PRId64,
                    esp_http_client_get_status_code(client),
                    esp_http_client_get_content_length(client));
        } else {
            ESP_LOGE(TAG, "HTTP GET request failed: %s", esp_err_to_name(err));
        }
        ESP_LOG_BUFFER_HEX(TAG, local_response_buffer, strlen(local_response_buffer));

        esp_http_client_cleanup(client);
        // Delay for 30 minutes (1800 seconds)
        vTaskDelay(1800 * 1000 / portTICK_PERIOD_MS);
    }
    
}

void mqtt_app_start(void)
{
    const esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = mqtt_address,
        .buffer.size = 1024 * 10, // Increased Buffer Size // Use to calculate how many UIDs can be stored
    };

    client = esp_mqtt_client_init(&mqtt_cfg);
    /* The last argument may be used to pass data to the event handler, in this example mqtt_event_handler */
    esp_mqtt_client_register_event(client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(client);
}

// Create an Authenticate Task that runs in the background and runs the authenticate_NFC function based on a flag and UID
void authenticate_task(void *pvParameters) {
    while (1) {
        if (to_be_authenticated) {
            authenticate_NFC(hex_uid_to_be_authenticated);
            to_be_authenticated = false;
        }
        vTaskDelay(100 / portTICK_PERIOD_MS);
    }
}

static void rc522_handler(void* arg, esp_event_base_t base, int32_t event_id, void* event_data)
{
    rc522_event_data_t* data = (rc522_event_data_t*) event_data;

    switch(event_id) {
        case RC522_EVENT_TAG_SCANNED: {
                rc522_tag_t* tag = (rc522_tag_t*) data->ptr;
                
                // Convert the serial number to a uint32_t to reverse the byte order
                uint32_t serial_number_32 = (uint32_t) tag->serial_number;

                // Reverse the byte order to match the desired hex output
                uint32_t reversed_serial_number = reverse_byte_order(serial_number_32);

                // Allocate memory for the hex string
                char hex_uid[9]; // 8 characters for the hex value + 1 for null terminator
                sprintf(hex_uid, "%08X", (unsigned int)reversed_serial_number);

                // Print the hexadecimal serial number
                ESP_LOGI(RC522_TAG, "Tag scanned (sn: %s)", hex_uid);
                
                // Authenticate the user outside of the task content
                // Copy the hex UID to the global variable (not store the address) by copying the content strncpy
                strncpy(hex_uid_to_be_authenticated, hex_uid, 9);

                to_be_authenticated = true;
            }
            break;
    }
}

void request_access_list() {
    waiting_edge_response_access_list = true;
    
    mqtt_publish(REQUEST_ACCESS_LIST_TOPIC, "update");

    // Wait 5 seconds for the response from the server and flash all LEDs
    for (int i = 0; i < 10; i++) {
        vTaskDelay(500 / portTICK_PERIOD_MS);
        // Switch the Yellow LED on and off to indicate waiting for response, starting with off
        gpio_set_level(LED_YELLOW, i % 2);
        if (!waiting_edge_response_access_list) {
            gpio_set_level(LED_YELLOW, 0);
            break;
        }
    }

    // Turn off the Yellow LED
    gpio_set_level(LED_YELLOW, 0);
}


// Main application function
void app_main() {
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    wifi_connection();                      // Connects to wifi
    vTaskDelay(20000 / portTICK_PERIOD_MS); // delay is important cause we need to let it connect to wifi

    obtain_time();                          // Obtain time from the NTP server

    mqtt_app_start();                       // MQTT start app as shown above most important code for MQTT

    vTaskDelay(5000 / portTICK_PERIOD_MS); // delay is important cause we need to let it connect

    init_leds(); // Initialize LEDs for signaling
    init_relay(); // Initialize relay control

    request_access_list(); // Request the access list from the edge server

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

    // Create the authenticate task
    xTaskCreate(authenticate_task, "authenticate_task", 8192, NULL, 5, NULL);


    // Heartbeat task (Only when API is deployed to cloud)
    //xTaskCreate(heartbeat_cloud_task, "heartbeat_cloud_task", 8192, NULL, 5, NULL);

    print_memory_info("app_main");
}
