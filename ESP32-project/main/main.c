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
#include "MFRC522.c"

// Define GPIO pins for LED indicators
#define LED_RED GPIO_NUM_46   // Line for Red
#define LED_GREEN GPIO_NUM_45  // Line for Green
gpio_set_level(LED_GREEN, 0); // Turn off Green LED
gpio_set_level(LED_RED, 0);   // Turn off Red LED

// Function to display red LED
void red_led() {
    gpio_set_level(LED_GREEN, 0);
    gpio_set_level(LED_RED, 1);
}

// Function to display green LED
void green_led() {
    gpio_set_level(LED_GREEN, 1);
    gpio_set_level(LED_RED, 0);
}

// Function to display yellow LED
void yellow_led() {
    gpio_set_level(LED_GREEN, 1);
    gpio_set_level(LED_RED, 1);
}

// Function to initialize SPI bus and device for communication with RC522
spi_device_handle_t init_spi() {
    esp_err_t ret; // Variable to store return values
    // Configuration for the SPI bus
    spi_bus_config_t buscfg = {
        .miso_io_num = PIN_NUM_MISO,
        .mosi_io_num = PIN_NUM_MOSI,
        .sclk_io_num = PIN_NUM_CLK,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 32,
    };

    spi_device_handle_t spi; // Handle for the SPI device
    // Configuration for the SPI device, specifically for RC522
    spi_device_interface_config_t devcfg = {
        .clock_speed_hz=5000000, // Clock speed of 5 MHz
        .mode = 0,                     // SPI mode 0
        .spics_io_num = PIN_NUM_CS,    // Chip Select pin
        .queue_size = 7,               // Queue up to 7 transactions
    };

    // Initialize the SPI bus
    ret = spi_bus_initialize(SPI2_HOST, &buscfg, SPI_DMA_CH_AUTO);
    assert(ret==ESP_OK);
    // Add the SPI device (RC522) to the bus
    ret = spi_bus_add_device(SPI2_HOST, &devcfg, &spi);
    assert(ret==ESP_OK);

    return spi;
}

// Function to set up GPIO pins for LEDs as output
void init_leds() {
    gpio_set_direction(LED_GREEN, GPIO_MODE_OUTPUT);
    gpio_set_direction(LED_RED, GPIO_MODE_OUTPUT);
}

void NFC_Reading_Task(void *arg) {
    spi_device_handle_t spi = *(spi_device_handle_t*) arg;
    while(1)
    {
        yellow_led(); // Indicate processing
        vTaskDelay(500 / portTICK_PERIOD_MS); // Short delay for visual effect

        // Check for New Card
        if(PICC_IsNewCardPresent(spi))                   
        {
            // Card is present
            printf("*****************CARD PRESENT*****************\r\n");

            // Read Card Serial
            PICC_ReadCardSerial(spi);
            // Get UID	      
            PICC_DumpToSerial(spi,&uid);       

            vTaskDelay(1000 / portTICK_PERIOD_MS);

        } else {
            continue;
        }

    }
}

// Main application function
void app_main() {
    spi_device_handle_t spi; // Handle for the SPI device

    // Initialize NVS (Non-Volatile Storage) for storing data
    esp_err_t ret = nvs_flash_init();
    // Check for errors related to storage initialization
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
      nvs_flash_erase(); // Erase if there are no free pages or there's a new version
      nvs_flash_init();  // Re-initialize
    }

    spi = init_spi();  // Initialize SPI for communication with RC522
    init_leds(); // Initialize LEDs for signaling

    PCD_Init(spi); // Initialize the RC522 device

    xTaskCreate(NFC_Reading_Task, "NFC_Reading_Task", 2048, &spi, 1, NULL);
    
}
