#include "mqtt.h"
#include "mqtt_client.h"
#include "esp_log.h"

esp_mqtt_client_handle_t client = NULL;
static const char *TAG = "NexxGate";
static bool mqtt_connected = false;

void log_error_if_nonzero(const char *message, int error_code)
{
    if (error_code != 0)
    {
        ESP_LOGE(TAG, "Last error %s: 0x%x", message, error_code);
    }
}

void mqtt_publish(char *topic, char *data)
{
    if (mqtt_connected)
    {
        printf("Publishing message to topic %s: %s\n", topic, data);
        esp_mqtt_client_publish(client, topic, data, 0, 0, 0);
    } else {
        ESP_LOGE(TAG, "MQTT not connected. Cannot publish message.");
    }
}



