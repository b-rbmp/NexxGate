#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "security.h"
#include "config.h"
#include "nvs_flash.h"
#include "esp_log.h"
#include "mbedtls/pk.h"
#include "mbedtls/md.h"
#include "mbedtls/error.h"
#include "mbedtls/base64.h"

char valid_uids[MAX_UIDS][UID_LENGTH]; // Array to store UIDs
int head = 0; // Head index for the circular buffer
int tail = 0; // Tail index for the circular buffer
int uid_count = 0; // Current count of stored UIDs

/**
 * Adds a UID to the circular buffer.
 *
 * @param uid The UID to be added.
 */
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

/**
 * Removes a UID from the circular buffer if it is present.
 *
 * @param uid The UID to be removed.
 */
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
/**
 * Update the access list with a new list of encrypted UIDs by replacing the old list.
 * 
 * @param uids An array of encrypted UIDs.
 * @param count The number of UIDs in the array.
 */
void update_access_list(const char* uids[], int count) {
    head = 0;
    tail = 0;
    uid_count = count;
    for (int i = 0; i < count; i++) {
        strcpy(valid_uids[tail], uids[i]);
        tail = (tail + 1) % MAX_UIDS;
    }
}

/**
 * Checks if a UID is valid.
 *
 * @param uid The UID to check.
 * @return 1 if the UID is found in the valid UIDs list, 0 otherwise.
 */
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

/**
 * Saves the UIDs to the NVS (Non-Volatile Storage).
 */
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

/**
 * @brief Function to load UIDs from NVS
 * 
 * This function retrieves UIDs from the NVS (Non-Volatile Storage) and stores them in an array.
 * It opens the NVS handle, retrieves the UID count, and then loads each UID from the NVS.
 * The UIDs are stored in the `valid_uids` array.
 * 
 */
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

/**
 * Verifies the signature of the given data using a public key.
 *
 * @param data The data to be verified.
 * @param signature_base64 The base64 encoded signature to be verified.
 * @return 0 if the signature is valid, -1 otherwise.
 */
int verify_signature(const char *data, const char *signature_base64) {
    unsigned char signature[256];
    size_t sig_len;
    int ret;

    // Decode the base64 signature
    ret = mbedtls_base64_decode(signature, sizeof(signature), &sig_len, (const unsigned char *)signature_base64, strlen(signature_base64));
    if (ret != 0) {
        ESP_LOGE(SECURITY_TAG, "Failed to decode signature: -0x%04X\n", -ret);
        return -1;
    }

    // Initialize the public key context
    mbedtls_pk_context pk;
    mbedtls_pk_init(&pk);

    // Parse the public key
    ret = mbedtls_pk_parse_public_key(&pk, (unsigned char *)PUBLIC_KEY_EDGE, strlen(PUBLIC_KEY_EDGE) + 1);
    if (ret != 0) {
        ESP_LOGE(SECURITY_TAG, "Failed to parse public key: -0x%04X\n", -ret);
        mbedtls_pk_free(&pk);
        return -1;
    }

    // Compute the SHA-256 hash of the data
    unsigned char hash[32];
    ret = mbedtls_md(mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), (const unsigned char *)data, strlen(data), hash);
    if (ret != 0) {
        ESP_LOGE(SECURITY_TAG, "Failed to hash data: -0x%04X\n", -ret);
        mbedtls_pk_free(&pk);
        return -1;
    }

    // Verify the signature using PKCS#1 v1.5 padding
    ret = mbedtls_pk_verify(&pk, MBEDTLS_MD_SHA256, hash, sizeof(hash), signature, sig_len);
    if (ret != 0) {
        ESP_LOGW(SECURITY_TAG, "Signature verification failed: -0x%04X\n", -ret);
    } else {
        ESP_LOGI(SECURITY_TAG, "Signature verification succeeded\n");
    }

    mbedtls_pk_free(&pk);
    return ret == 0 ? 0 : -1;
}
