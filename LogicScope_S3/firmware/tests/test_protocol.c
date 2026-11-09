#include "protocol.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    assert(ls_crc32(0, "123456789", 9) == 0xcbf43926u);
    uint32_t crc = ls_crc32(0, "1234", 4);
    assert(ls_crc32(crc, "56789", 5) == 0xcbf43926u);
    uint8_t payload[12] = {0};
    ls_put32(payload, 1000000); ls_put32(payload + 4, 65536);
    ls_request_t r;
    assert(ls_parse_request(payload, 12, &r));
    payload[11] = 1; assert(!ls_parse_request(payload, 12, &r)); payload[11] = 0;
    payload[8] = LS_RISING; payload[9] = 1;
    assert(ls_parse_request(payload, 12, &r));
    const uint8_t samples[] = {0, 0, 1, 1, 0};
    assert(ls_find_trigger(samples, 5, &r) == 2);
    r.trigger = LS_FALLING; assert(ls_find_trigger(samples, 5, &r) == 4);
    r.trigger = LS_LOW; assert(ls_find_trigger(samples, 5, &r) == 0);
    r.trigger = LS_PATTERN; r.mask = 3; r.value = 2;
    assert(ls_find_trigger(samples, 5, &r) == -1);
    payload[9] = 3; assert(!ls_parse_request(payload, 12, &r));
    uint8_t header[16]; ls_make_header(header, LS_CAPTURE, 0xabcd, 65552);
    assert(!memcmp(header, "LSA1", 4) && header[4] == 2 && header[5] == 0);
    assert(header[6] == 0xcd && header[7] == 0xab && ls_get32(header + 8) == 65552);
    puts("Firmware protocol tests passed");
    return 0;
}
