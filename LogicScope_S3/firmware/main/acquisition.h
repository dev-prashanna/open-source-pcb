#pragma once
#include "esp_err.h"
#include "protocol.h"

esp_err_t acquisition_init(void);
/* Buffer is retained until the next acquisition, only read after success. */
esp_err_t acquisition_capture(const ls_request_t *request, const uint8_t **samples);
