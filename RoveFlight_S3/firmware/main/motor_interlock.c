#include "driver/gpio.h"
#include "esp_err.h"
#include "board_pins.h"
#include "motor_interlock.h"

void motor_interlock_kill(void)
{
    ESP_ERROR_CHECK(gpio_set_level(PIN_KILL_OD, 0));
    ESP_ERROR_CHECK(gpio_set_level(PIN_ARM_CLK, 0));
    ESP_ERROR_CHECK(gpio_set_level(PIN_PWM_M1, 0));
    ESP_ERROR_CHECK(gpio_set_level(PIN_PWM_M2, 0));
    ESP_ERROR_CHECK(gpio_set_level(PIN_PWM_M3, 0));
    ESP_ERROR_CHECK(gpio_set_level(PIN_PWM_M4, 0));
}

void motor_interlock_init_disarmed(void)
{
    /* Assert the hardware latch clear before configuring any other outputs. */
    ESP_ERROR_CHECK(gpio_set_level(PIN_KILL_OD, 0));
    const gpio_config_t kill = {
        .pin_bit_mask = 1ULL << PIN_KILL_OD,
        .mode = GPIO_MODE_OUTPUT_OD,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&kill));
    const int pins[] = {PIN_ARM_CLK, PIN_WD_HEARTBEAT, PIN_PWM_M1,
                       PIN_PWM_M2, PIN_PWM_M3, PIN_PWM_M4};
    for (unsigned i = 0; i < sizeof(pins) / sizeof(pins[0]); ++i) {
        ESP_ERROR_CHECK(gpio_set_level(pins[i], 0));
        ESP_ERROR_CHECK(gpio_set_direction(pins[i], GPIO_MODE_OUTPUT));
    }
    motor_interlock_kill();
    /* No heartbeat: an unimplemented control loop must not look healthy. */
}
