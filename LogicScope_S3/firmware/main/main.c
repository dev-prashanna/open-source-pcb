#include <string.h>
#include "acquisition.h"
#include "driver/usb_serial_jtag.h"
#include "esp_log.h"
#include "esp_timer.h"

static bool read_exact(uint8_t *dst, size_t length, int timeout_ms)
{
    int64_t end = esp_timer_get_time() + timeout_ms * 1000LL;
    while (length && esp_timer_get_time() < end) {
        int n = usb_serial_jtag_read_bytes(dst, length, pdMS_TO_TICKS(20));
        if (n > 0) { dst += n; length -= n; }
    }
    return length == 0;
}

static bool write_all(const void *data, size_t length)
{
    const uint8_t *p = data;
    int64_t end = esp_timer_get_time() + 5000000LL;
    while (length && esp_timer_get_time() < end) {
        size_t block = length > 1024 ? 1024 : length;
        int n = usb_serial_jtag_write_bytes(p, block, pdMS_TO_TICKS(100));
        if (n > 0) { p += n; length -= n; }
    }
    return length == 0;
}

static void send_frame(uint8_t type, uint16_t seq, const void *meta, size_t mlen,
                       const void *data, size_t dlen)
{
    uint8_t h[LS_HEADER_SIZE];
    ls_make_header(h, type, seq, mlen + dlen);
    uint32_t crc = ls_crc32(0, h, 12);
    crc = ls_crc32(crc, meta, mlen);
    crc = ls_crc32(crc, data, dlen);
    ls_put32(h + 12, crc);
    if (!write_all(h, sizeof(h)) || !write_all(meta, mlen)) return;
    write_all(data, dlen);
}

static void send_error(uint16_t seq, const char *message)
{
    send_frame(LS_ERROR, seq, message, strlen(message), NULL, 0);
}

void app_main(void)
{
    /* Logs/boot console use UART43/44. Never mix logs with USB binary frames. */
    esp_err_t acquisition_status = acquisition_init();
    usb_serial_jtag_driver_config_t usb = {.tx_buffer_size = 4096, .rx_buffer_size = 1024};
    ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb));
    ESP_LOGI("LogicScope", "v%s acquisition: %s", LS_VERSION, esp_err_to_name(acquisition_status));
    for (;;) {
        uint8_t h[LS_HEADER_SIZE], payload[12];
        /* Rolling magic scanner also recovers after garbage/partial host writes. */
        size_t matched = 0;
        while (matched < 4) {
            uint8_t ch;
            if (!read_exact(&ch, 1, 1000)) continue;
            if (ch == (uint8_t)"LSA1"[matched]) h[matched++] = ch;
            else { matched = ch == 'L' ? 1 : 0; if (matched) h[0] = ch; }
        }
        if (!read_exact(h + 4, 12, 500)) continue;
        uint16_t seq = h[6] | ((uint16_t)h[7] << 8);
        uint32_t length = ls_get32(h + 8);
        if (length > sizeof(payload)) { send_error(seq, "E_LENGTH: request too large"); continue; }
        if (!read_exact(payload, length, 500)) { send_error(seq, "E_TIMEOUT: incomplete request"); continue; }
        uint32_t crc = ls_crc32(0, h, 12);
        crc = ls_crc32(crc, payload, length);
        if (crc != ls_get32(h + 12)) { send_error(seq, "E_CRC: invalid request checksum"); continue; }
        if (h[5]) { send_error(seq, "E_FLAGS: reserved flags must be zero"); continue; }
        if (h[4] == LS_INFO && length == 0) {
            const char *info = "{\"device\":\"LogicScope S3\",\"board\":\"LS-S3-A0\","
                "\"firmware\":\"" LS_VERSION "\",\"protocol\":1,\"channels\":8,"
                "\"rates\":[100000,250000,500000,1000000],\"max_samples\":65536,"
                "\"alignment\":4,\"hardware_validated\":false,\"trigger_mode\":\"search_in_capture\"}";
            send_frame(LS_INFO | 0x80, seq, info, strlen(info), NULL, 0);
        } else if (h[4] == LS_CAPTURE) {
            ls_request_t request;
            if (!ls_parse_request(payload, length, &request)) {
                send_error(seq, "E_CONFIG: invalid rate, count or trigger"); continue;
            }
            if (acquisition_status != ESP_OK) {
                send_error(seq, "E_INIT: acquisition unavailable; inspect debug UART"); continue;
            }
            const uint8_t *samples;
            esp_err_t err = acquisition_capture(&request, &samples);
            if (err != ESP_OK) {
                send_error(seq, err == ESP_ERR_TIMEOUT ? "E_CAPTURE_TIMEOUT: clock/gating/FIFO fault" :
                           "E_CAPTURE: DMA, sample count or guard validation failed");
                continue;
            }
            uint8_t meta[16];
            ls_put32(meta, request.rate); ls_put32(meta + 4, request.count);
            ls_put32(meta + 8, (uint32_t)ls_find_trigger(samples, request.count, &request));
            ls_put32(meta + 12, LS_UNVALIDATED);
            send_frame(LS_CAPTURE | 0x80, seq, meta, sizeof(meta), samples, request.count);
        } else send_error(seq, "E_COMMAND: unsupported command or payload");
    }
}
