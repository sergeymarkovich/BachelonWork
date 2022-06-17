
/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __SERVO_CONTROL_H
#define __SERVO_CONTROL_H

#include "stm32f10x.h"
#include "stm32f10x_rcc.h"
#include "stm32f10x_gpio.h"
#include "misc.h"

//#define SERVO_COUNT          3
#define SERVO_COUNT         21
#define PWM_PERIOD       20000 // us
#define PWM_PULSE_MAX     2400 // us
#define PWM_PULSE_MIN      600 // us
//#define PWM_SORT_OFFSET	  1000 // us

typedef enum {BUSY = 0, READY = !BUSY} ServoControlStatus;
typedef enum {FAIL = 0, OK = !FAIL} ServoControlBool;

typedef struct
{
	GPIO_TypeDef *Port;
	uint16_t      Pin;
} Servo_Typedef;

typedef struct
{
	uint16_t PulseWidth;
	uint8_t  Indx;
} Control_Typedef;

ServoControlStatus GetControlStatus();
ServoControlBool PreloadControlValues(Control_Typedef *InputControlValues);

void InitPWM(Servo_Typedef *_ServoArray);
void RunPWM(Control_Typedef *InputControlValues);
void IRQServoControl();

#endif  /*__SERVO_CONTROL_H*/
