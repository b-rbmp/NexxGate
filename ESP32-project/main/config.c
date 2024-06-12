#include "config.h"
#include "esp_wifi.h"
#include "esp_sntp.h"
#include "esp_log.h"

// WIFI credentials
const char *ssid = "WIFI-SPAZIO-IMPERO";
const char *pass = "SpazioImpero";

// MQTT address
const char *mqtt_address = "mqtts://172.27.73.117:8883";

// Config Log Tag
#define CONFIG_TAG "CONFIG"

int retry_num = 0;

/**
 * @brief Event handler for WiFi events.
 */
static void wifi_event_handler(void *event_handler_arg, esp_event_base_t event_base, int32_t event_id, void *event_data)
{
    if (event_id == WIFI_EVENT_STA_START)
    {
        ESP_LOGI(CONFIG_TAG, "WIFI CONNECTING....\n");
    }
    else if (event_id == WIFI_EVENT_STA_CONNECTED)
    {
        ESP_LOGI(CONFIG_TAG, "WiFi CONNECTED\n");
    }
    else if (event_id == WIFI_EVENT_STA_DISCONNECTED)
    {
        ESP_LOGE(CONFIG_TAG, "WiFi lost connection\n");
        if (retry_num < 5)
        {
            esp_wifi_connect();
            retry_num++;
            ESP_LOGI(CONFIG_TAG, "Retrying to Connect...\n");
        }
    }
    else if (event_id == IP_EVENT_STA_GOT_IP)
    {
        ESP_LOGI(CONFIG_TAG, "Wifi got IP...\n\n");
    }
}

/**
 * @brief Configures and connects to a Wi-Fi network.
 *
 * This function performs the following steps:
 * 1. Initializes the network interface.
 * 2. Creates the event loop and sets up the Wi-Fi station.
 * 3. Initializes the Wi-Fi module with default settings.
 * 4. Registers event handlers for Wi-Fi and IP events.
 * 5. Sets the Wi-Fi configuration with the provided SSID and password.
 * 6. Starts the Wi-Fi module in station mode.
 * 7. Connects to the Wi-Fi network.
 *
 * @param None
 * @return None
 */
void wifi_connection()
{
    esp_netif_init();
    esp_event_loop_create_default();
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t wifi_initiation = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&wifi_initiation);
    esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, wifi_event_handler, NULL);
    esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, wifi_event_handler, NULL);
    wifi_config_t wifi_configuration = {
        .sta = {
            .ssid = "",
            .password = "",

        }

    };
    strcpy((char *)wifi_configuration.sta.ssid, ssid);
    strcpy((char *)wifi_configuration.sta.password, pass);
    esp_wifi_set_config(ESP_IF_WIFI_STA, &wifi_configuration);
    // 3 - Wi-Fi Start Phase
    esp_wifi_start();
    esp_wifi_set_mode(WIFI_MODE_STA);
    // 4- Wi-Fi Connect Phase
    esp_wifi_connect();
    ESP_LOGI(CONFIG_TAG, "wifi_init_softap finished. SSID:%s  password:%s", ssid, pass);
}

/**
 * @brief Initializes the Simple Network Time Protocol (SNTP) client.
 * 
 * This function sets the operating mode of the SNTP client to poll mode and
 * configures the server name to "pool.ntp.org" using the NTP pool project server.
 * It then initializes the SNTP client.
 */
void initialize_sntp(void) {
    esp_sntp_setoperatingmode(SNTP_OPMODE_POLL);
    esp_sntp_setservername(0, "pool.ntp.org"); // Using the NTP pool project server
    esp_sntp_init();
}

/**
 * @brief Obtains the current system time.
 * 
 * This function initializes the Simple Network Time Protocol (SNTP) and waits for the system time to be set.
 * It retries a maximum of 10 times, with a delay of 2 seconds between each retry, until the time is set or the maximum retry count is reached.
 * 
 */
void obtain_time(void) {
    initialize_sntp();

    // Wait for time to be set
    time_t now = 0;
    struct tm timeinfo = { 0 };
    int retry = 0;
    const int retry_count = 10;
    while (timeinfo.tm_year < (2016 - 1900) && ++retry < retry_count) {
        ESP_LOGI(CONFIG_TAG, "Waiting for system time to be set... (%d/%d)", retry, retry_count);
        vTaskDelay(pdMS_TO_TICKS(2000));
        time(&now);
        localtime_r(&now, &timeinfo);
    }
}

/**
 * @brief Generates the current time in ISO8601 format without timezone information.
 * 
 * This function takes a buffer and its length as input parameters. It retrieves the current time
 * and formats it in ISO8601 format ("%Y-%m-%d %H:%M:%S") without timezone information. The formatted
 * time string is then stored in the provided buffer.
 * 
 * @param buf Pointer to the buffer where the formatted time string will be stored.
 * @param buf_len The length of the buffer.
 */
void get_iso8601_time(char *buf, size_t buf_len) {
    time_t now;
    struct tm timeinfo;
    time(&now);
    localtime_r(&now, &timeinfo);

    // Generate the current time in ISO8601 format without timezone information
    strftime(buf, buf_len, "%Y-%m-%d %H:%M:%S", &timeinfo);
}


