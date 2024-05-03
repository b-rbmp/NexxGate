#include "config.h"
#include "MFRC522.c"


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
        .clock_speed_hz=1000000, // Clock speed of 1 MHz
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