/* LS-S3-A0 only; ESP-IDF v5.5.2. Internal LCD_CAM/GDMA APIs are version pinned. */
#include "acquisition.h"
#include <string.h>
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "esp_check.h"
#include "esp_heap_caps.h"
#include "esp_idf_version.h"
#include "esp_private/gdma.h"
#include "esp_private/periph_ctrl.h"
#include "esp_rom_gpio.h"
#include "esp_rom_sys.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "hal/dma_types.h"
#include "soc/gpio_sig_map.h"
#include "soc/lcd_cam_struct.h"

#if !CONFIG_IDF_TARGET_ESP32S3
#error "LogicScope S3 requires ESP32-S3"
#endif
#if ESP_IDF_VERSION != ESP_IDF_VERSION_VAL(5, 5, 2)
#error "Use ESP-IDF v5.5.2; review private peripheral APIs before changing SDK"
#endif

#define OE 13
#define LED 14
#define DE 9
#define VSYNC 10
#define PCLK 11
#define CLOCK_OUT 12
#define NODE_BYTES 4092u
#define NODES ((LS_MAX_SAMPLES + NODE_BYTES - 1) / NODE_BYTES)
#define GUARD_BYTES 16u

static const char *TAG = "acquisition";
static const int data_pins[8] = {4, 5, 6, 7, 15, 16, 17, 18};
static gdma_channel_handle_t dma;
static dma_descriptor_t *descriptors;
static uint8_t *buffer;
static SemaphoreHandle_t done;
static volatile bool dma_error;
static volatile intptr_t eof_descriptor;

/* This callback runs before the next task can touch the completed buffer.
 * There is no descriptor ring: DMA cannot overwrite the capture. */
static bool IRAM_ATTR on_eof(gdma_channel_handle_t chan, gdma_event_data_t *e, void *ctx)
{
    (void)chan; (void)ctx;
    LCD_CAM.cam_ctrl1.cam_start = 0;
    LCD_CAM.cam_ctrl.cam_update = 1;
    eof_descriptor = e->rx_eof_desc_addr;
    dma_error |= e->flags.abnormal_eof;
    BaseType_t wake = pdFALSE;
    xSemaphoreGiveFromISR(done, &wake);
    return wake == pdTRUE;
}

static bool IRAM_ATTR on_error(gdma_channel_handle_t chan, gdma_event_data_t *e, void *ctx)
{
    dma_error = true;
    return on_eof(chan, e, ctx);
}

static void safe_stop(void)
{
    gpio_set_level(DE, 0);
    LCD_CAM.cam_ctrl1.cam_start = 0;
    LCD_CAM.cam_ctrl.cam_update = 1;
    ledc_stop(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 0);
    gdma_stop(dma);
    gpio_set_level(OE, 1);
    gpio_set_level(LED, 0);
}

