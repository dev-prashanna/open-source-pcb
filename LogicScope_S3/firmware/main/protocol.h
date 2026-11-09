#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define LS_VERSION "0.1.0"
#define LS_MAX_SAMPLES 65536u
#define LS_HEADER_SIZE 16u
#define LS_INFO 1u
#define LS_CAPTURE 2u
#define LS_ERROR 255u
#define LS_UNVALIDATED 1u

/* All wire integers are little endian; no packed-struct/ABI dependency. */
typedef struct {
    uint32_t rate, count;
    uint8_t trigger, mask, value;
} ls_request_t;

enum { LS_IMMEDIATE, LS_RISING, LS_FALLING, LS_HIGH, LS_LOW, LS_PATTERN };

uint32_t ls_get32(const uint8_t *p);
void ls_put32(uint8_t *p, uint32_t v);
uint32_t ls_crc32(uint32_t crc, const void *data, size_t len);
bool ls_parse_request(const uint8_t *payload, size_t len, ls_request_t *out);
int32_t ls_find_trigger(const uint8_t *samples, size_t count, const ls_request_t *r);
void ls_make_header(uint8_t *h, uint8_t type, uint16_t seq, uint32_t length);
