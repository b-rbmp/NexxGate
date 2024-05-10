#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "security.h"

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
