/******************** (C) COPYRIGHT 2009 STMicroelectronics ********************
* File Name          : usb_endp.c
* Author             : MCD Application Team
* Version            : V3.1.0
* Date               : 10/30/2009
* Description        : Endpoint routines
********************************************************************************
* THE PRESENT FIRMWARE WHICH IS FOR GUIDANCE ONLY AIMS AT PROVIDING CUSTOMERS
* WITH CODING INFORMATION REGARDING THEIR PRODUCTS IN ORDER FOR THEM TO SAVE TIME.
* AS A RESULT, STMICROELECTRONICS SHALL NOT BE HELD LIABLE FOR ANY DIRECT,
* INDIRECT OR CONSEQUENTIAL DAMAGES WITH RESPECT TO ANY CLAIMS ARISING FROM THE
* CONTENT OF SUCH FIRMWARE AND/OR THE USE MADE BY CUSTOMERS OF THE CODING
* INFORMATION CONTAINED HEREIN IN CONNECTION WITH THEIR PRODUCTS.
*******************************************************************************/

/* Includes ------------------------------------------------------------------*/
#include "usb_lib.h"
#include "usb_istr.h"

#include "user_usb.h"

// $USBCONFIG - Тут нужно при необходимости добавить/удалить Callback-и Ендпойинтов
// См. также usb_conf.h

// Ендпойнт 1. 
void EP1_IN_Callback(void)
{

}

// Ендпойнт 2. 
void EP2_OUT_Callback(void)
{
	// Разрешаем ендпойнту получить следующую команду
	SetEPRxStatus(ENDP2, EP_RX_VALID);

	// Чтение и обработка пришедших данных
	usbIRQHandler();
}

// Ендпойнт 3. 
void EP3_IN_Callback(void)
{

}

// Ендпойнт 4. Ничего не делает.
void EP4_OUT_Callback(void)
{
	// Разрешаем ендпойнту получить следующую команду
	SetEPRxStatus(ENDP4, EP_RX_VALID);
}


/******************* (C) COPYRIGHT 2009 STMicroelectronics *****END OF FILE****/

