#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "mbedtls/pk.h"
#include "mbedtls/rsa.h"
#include "mbedtls/sha256.h"
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/entropy.h"
#include "mbedtls/error.h"
#include "mbedtls/base64.h"
#include "security.h"

#define MAX_UIDS 100
#define ENCRYPTED_UID_LENGTH 256 // Adjust as necessary

char valid_encrypted_uids[MAX_UIDS][ENCRYPTED_UID_LENGTH * 2 + 1]; // Hex string requires twice the space plus null terminator
int head = 0; // Head index for the circular buffer
int tail = 0; // Tail index for the circular buffer
int uid_count = 0; // Current count of stored UIDs

mbedtls_pk_context pk_edge;
mbedtls_ctr_drbg_context ctr_drbg;
mbedtls_entropy_context entropy;

// Function to convert a hex string to a binary string
unsigned char* hex_to_bin(const char* hex_str, size_t* bin_len) {
    size_t len = strlen(hex_str);
    *bin_len = len / 2;
    unsigned char* bin_data = (unsigned char*)malloc(*bin_len);

    for (size_t i = 0; i < len; i += 2) {
        sscanf(hex_str + i, "%2hhx", &bin_data[i / 2]);
    }

    return bin_data;
}

// Function to convert a binary string to a hex string
void bin_to_hex(const unsigned char *bin, size_t bin_len, char *hex) {
    for (size_t i = 0; i < bin_len; i++) {
        sprintf(hex + (i * 2), "%02x", bin[i]);
    }
    hex[bin_len * 2] = '\0';
}

// Function to convert a base64 string to binary
int base64_to_bin(const char *base64, unsigned char *bin, size_t *bin_len) {
    return mbedtls_base64_decode(bin, *bin_len, bin_len, (unsigned char *)base64, strlen(base64));
}

// Function to convert a binary string to a base64 string
void bin_to_base64(const unsigned char *bin, size_t bin_len, char *base64) {
    size_t base64_len;
    mbedtls_base64_encode((unsigned char *)base64, ENCRYPTED_UID_LENGTH * 2, &base64_len, bin, bin_len);
    base64[base64_len] = '\0';
}

// Function to initialize the RSA context
void rsa_init(const char* public_key_hex) {
    unsigned char* public_key_pem;
    size_t pem_len;
    public_key_pem = hex_to_bin(public_key_hex, &pem_len);

    // Add null terminator to the PEM buffer
    public_key_pem = (unsigned char *)realloc(public_key_pem, pem_len + 1);
    public_key_pem[pem_len] = '\0';

    // Print the public key in PEM format
    printf("Public key in PEM:\n%s\n", public_key_pem);

    mbedtls_pk_init(&pk_edge);
    mbedtls_ctr_drbg_init(&ctr_drbg);
    mbedtls_entropy_init(&entropy);

    const char *pers = "rsa_encrypt";
    int ret = mbedtls_ctr_drbg_seed(&ctr_drbg, mbedtls_entropy_func, &entropy, (const unsigned char *)pers, strlen(pers));
    if (ret != 0) {
        char error_buf[100];
        mbedtls_strerror(ret, error_buf, sizeof(error_buf));
        printf("Failed to initialize entropy and CTR_DRBG: %s\n", error_buf);
        free(public_key_pem);
        return;
    }

    ret = mbedtls_pk_parse_public_key(&pk_edge, public_key_pem, pem_len + 1);
    if (ret != 0) {
        char error_buf[100];
        mbedtls_strerror(ret, error_buf, sizeof(error_buf));
        printf("Failed to parse public key: %s\n", error_buf);
        free(public_key_pem);
        return;
    }

    // Verify that the key is an RSA key
    if (!mbedtls_pk_can_do(&pk_edge, MBEDTLS_PK_RSA)) {
        printf("The parsed key is not an RSA key\n");
        mbedtls_pk_free(&pk_edge);
        free(public_key_pem);
        return;
    }

    // Print the public key to verify it
    char public_key_buf[500];
    ret = mbedtls_pk_write_pubkey_pem(&pk_edge, (unsigned char *)public_key_buf, sizeof(public_key_buf));
    if (ret != 0) {
        char error_buf[100];
        mbedtls_strerror(ret, error_buf, sizeof(error_buf));
        printf("Failed to write public key PEM: %s\n", error_buf);
        mbedtls_pk_free(&pk_edge);
        free(public_key_pem);
        return;
    }

    printf("Public key:\n%s\n", public_key_buf);

    free(public_key_pem);
}

// Function to update the public key and reinitialize the RSA context
void update_public_key(const char* new_public_key_pem) {
    rsa_init(new_public_key_pem);
}

// Function to check if an encrypted UID matches any in the list
int is_valid_uid(const char* encrypted_uid) {
    int index = head;
    for (int i = 0; i < uid_count; i++) {
        if (strcmp(valid_encrypted_uids[index], encrypted_uid) == 0) {
            return 1; // Encrypted UID found
        }
        index = (index + 1) % MAX_UIDS;
    }
    return 0; // Encrypted UID not found
}

// Update the access list with a new list of encrypted UIDs by replacing the old list
void update_access_list(const char* encrypted_uids[], int count) {
    head = 0;
    tail = 0;
    uid_count = count;
    for (int i = 0; i < count; i++) {
        strcpy(valid_encrypted_uids[tail], encrypted_uids[i]);
        tail = (tail + 1) % MAX_UIDS;
    }
}

// Function to encrypt a UID using the public key and return base64 string
int encrypt_uid(const char* uid, char* output) {
    unsigned char hash[32];
    unsigned char encrypted[256];
    size_t olen = 0;
    int ret;

    // Check if the RSA context is properly initialized
    if (!mbedtls_pk_can_do(&pk_edge, MBEDTLS_PK_RSA)) {
        printf("RSA context is not properly initialized.\n");
        return -1;
    }

    // Hash the UID using SHA-256
    ret = mbedtls_sha256((const unsigned char *)uid, strlen(uid), hash, 0);
    if (ret != 0) {
        char error_buf[100];
        mbedtls_strerror(ret, error_buf, sizeof(error_buf));
        printf("Failed to hash UID: %s\n", error_buf);
        return -1;
    }

    // Encrypt the hash using the public key with OAEP padding
    mbedtls_rsa_context *rsa = mbedtls_pk_rsa(pk_edge);
    mbedtls_rsa_set_padding(rsa, MBEDTLS_RSA_PKCS_V21, MBEDTLS_MD_SHA256);
    ret = mbedtls_rsa_rsaes_oaep_encrypt(rsa, mbedtls_ctr_drbg_random, &ctr_drbg, NULL, 0, sizeof(hash), hash, encrypted);
    if (ret != 0) {
        char error_buf[100];
        mbedtls_strerror(ret, error_buf, sizeof(error_buf));
        printf("Failed to encrypt UID: %s\n", error_buf);
        return -1;
    }

    // Convert the encrypted data to base64
    bin_to_base64(encrypted, mbedtls_pk_rsa(pk_edge)->private_len, output);

    return 0;
}