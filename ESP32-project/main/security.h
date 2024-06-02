#define MAX_UIDS 100  // Maximum number of UIDs we can store
#define UID_LENGTH 10 // Assuming UID length to be 10 characters

int is_valid_uid(const char* uid);
void add_uid(const char* uid);
void update_access_list(const char* uids[], int count);
void save_uids_to_nvs();
void load_uids_from_nvs();