#include "mqtt.h"
#include "mqtt_client.h"
#include "esp_log.h"
#include "config.h"

// MQTT global variables
esp_mqtt_client_handle_t client = NULL;
static bool mqtt_connected = false;

/**
 * Logs an error message if the error code is non-zero.
 *
 * @param message The error message to log.
 * @param error_code The error code to check.
 */
void log_error_if_nonzero(const char *message, int error_code)
{
    if (error_code != 0)
    {
        ESP_LOGE(MQTT_TAG, "Last error %s: 0x%x", message, error_code);
    }
}

/**
 * Publishes a message to the MQTT broker.
 *
 * @param topic The topic to publish the message to.
 * @param data The message data to be published.
 */
void mqtt_publish(char *topic, char *data)
{
    if (mqtt_connected)
    {
        ESP_LOGI(MQTT_TAG, "Publishing message to topic %s: %s\n", topic, data);
        esp_mqtt_client_publish(client, topic, data, 0, 0, 0);
    } else {
        ESP_LOGE(MQTT_TAG, "MQTT not connected. Cannot publish message.");
    }
}



