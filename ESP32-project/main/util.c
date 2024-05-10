#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_heap_caps.h"
#include "util.h"

void print_memory_info(const char *taskName) {
    UBaseType_t uxHighWaterMark = uxTaskGetStackHighWaterMark(NULL);
    ESP_LOGI("NexxGate", "Stack high water mark: %u bytes remaining", (unsigned int) uxHighWaterMark);
    ESP_LOGI("NexxGate", "Heap: Free %u bytes", (unsigned int) esp_get_free_heap_size());
}