#include "ServoControl.h"

// Rewrite input value to internal buffer
Servo_Typedef ServoArray[SERVO_COUNT];

// Internal buffer
Control_Typedef ServoControl[SERVO_COUNT];

// Preload buffer
Control_Typedef PreloadControl[SERVO_COUNT];

// Current processing servo in interrupt (which of servo pulse will be finished)
uint8_t CurrentServo = 0;

// Information from outer buffer reread into internal in the current period
//ServoControlStatus ControlStatus = BUSY;
ServoControlStatus PreloadStatus = BUSY;
uint8_t isPreloadBufferUpdated = 0x00;

// Flag indicate that input array of control values is already sorted
//uint8_t isControlSorted = 0;

void GPIO_SetPinConfig(GPIO_TypeDef *GPIOx, uint16_t GPIO_Pin_x,
		GPIOSpeed_TypeDef GPIO_Speed, GPIOSpeed_TypeDef GPIO_Mode)
{
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_x;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode;
	GPIO_Init(GPIOx, &GPIO_InitStructure);
}

void InitServoPins(Servo_Typedef *ServoSet)
{
	uint16_t k = 0;
	uint8_t  PeriphFlagEnable[7] = {0x00};
	for (k = 0; k < SERVO_COUNT; k++)
	{
		if (ServoSet[k].Port == GPIOA && !PeriphFlagEnable[0])
		{
			RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
			PeriphFlagEnable[0] = 1;
		}
		else if (ServoSet[k].Port == GPIOB && !PeriphFlagEnable[1])
		{
			RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
			PeriphFlagEnable[1] = 1;
		}
		else if (ServoSet[k].Port == GPIOC && !PeriphFlagEnable[2])
		{
			RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);
			PeriphFlagEnable[2] = 1;
		}
		else if (ServoSet[k].Port == GPIOD && !PeriphFlagEnable[3])
		{
			RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOD, ENABLE);
			PeriphFlagEnable[3] = 1;
		}
		else if (ServoSet[k].Port == GPIOE && !PeriphFlagEnable[4])
		{
			RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOE, ENABLE);
			PeriphFlagEnable[4] = 1;
		}
		else if (ServoSet[k].Port == GPIOF && !PeriphFlagEnable[5])
		{
			RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOF, ENABLE);
			PeriphFlagEnable[5] = 1;
		}
		else if (ServoSet[k].Port == GPIOG && !PeriphFlagEnable[6])
		{
			RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOG, ENABLE);
			PeriphFlagEnable[6] = 1;
		}

		GPIO_SetPinConfig(
				ServoSet[k].Port,
				ServoSet[k].Pin,
				GPIO_Speed_50MHz,
				GPIO_Mode_Out_PP);
	}
}

void qs(Control_Typedef *items, int16_t left, int16_t right)
{
	Control_Typedef tmp;
	int16_t i, j;
	int16_t x;
	i = left; j = right;

    // находим середину. для компаранда
	x = items[(left+right)/2].PulseWidth;

	// переносим элементы в разделённые области
	do
	{
		while ((items[i].PulseWidth < x) && (i < right)) i++;
		while ((x < items[j].PulseWidth) && (j > left)) j--;

		if (i <= j)
		{
			tmp = items[i];
			items[i] = items[j];
			items[j] = tmp;
			i++; j--;
		}
	} while (i <= j);

	// если массив не отсортирован вызываем функцию рекурсивно
	if (left < j) qs(items, left, j);
	if (i < right) qs(items, i, right);
}

void quicksort (Control_Typedef *items, uint16_t len)
{
//	if (!isControlSorted)
//	{
	// при первом вызове предлагаем к сортировке весь массив
	qs(items, 0, len-1);

		// Array sorted, not need to resort it if we not rewrite new values
//		isControlSorted = 1;
//	}
}

void InitPWM(Servo_Typedef *_ServoArray)
{
	// Save pinout servo configuration to internal buffer
	// Avoid problem if outer buffer rewrite
	uint8_t k = 0;
	for (k = 0; k < SERVO_COUNT; k++)
		ServoArray[k] = _ServoArray[k];

	// Initialize servo configuration pinout
	InitServoPins(ServoArray);

	// Configuration of Timer 2 interrupt
	// TODO: CHOOSE WRITE PRIORITY VALUES
	NVIC_InitTypeDef NVIC_InitStructure;
	//NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1); // -- previous: delete
    NVIC_InitStructure.NVIC_IRQChannel = TIM2_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 0; //2
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);

    // Enable timing
	RCC->APB1ENR |= RCC_APB1Periph_TIM2;
	// Set prescaler, one step of counter = 0.5 us
	TIM2->PSC = (36 - 1);
	// Set PWM period (necessary to multiply by 2)
	TIM2->ARR = (PWM_PERIOD << 1);
	// Reset timer counter
	TIM2->CNT = 0;

	TIM2->CCMR1 &= ~TIM_CCMR1_CC1S;  // Configure channel 1 as output
	TIM2->CCMR1 &= ~TIM_CCMR1_OC1FE; // Disable output compare fast
	TIM2->CCMR1 &= ~TIM_CCMR1_OC1PE; // Disable output compare preload
	TIM2->CCMR1 &= ~TIM_CCMR1_OC1M;  // Disable compare output
	TIM2->CCMR1 &= ~TIM_CCMR1_OC1CE; // Disable output compare clear

	TIM2->DIER |= TIM_DIER_CC1IE;    // Capture/Compare 1 Interrupt enable
	TIM2->DIER |= TIM_DIER_UIE;      // Update interrupt enable

	// Clear pending bits of timer interrupt
	TIM2->SR &= ~(TIM_SR_UIF | TIM_SR_CC1IF);

	// Disable control on all servo pins, initialize it = 0
	for (k = 0; k < SERVO_COUNT; k++)
		ServoArray[k].Port->ODR &= ~ServoArray[k].Pin;

	// Initializing is OK and can accept new control values
	//ControlStatus = READY;
	PreloadStatus = READY;
}

