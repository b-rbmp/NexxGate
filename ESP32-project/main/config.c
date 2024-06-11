#include "config.h"
#include "esp_wifi.h"
#include "esp_sntp.h"
#include "esp_log.h"

const char *ssid = "WIFI-SPAZIO-IMPERO";
const char *pass = "SpazioImpero";
const char *mqtt_address = "mqtts://172.27.73.117:8883";

#define CONFIG_TAG "CONFIG"

int retry_num = 0;

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

void wifi_connection()
{
    //                          s1.4
    // 2 - Wi-Fi Configuration Phase
    esp_netif_init();
    esp_event_loop_create_default();     // event loop                    s1.2
    esp_netif_create_default_wifi_sta(); // WiFi station                      s1.3
    wifi_init_config_t wifi_initiation = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&wifi_initiation); //
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
    // esp_log_write(ESP_LOG_INFO, "Kconfig", "SSID=%s, PASS=%s", ssid, pass);
    esp_wifi_set_config(ESP_IF_WIFI_STA, &wifi_configuration);
    // 3 - Wi-Fi Start Phase
    esp_wifi_start();
    esp_wifi_set_mode(WIFI_MODE_STA);
    // 4- Wi-Fi Connect Phase
    esp_wifi_connect();
    ESP_LOGI(CONFIG_TAG, "wifi_init_softap finished. SSID:%s  password:%s", ssid, pass);
}


void initialize_sntp(void) {
    // Update deprecated function names to the new ones
    esp_sntp_setoperatingmode(SNTP_OPMODE_POLL);
    esp_sntp_setservername(0, "pool.ntp.org"); // Using the NTP pool project server
    esp_sntp_init();
}

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

void get_iso8601_time(char *buf, size_t buf_len) {
    time_t now;
    struct tm timeinfo;
    time(&now);
    localtime_r(&now, &timeinfo);

    // Generate the current time in ISO8601 format without timezone information
    strftime(buf, buf_len, "%Y-%m-%d %H:%M:%S", &timeinfo);
}


