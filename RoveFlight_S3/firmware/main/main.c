#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "board_pins.h"
#include "motor_interlock.h"

void app_main(void)
{
    motor_interlock_init_disarmed();
    ESP_ERROR_CHECK(gpio_set_direction(PIN_STATUS_LED, GPIO_MODE_OUTPUT));
    ESP_LOGW("roveflight", "Bring-up only: motors held disarmed; sensor/control drivers not implemented");
    for (;;) {
        ESP_ERROR_CHECK(gpio_set_level(PIN_STATUS_LED, 1));
        vTaskDelay(pdMS_TO_TICKS(100));
        ESP_ERROR_CHECK(gpio_set_level(PIN_STATUS_LED, 0));
        vTaskDelay(pdMS_TO_TICKS(900));
    }
}
