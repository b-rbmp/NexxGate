#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "security.h"
#include "config.h"
#include "nvs_flash.h"
#include "esp_log.h"

char valid_uids[MAX_UIDS][UID_LENGTH]; // Array to store UIDs
int head = 0; // Head index for the circular buffer
int tail = 0; // Tail index for the circular buffer
int uid_count = 0; // Current count of stored UIDs

// Function to add a UID to the circular buffer
void add_uid(const char* uid) {
    if (uid_count >= MAX_UIDS) {
        // Buffer is full, remove the oldest UID
        head = (head + 1) % MAX_UIDS;
        uid_count--; // Reduce count because we will overwrite an existing UID
    }
    // Add new UID at the tail and update tail position
    strncpy(valid_uids[tail], uid, UID_LENGTH);
    tail = (tail + 1) % MAX_UIDS;
    uid_count++;
}

// Function to remove an UID from the circular buffer if it is present
void remove_uid(const char* uid) {
    int index = head;
    for (int i = 0; i < uid_count; i++) {
        if (strncmp(valid_uids[index], uid, UID_LENGTH) == 0) {
            // UID found, remove it
            for (int j = i; j < uid_count - 1; j++) {
                strncpy(valid_uids[(index + j) % MAX_UIDS], valid_uids[(index + j + 1) % MAX_UIDS], UID_LENGTH);
            }
            tail = (tail - 1 + MAX_UIDS) % MAX_UIDS;
            uid_count--;
            return;
        }
        index = (index + 1) % MAX_UIDS;
    }
}

// Update the access list with a new list of encrypted UIDs by replacing the old list
void update_access_list(const char* uids[], int count) {
    head = 0;
    tail = 0;
    uid_count = count;
    for (int i = 0; i < count; i++) {
        strcpy(valid_uids[tail], uids[i]);
        tail = (tail + 1) % MAX_UIDS;
    }
}

// Function to check if a UID is valid
int is_valid_uid(const char* uid) {
    int index = head;
    for (int i = 0; i < uid_count; i++) {
        if (strncmp(valid_uids[index], uid, UID_LENGTH) == 0) {
            return 1; // UID found
        }
        index = (index + 1) % MAX_UIDS;
    }
    return 0; // UID not found
}

// Function to save UIDs to NVS

// Calculation for how many UIDs can be stored in NVS
//     Overhead per entry: ~32 bytes
//     Size of each UID: 10 bytes
//     Total size per UID entry: 32 bytes (overhead) + 10 bytes (UID) = 42 bytes

// Calculation:

//     Available space: 16KB = 16384 bytes
//     Space per UID: 42 bytes

// Total available space​=16384/42=390 UIDs

void save_uids_to_nvs() {
    esp_err_t err;

    nvs_handle_t nvs_handle;

    int32_t uid_count_temp = (int32_t)uid_count;

    // Open NVS handle
    err = nvs_open(STORAGE_NAMESPACE, NVS_READWRITE, &nvs_handle);
    if (err != ESP_OK) {
        ESP_LOGE(NVS_TAG, "Error opening NVS handle: %s\n", esp_err_to_name(err));
        return;
    }

    // Save the UID count
    err = nvs_set_i32(nvs_handle, "uid_count", uid_count_temp);
    if (err != ESP_OK) {
        ESP_LOGE(NVS_TAG, "Error saving UID count to NVS: %s\n", esp_err_to_name(err));
        return;
    }

    // Save each UID
    for (int i = 0; i < uid_count; i++) {
        char key[16];
        snprintf(key, sizeof(key), "uid_%d", i);
        err = nvs_set_str(nvs_handle, key, valid_uids[i]);
        
        if (err != ESP_OK) {
            ESP_LOGE(NVS_TAG, "Error saving UID to NVS: %s\n", esp_err_to_name(err));
            return;
        }
    }

    // Commit the write operation
    err = nvs_commit(nvs_handle);
    if (err != ESP_OK) {
        ESP_LOGE(NVS_TAG, "Error committing UIDs to NVS: %s\n", esp_err_to_name(err));
    }

    nvs_close(nvs_handle);

    ESP_LOGI(NVS_TAG, "UIDs saved to NVS successfully.");
}

// Function to load UIDs from NVS 
void load_uids_from_nvs() {
    esp_err_t err;

    nvs_handle_t nvs_handle;

    // Open NVS handle
    err = nvs_open(STORAGE_NAMESPACE, NVS_READWRITE, &nvs_handle);
    if (err != ESP_OK) {
        ESP_LOGE(NVS_TAG, "Error opening NVS handle: %s\n", esp_err_to_name(err));
        return;
    }
    
    int32_t uid_count_temp;

    // Load the UID count
    err = nvs_get_i32(nvs_handle, "uid_count", &uid_count_temp);
    if (err != ESP_OK) {
        ESP_LOGE(NVS_TAG, "Error loading UID count from NVS: %s\n", esp_err_to_name(err));
        return;
    }

    // Load each UID
    for (int i = 0; i < uid_count_temp; i++) {
        char key[16];
        snprintf(key, sizeof(key), "uid_%d", i);
        size_t required_size;
        err = nvs_get_str(nvs_handle, key, NULL, &required_size);
        if (err != ESP_OK) {
            ESP_LOGE(NVS_TAG, "Error getting size of UID from NVS: %s\n", esp_err_to_name(err));
            return;
        }
        err = nvs_get_str(nvs_handle, key, valid_uids[i], &required_size);
        if (err != ESP_OK) {
            ESP_LOGE(NVS_TAG, "Error loading UID from NVS: %s\n", esp_err_to_name(err));
            return;
        }
    }

    nvs_close(nvs_handle);

    uid_count = (int)uid_count_temp;

    ESP_LOGI(NVS_TAG, "UIDs loaded from NVS successfully.");
}