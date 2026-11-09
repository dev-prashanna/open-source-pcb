#include "protocol.h"
#include <string.h>

uint32_t ls_get32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

void ls_put32(uint8_t *p, uint32_t v)
{
    for (int i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (8 * i));
}

/* Standard reflected CRC-32, compatible with Python zlib.crc32, incremental. */
uint32_t ls_crc32(uint32_t crc, const void *data, size_t len)
{
    const uint8_t *p = data;
    crc = ~crc;
    while (len--) {
        crc ^= *p++;
        for (int bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}

bool ls_parse_request(const uint8_t *p, size_t len, ls_request_t *r)
{
    if (len != 12 || p[11]) return false;
    r->rate = ls_get32(p);
    r->count = ls_get32(p + 4);
    r->trigger = p[8]; r->mask = p[9]; r->value = p[10];
    if (r->rate != 100000 && r->rate != 250000 &&
        r->rate != 500000 && r->rate != 1000000) return false;
    if (r->count < 16 || r->count > LS_MAX_SAMPLES || r->count % 4) return false;
    if (r->trigger > LS_PATTERN) return false;
    if (r->trigger && !r->mask) return false;
    /* Edge and level searches address exactly one channel. */
    if (r->trigger && r->trigger != LS_PATTERN && (r->mask & (r->mask - 1))) return false;
    return (r->value & ~r->mask) == 0;
}

int32_t ls_find_trigger(const uint8_t *s, size_t count, const ls_request_t *r)
{
    if (r->trigger == LS_IMMEDIATE) return -1;
    for (size_t i = 0; i < count; ++i) {
        uint8_t now = s[i] & r->mask;
        bool found = false;
        switch (r->trigger) {
        case LS_RISING: found = i && !(s[i - 1] & r->mask) && now; break;
        case LS_FALLING: found = i && (s[i - 1] & r->mask) && !now; break;
        case LS_HIGH: found = now != 0; break;
        case LS_LOW: found = now == 0; break;
        case LS_PATTERN: found = now == r->value; break;
        default: break;
        }
        if (found) return (int32_t)i;
    }
    return -1;
}

void ls_make_header(uint8_t *h, uint8_t type, uint16_t seq, uint32_t length)
{
    memset(h, 0, LS_HEADER_SIZE);
    memcpy(h, "LSA1", 4);
    h[4] = type;
    h[6] = seq & 255; h[7] = seq >> 8;
    ls_put32(h + 8, length);
}
