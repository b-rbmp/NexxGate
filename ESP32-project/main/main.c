#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "esp_system.h"
#include "nvs_flash.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "esp_log.h"
#include "config.c"


// Function that authenticates the user
bool authenticate_NFC(char* uid) {
    if (uid != NULL) {
        // Check if the provided uid is in the list of valid uids
        for (int i = 0; i < num_valid_uids; i++) {
            printf("Comparing provided UID: %s with valid UID %d: %s\n", uid, i+1, valid_uids[i]);
            if (strcmp(uid, valid_uids[i]) == 0) {
                printf("UID is valid. Authentication successful.\n");
                return true;
            }
        }
        printf("UID is not recognized. Authentication failed.\n");
    } else {
        printf("UID is invalid. Authentication failed.\n");
    }
    return false;
}


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
}

void NFC_Reading_Task(void *arg) {

    // Prepare key - all keys are set to FFFFFFFFFFFFh at chip delivery from the factory.
    // MIFARE_Key key_a;
    // // MIFARE_Key key_b;
    // key_a.keyByte[0] = 0xFF; key_a.keyByte[1] = 0xFF; key_a.keyByte[2] = 0xFF; key_a.keyByte[3] = 0xFF; key_a.keyByte[4] = 0xFF; key_a.keyByte[5] = 0xFF;
    // // key_b.keyByte[0] = 0xFF; key_b.keyByte[1] = 0xFF; key_b.keyByte[2] = 0xFF; key_b.keyByte[3] = 0xFF; key_b.keyByte[4] = 0xFF; key_b.keyByte[5] = 0xFF;

    spi_device_handle_t spi; // Handle for the SPI device
    spi = init_spi();  // Initialize SPI for communication with RC522
    PCD_Init(spi); // Initialize the RC522 device
    while(1)
    {
        vTaskDelay(500 / portTICK_PERIOD_MS);
        // Check for New Card
        if(PICC_IsNewCardPresent(spi))                   
        {
            // Card is present
            printf("*****************CARD PRESENT*****************\r\n");

            // Turn on Green LED and turn on Red LED, so yellow processing
            off_leds();
            gpio_set_level(LED_YELLOW, 1);

            // Read Card Serial
            if (!PICC_ReadCardSerial(spi)) {
                printf("*****************ERROR READING CARD*****************\r\n");
                off_leds();
                continue;
            }
            // Get UID
            //PICC_DumpToSerial_Custom_Key(spi,&uid,key_a);

            // Get UID as string knowing it can have up to 10 bytes
            char uid_string[22];
            for (uint8_t i = 0; i < uid.size; i++) {
                sprintf(&uid_string[i*2], "%02X", uid.uidByte[i]);
            }
            printf("UID: %s\r\n", uid_string);

            // Authenticate
            bool authenticated = authenticate_NFC(uid_string);
            if (authenticated) {
                // Turn on Green LED
                off_leds();
                gpio_set_level(LED_BLUE, 1);
                printf("*****************CARD AUTHENTICATED*****************\r\n");
                vTaskDelay(2000 / portTICK_PERIOD_MS);
            } else {
                // Turn on Red LED
                off_leds();
                gpio_set_level(LED_RED, 1);
                printf("*****************CARD NOT AUTHENTICATED*****************\r\n");
                vTaskDelay(2000 / portTICK_PERIOD_MS);
            }
            off_leds();
            PICC_HaltA(spi);
            PCD_StopCrypto1(spi);
        } else {
            off_leds();
            vTaskDelay(100 / portTICK_PERIOD_MS);
            continue;
        }

    }
}

// Main application function
void app_main() {

    // // Initialize NVS (Non-Volatile Storage) for storing data
    // esp_err_t ret = nvs_flash_init();
    // // Check for errors related to storage initialization
    // if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
    //   nvs_flash_erase(); // Erase if there are no free pages or there's a new version
    //   nvs_flash_init();  // Re-initialize
    // }
    
    init_leds(); // Initialize LEDs for signaling

    xTaskCreate(NFC_Reading_Task, "NFC_Reading_Task", 2048, NULL, 1, NULL);
}