esp_err_t acquisition_init(void)
{
    /* Set the output latch before enabling OE's output driver. */
    gpio_set_level(OE, 1);
    gpio_config_t outputs = {
        .pin_bit_mask = (1ULL << OE) | (1ULL << LED), .mode = GPIO_MODE_OUTPUT,
    };
    ESP_RETURN_ON_ERROR(gpio_config(&outputs), TAG, "control GPIOs");
    gpio_set_level(LED, 0);
    gpio_config_t gates = {
        .pin_bit_mask = (1ULL << DE) | (1ULL << VSYNC), .mode = GPIO_MODE_INPUT_OUTPUT,
    };
    ESP_RETURN_ON_ERROR(gpio_config(&gates), TAG, "gate GPIOs");
    gpio_set_level(DE, 0); gpio_set_level(VSYNC, 0);
    for (int i = 0; i < 8; ++i) {
        ESP_RETURN_ON_ERROR(gpio_reset_pin(data_pins[i]), TAG, "reset input");
        ESP_RETURN_ON_ERROR(gpio_set_direction(data_pins[i], GPIO_MODE_INPUT), TAG, "input");
        ESP_RETURN_ON_ERROR(gpio_set_pull_mode(data_pins[i], GPIO_FLOATING), TAG, "input pull");
        esp_rom_gpio_connect_in_signal(data_pins[i], CAM_DATA_IN0_IDX + i, false);
    }
    ESP_RETURN_ON_ERROR(gpio_set_direction(PCLK, GPIO_MODE_INPUT), TAG, "PCLK input");
    esp_rom_gpio_connect_in_signal(PCLK, CAM_PCLK_IDX, false);
    esp_rom_gpio_connect_in_signal(DE, CAM_H_ENABLE_IDX, false);
    esp_rom_gpio_connect_in_signal(VSYNC, CAM_V_SYNC_IDX, false);

    ledc_timer_config_t timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE, .duty_resolution = LEDC_TIMER_1_BIT,
        .timer_num = LEDC_TIMER_0, .freq_hz = 100000, .clk_cfg = LEDC_USE_XTAL_CLK,
    };
    ESP_RETURN_ON_ERROR(ledc_timer_config(&timer), TAG, "clock timer");
    ledc_channel_config_t clock = {
        .gpio_num = CLOCK_OUT, .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_0, .timer_sel = LEDC_TIMER_0, .duty = 0,
    };
    ESP_RETURN_ON_ERROR(ledc_channel_config(&clock), TAG, "clock output");
    periph_module_enable(PERIPH_LCD_CAM_MODULE);
    LCD_CAM.cam_ctrl.val = 0;
    LCD_CAM.cam_ctrl.cam_clk_sel = 3; /* PLL160M */
    LCD_CAM.cam_ctrl.cam_clkm_div_num = 4; /* module 40 MHz >= 2 x PCLK */
    LCD_CAM.cam_ctrl.cam_stop_en = 1; /* stop on DMA FIFO full */
    LCD_CAM.cam_ctrl1.val = 0; /* 8-bit, DE/VSYNC, positive PCLK, no swapping */
    LCD_CAM.cam_rgb_yuv.val = 0; /* bypass conversion */
    LCD_CAM.lc_dma_int_ena.val = 0;
    LCD_CAM.lc_dma_int_clr.val = ~0u;

    gdma_channel_alloc_config_t alloc = {.direction = GDMA_CHANNEL_DIRECTION_RX};
    ESP_RETURN_ON_ERROR(gdma_new_ahb_channel(&alloc, &dma), TAG, "GDMA channel");
    ESP_RETURN_ON_ERROR(gdma_connect(dma, GDMA_MAKE_TRIGGER(GDMA_TRIG_PERIPH_CAM, 0)), TAG, "GDMA CAM");
    gdma_strategy_config_t strategy = {.owner_check = true, .auto_update_desc = false};
    ESP_RETURN_ON_ERROR(gdma_apply_strategy(dma, &strategy), TAG, "GDMA ownership");
    gdma_transfer_config_t transfer = {.max_data_burst_size = 4, .access_ext_mem = false};
    ESP_RETURN_ON_ERROR(gdma_config_transfer(dma, &transfer), TAG, "GDMA transfer");
    done = xSemaphoreCreateBinary();
    descriptors = heap_caps_calloc(NODES, sizeof(*descriptors), MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
    /* Two guards surrounding the full allocation; per-capture tail is set below. */
    buffer = heap_caps_aligned_alloc(16, LS_MAX_SAMPLES + 2 * GUARD_BYTES,
                                    MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
    if (!done || !descriptors || !buffer) return ESP_ERR_NO_MEM;
    gdma_rx_event_callbacks_t callbacks = {.on_recv_eof = on_eof, .on_descr_err = on_error};
    ESP_RETURN_ON_ERROR(gdma_register_rx_event_callbacks(dma, &callbacks, NULL), TAG, "GDMA ISR");
    return ESP_OK;
}

esp_err_t acquisition_capture(const ls_request_t *r, const uint8_t **samples)
{
    *samples = NULL;
    uint8_t *data = buffer + GUARD_BYTES;
    memset(buffer, 0xa5, GUARD_BYTES);
    memset(data + r->count, 0xa5, GUARD_BYTES);
    memset(descriptors, 0, NODES * sizeof(*descriptors));
    size_t remaining = r->count, offset = 0, nodes = 0;
    while (remaining) {
        size_t length = remaining > NODE_BYTES ? NODE_BYTES : remaining;
        dma_descriptor_t *d = &descriptors[nodes++];
        d->dw0.size = length; d->dw0.owner = DMA_DESCRIPTOR_BUFFER_OWNER_DMA;
        d->buffer = data + offset;
        remaining -= length; offset += length;
        d->next = remaining ? &descriptors[nodes] : NULL;
    }
    while (xSemaphoreTake(done, 0) == pdTRUE) {}
    dma_error = false; eof_descriptor = 0;
    esp_err_t err = ledc_set_freq(LEDC_LOW_SPEED_MODE, LEDC_TIMER_0, r->rate);
    if (err != ESP_OK) return err;
    if (ledc_get_freq(LEDC_LOW_SPEED_MODE, LEDC_TIMER_0) != r->rate) return ESP_ERR_INVALID_STATE;
    err = gdma_reset(dma);
    if (err != ESP_OK) { safe_stop(); return err; }
    LCD_CAM.cam_ctrl1.cam_reset = 1;
    LCD_CAM.cam_ctrl1.cam_reset = 0;
    LCD_CAM.cam_ctrl1.cam_afifo_reset = 1;
    LCD_CAM.cam_ctrl1.cam_afifo_reset = 0;
    LCD_CAM.cam_ctrl1.cam_rec_data_bytelen = r->count - 1;
    LCD_CAM.cam_ctrl.cam_vs_eof_en = 0; /* exact byte-count EOF, never VSYNC EOF */
    err = gdma_start(dma, (intptr_t)descriptors);
    if (err != ESP_OK) { safe_stop(); return err; }
    gpio_set_level(OE, 0); gpio_set_level(LED, 1);
    esp_rom_delay_us(2); /* input buffer settling */
    LCD_CAM.cam_ctrl.cam_update = 1;
    LCD_CAM.cam_ctrl1.cam_start = 1;
    err = ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 1);
    if (err == ESP_OK) err = ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
    if (err != ESP_OK) { safe_stop(); return err; }
    /* Establish a frame boundary with DE disabled; PCLK runs for synchronization. */
    gpio_set_level(VSYNC, 1); esp_rom_delay_us(50);
    gpio_set_level(VSYNC, 0); esp_rom_delay_us(50);
    gpio_set_level(DE, 1);
    uint32_t timeout_ms = (r->count * 1000u + r->rate - 1) / r->rate + 250u;
    bool completed = xSemaphoreTake(done, pdMS_TO_TICKS(timeout_ms)) == pdTRUE;
    safe_stop();
    /* Stop/reset quiesces the DMA channel before inspecting descriptors/guards. */
    err = gdma_reset(dma);
    if (err != ESP_OK) return err;
    if (!completed) return ESP_ERR_TIMEOUT;
    if (dma_error || eof_descriptor != (intptr_t)&descriptors[nodes - 1]) return ESP_FAIL;
    size_t total = 0;
    for (size_t i = 0; i < nodes; ++i) {
        if (descriptors[i].dw0.owner || descriptors[i].dw0.err_eof ||
            descriptors[i].dw0.length != descriptors[i].dw0.size) return ESP_FAIL;
        total += descriptors[i].dw0.length;
    }
    if (total != r->count || !descriptors[nodes - 1].dw0.suc_eof) return ESP_FAIL;
    for (size_t i = 0; i < GUARD_BYTES; ++i)
        if (buffer[i] != 0xa5 || data[r->count + i] != 0xa5) return ESP_FAIL;
    *samples = data;
    return ESP_OK;
}
