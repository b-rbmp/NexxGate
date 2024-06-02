#define MAX_UIDS 100  // Maximum number of UIDs we can store
#define ENCRYPTED_UID_LENGTH 256 // Assuming =Encrypted UIDs with a 256-byte ciphertext + null-terminator

void rsa_init(const char* public_key_pem);
void update_public_key(const char* new_public_key_pem);
int encrypt_uid(const char* uid, char* output);
int is_valid_uid(const char* uid);
void update_access_list(const char* encrypted_uids[], int count);

