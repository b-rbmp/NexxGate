#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_heap_caps.h"
#include "util.h"
#include "config.h"

/**
 * @brief Prints memory information including stack high water mark and free heap size.
 * 
 * @param taskName The name of the task.
 */
void print_memory_info(const char *taskName) {
    UBaseType_t uxHighWaterMark = uxTaskGetStackHighWaterMark(NULL);
    ESP_LOGI("NexxGate", "Stack high water mark: %u bytes remaining", (unsigned int) uxHighWaterMark);
    ESP_LOGI("NexxGate", "Heap: Free %u bytes", (unsigned int) esp_get_free_heap_size());
}

/**
 * Reverses the byte order of a 32-bit value.
 *
 * @param value The 32-bit value to reverse the byte order of.
 * @return The 32-bit value with the byte order reversed.
 */
uint32_t reverse_byte_order(uint32_t value) {
    uint32_t byte0 = (value & 0x000000FF) << 24;
    uint32_t byte1 = (value & 0x0000FF00) << 8;
    uint32_t byte2 = (value & 0x00FF0000) >> 8;
    uint32_t byte3 = (value & 0xFF000000) >> 24;
    return (byte0 | byte1 | byte2 | byte3);
}
