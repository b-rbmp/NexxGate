#define MAX_UIDS 100  // Maximum number of UIDs we can store
#define UID_LENGTH 10 // Assuming UID length to be 10 characters

// Public key used for verifying the signature
#define PUBLIC_KEY_EDGE "-----BEGIN PUBLIC KEY-----\n" \
"MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0iag2Z7BkrUrZQh0ZglG\n" \
"nW5Uhq3JhTtfXDHLqCgAncGraGhQBEKEYADXQdC1iFtVh9Qe73VhDsdvNXYNytqi\n" \
"XdJNu2CKrJA5aGlDb/GjBjRyHLWXFqQhK+ptnyULwgB1YCHM8QG9hsFvGvsrjaTK\n" \
"h63K3J1E2+dD5eQG1lGZDkVQEeStOra80Jv+mW0G9N0ahcGrb8E/JvfAMQO65wQK\n" \
"PhlAhnW2wzsKwfY1LeCM5PUYZ9DYYqY8fR3YomK18MrumhJZKLCePzRDSd4SmHsC\n" \
"gSIML6xHT/YDsyUpUFdws807r4Q4sPEba/MqPEsRATN5O9HZb4BlgUBi8fi5xhQY\n" \
"GwIDAQAB\n" \
"-----END PUBLIC KEY-----\n"


int is_valid_uid(const char* uid);
void add_uid(const char* uid);
void remove_uid(const char* uid);
void update_access_list(const char* uids[], int count);
void save_uids_to_nvs();
void load_uids_from_nvs();
int verify_signature(const char* data, const char* signature);
