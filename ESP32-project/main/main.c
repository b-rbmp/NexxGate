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
#define LED_YELLOW GPIO_NUM_45   // Line for Yellow
#define LED_BLUE GPIO_NUM_42  // Line for Blue
#define LED_RED GPIO_NUM_46  // Line for Red

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
        .clock_speed_hz=5000000, // Clock speed of 1 MHz
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
    spi_device_handle_t spi; // Handle for the SPI device
    spi = init_spi();  // Initialize SPI for communication with RC522
    PCD_Init(spi); // Initialize the RC522 device
    while(1)
    {
        // Check for New Card
        if(PICC_IsNewCardPresent(spi))                   
        {
            // Card is present
            printf("*****************CARD PRESENT*****************\r\n");

            // Turn on Green LED and turn on Red LED, so yellow processing
            off_leds();
            gpio_set_level(LED_YELLOW, 1);

            // Read Card Serial
            PICC_ReadCardSerial(spi);
            // Get UID	      
            PICC_DumpToSerial(spi,&uid);       

            // Authenticate
            bool authenticated = true;
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
        } else {
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