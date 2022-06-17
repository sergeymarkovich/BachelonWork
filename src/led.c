#include "led.h"
#include "stm32f10x.h"
#include "platform_config.h"

// Глобальные переменные
//uint8_t led_state[LEDS_NUM];
//
//uint16_t led_blink_on[LEDS_NUM];
//uint16_t led_blink_off[LEDS_NUM];
//
//uint16_t led_ticks_on[LEDS_NUM];
//uint16_t led_ticks_off[LEDS_NUM];

// Стркутура, хранящая все необходимое для работы с LED
//typedef struct _led_params
//{
//	GPIO_TypeDef* GPIOx;
//	uint16_t Pin;
//	uint32_t RCC_APB2Periph;
//} led_params;
//
//// Набор параметров для разных LED
//led_params ledx[] =
//	{
//	#ifdef LED1
//		 {LED1_GPIO_PORT, LED1_GPIO_PIN, LED1_GPIO_CLK}
//	#ifdef LED2
//		,{LED2_GPIO_PORT, LED2_GPIO_PIN, LED2_GPIO_CLK}
//	#ifdef LED3
//		,{LED3_GPIO_PORT, LED3_GPIO_PIN, LED3_GPIO_CLK}
//	#ifdef LED4
//		,{LED4_GPIO_PORT, LED4_GPIO_PIN, LED4_GPIO_CLK}
//	#ifdef LED5
//		,{LED5_GPIO_PORT, LED5_GPIO_PIN, LED5_GPIO_CLK}
//	#ifdef LED6
//		,{LED6_GPIO_PORT, LED6_GPIO_PIN, LED6_GPIO_CLK}
//	#ifdef LED7
//		,{LED7_GPIO_PORT, LED7_GPIO_PIN, LED7_GPIO_CLK}
//	#ifdef LED8
//		,{LED8_GPIO_PORT, LED8_GPIO_PIN, LED8_GPIO_CLK}
//	#endif // LED8
//	#endif // LED7
//	#endif // LED6
//	#endif // LED5
//	#endif // LED4
//	#endif // LED3
//	#endif // LED2
//	#endif // LED1
//	};
//
//
//// Инициализация всех светодиодов. Вызов из hw_config.c
//void Led_Init()
//{
//	GPIO_InitTypeDef GPIO_InitStructure;
//
//	int i;
//	for(i = 0; i < LEDS_NUM; i++)
//	{
//		led_state[i] = LEDSTATE_OFF;
//		led_blink_on[i] = 0;
//		led_blink_off[i] = 0;
//		led_ticks_on[i] = 0;
//		led_ticks_off[i] = 0;
//
//	  	RCC_APB2PeriphClockCmd(ledx[i].RCC_APB2Periph, ENABLE);
//	  	GPIO_InitStructure.GPIO_Pin = ledx[i].Pin;
//  		GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
//  		GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
//	  	GPIO_Init(ledx[i].GPIOx, &GPIO_InitStructure);
//	}
//
//}
//
//// Получить состояние светодиода
//uint8_t LED_GetState(int led)
//{
//	if(led >= LEDS_NUM)
//		return LEDSTATE_UNKNOWN;
//	return led_state[led];
//}
//
//// Получить состояние светодиода и времена мигания
//uint8_t LED_GetBlinkState(int led, uint16_t *blink_on, uint16_t *blink_off)
//{
//	if(led >= LEDS_NUM)
//	{
//		*blink_on = 0;
//		*blink_off = 0;
//		return LEDSTATE_UNKNOWN;
//	}
//	*blink_on = led_blink_on[led];
//	*blink_off = led_blink_off[led];
//	return led_state[led];
//}
//
//
//// Зажечь светодиод
//void LED_On(int led)
//{
//	if(led >= LEDS_NUM)
//	{
//		return;
//	}
//	GPIO_SetBits(ledx[led].GPIOx, ledx[led].Pin);
//	led_state[led] = LEDSTATE_ON;
//	led_blink_on[led] = 0;
//	led_blink_off[led] = 0;
//}
//
//// Выключить светодиод
//void LED_Off(int led)
//{
//	if(led >= LEDS_NUM)
//	{
//		return;
//	}
//	GPIO_ResetBits(ledx[led].GPIOx, ledx[led].Pin);
//	led_state[led] = LEDSTATE_OFF;
//}
//
//// Включить режим мигания светодиода
//void LED_OnBlink(int led, uint16_t blink_on, uint16_t blink_off)
//{
//	if(led >= LEDS_NUM)
//	{
//		return;
//	}
//	led_blink_on[led] = blink_on;
//	led_blink_off[led] = blink_off;
//
//	led_ticks_on[led] = 0;
//	led_ticks_off[led] = 0;
//
//	if(led_blink_off[led] == 0)
//	{
//		LED_On(led);
//		return;
//	}
//	if(led_blink_on[led] == 0)
//	{
//		LED_Off(led);
//		return;
//	}
//	led_state[led] = LEDSTATE_BLINK;
//}
//
//
//// Обработка SysTick - 1 мс
//// Для режимов мигания
//// Вызывается в stm32f10x_it.c -> SysTick_Handler
//void LED_SysTick_Handler()
//{
//	int i;
//	for(i = 0; i < LEDS_NUM; i++)
//	{
//		if(led_state[i] != LEDSTATE_BLINK)
//			continue;
//
//		if (led_ticks_on[i] == 0)
//		{
//			GPIO_SetBits(ledx[i].GPIOx, ledx[i].Pin);
//		}
//
//		if (led_ticks_on[i] <= led_blink_on[i])
//		{
//			led_ticks_on[i]++;
//			continue;
//		}
//
//		if (led_ticks_off[i] == 0)
//		{
//			GPIO_ResetBits(ledx[i].GPIOx, ledx[i].Pin);
//		}
//
//		if (led_ticks_off[i] <= led_blink_off[i])
//		{
//			led_ticks_off[i]++;
//			continue;
//		}
//
//		led_ticks_on[i] = 0;
//		led_ticks_off[i] = 0;
//	}
//}