//ServoControlStatus GetControlStatus()
//{
//	return ControlStatus;
//}

ServoControlBool PreloadControlValues(Control_Typedef *InputControlValues)
{
	// If we are controlling servo now
	// (at least one pulse hasn't finished yet)
	// we cannot loading new values
//	if (ControlStatus == BUSY)
//		return FAIL;

	// New control values loading from the outer buffer
	// Cannot loaded any values during this period
	PreloadStatus = BUSY;

	// Copy new values of pulse width to internal buffer
	uint8_t k = 0;
	for (k = 0; k < SERVO_COUNT; k++)
	{
		PreloadControl[k] = InputControlValues[k];

		if (PreloadControl[k].PulseWidth > PWM_PULSE_MAX)
			PreloadControl[k].PulseWidth = PWM_PULSE_MAX;
		else if (PreloadControl[k].PulseWidth < PWM_PULSE_MIN)
			PreloadControl[k].PulseWidth = PWM_PULSE_MIN;
	}

	// Now array is not sorted, we need to resort it
	//isControlSorted = 0;

	isPreloadBufferUpdated = 1;

	PreloadStatus = READY;

	return OK;
}

void ControlStartPeriod()
{
	if (isPreloadBufferUpdated && PreloadStatus == READY)
	{
		uint16_t k = 0;
		for (k = 0; k < SERVO_COUNT; k++)
			ServoControl[k] = PreloadControl[k];

		// Sort pulse width array in increasing order
		quicksort(ServoControl, SERVO_COUNT);

		isPreloadBufferUpdated = 0;
	}

//	// Set first servo index
//	CurrentServo = 0;
//	// Set the smallest pulse width
//	TIM2->CCR1 = (ServoControl[CurrentServo].PulseWidth << 1);

	// Now we cannot change control values
	// ControlStatus = BUSY;
}

void RunPWM(Control_Typedef *InputControlValues)
{
	uint16_t k = 0;

//	if (ControlStatus == READY)
//	{

	// Copy startup values into internal buffer
	PreloadControlValues(InputControlValues);

	// Sort array values, set first servo to control, set status to BUSY
	ControlStartPeriod();

	// Set first servo index
	CurrentServo = 0;
	// Set the smallest pulse width
	TIM2->CCR1 = (ServoControl[CurrentServo].PulseWidth << 1);

	// Start of generating impulse on all PWM pins
	for (k = 0; k < SERVO_COUNT; k++)
		ServoArray[k].Port->ODR |= ServoArray[k].Pin;
	TIM2->CR1 |= TIM_CR1_CEN; // Run timer

//	}
}

void IRQServoControl()
{
	//TIM2->CR1 &= ~TIM_CR1_CEN;
	// Choose which of event has been occurred: end of pulse or period
	if ((TIM2->SR & TIM_SR_UIF) != 0) // End of period more priority ??
	{
		uint8_t k = 0;

		// Clear pending interrupt bit (period)
		TIM2->SR &= ~TIM_SR_UIF;

		// Start of generating impulse on all PWM pins
		for (k = 0; k < SERVO_COUNT; k++)
			ServoArray[k].Port->ODR |= ServoArray[k].Pin;

		// Set first servo index
		CurrentServo = 0;
		// Set the smallest pulse width
		TIM2->CCR1 = (ServoControl[CurrentServo].PulseWidth << 1);

		// Enable counter interrupt
		TIM2->DIER |= TIM_DIER_CC1IE;
	}
	else if (((TIM2->SR & TIM_SR_CC1IF) != 0) &&
			((TIM2->DIER & TIM_DIER_CC1IE) != 0)) // End of pulse less priority
	{
		uint8_t k = 0;

		// Clear pending interrupt bit (pulse end)
		TIM2->SR &= ~TIM_SR_CC1IF;

		for (k = CurrentServo; k < SERVO_COUNT; k++)
		{
			// Finish all pulses that period same as current
			if (ServoControl[k].PulseWidth ==
				ServoControl[CurrentServo].PulseWidth)
			{
				uint8_t indx = ServoControl[k].Indx;
				ServoArray[indx].Port->ODR &= ~ServoArray[indx].Pin;
			}
			else break;
		}

		if (k < SERVO_COUNT)
		{
			// If not all servos processed set
			// next pulse width to counter (CCR1)
			CurrentServo = k;
			TIM2->CCR1 = (ServoControl[CurrentServo].PulseWidth << 1);
		}
		else
		{
			// else disable counter interrupt
			// until PWM period not finished
			TIM2->DIER &= ~TIM_DIER_CC1IE;

			// Sort array values, set first servo to control, set status to BUSY
			ControlStartPeriod();

			if (GPIOE->ODR & GPIO_Pin_5)
				GPIOE->ODR &= ~(GPIO_Pin_5);
			else
				GPIOE->ODR |= GPIO_Pin_5;

			// Waiting for new control values
			// ControlStatus = READY;
		}
	}
	//TIM2->CR1 |= TIM_CR1_CEN;
}
