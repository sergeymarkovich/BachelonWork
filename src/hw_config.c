/******************** (C) COPYRIGHT 2009 STMicroelectronics ********************
* File Name          : hw_config.c
* Author             : Ezhik (thx to MCD Application Team)
* Version            : V1.0.0
* Date               : 09/06/2011
* Description        : ������������ � ���������
********************************************************************************
* THE PRESENT FIRMWARE WHICH IS FOR GUIDANCE ONLY AIMS AT PROVIDING CUSTOMERS
* WITH CODING INFORMATION REGARDING THEIR PRODUCTS IN ORDER FOR THEM TO SAVE TIME.
* AS A RESULT, STMICROELECTRONICS SHALL NOT BE HELD LIABLE FOR ANY DIRECT,
* INDIRECT OR CONSEQUENTIAL DAMAGES WITH RESPECT TO ANY CLAIMS ARISING FROM THE
* CONTENT OF SUCH FIRMWARE AND/OR THE USE MADE BY CUSTOMERS OF THE CODING
* INFORMATION CONTAINED HEREIN IN CONNECTION WITH THEIR PRODUCTS.
*******************************************************************************/


// Includes ------------------------------------------------------------------
#include "hw_config.h"

#include "stm32f10x.h"
#include "stm32f10x_rcc.h"
#include "stm32f10x_gpio.h"

#include "usb_desc.h"
#include "usb_pwr.h"
#include "usb_lib.h"
#include "misc.h"

// Private variables ---------------------------------------------------------
ErrorStatus HSEStartUpStatus;

// Private function prototypes -----------------------------------------------
//static void RCC_Config(void);
void USB_Disconnect_Config(void);

// Private functions ---------------------------------------------------------

// ������������� ����� � �������
void Set_System(void)
{

#ifdef USB_DISCONNECT
	// ������������ ����, ������������ USB
	USB_Disconnect_Config();
#endif

}

// ������ ����� USB (48 ���)
void Set_USBClock(void)
{
	// ��������
	RCC_USBCLKConfig(RCC_USBCLKSource_PLLCLK_1Div5);

	// �������� ���� USB
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_USB, ENABLE);
}

// ����� ������� �����������������. ����� ����� ��� ��������� ��� ������ �����.
void Enter_LowPowerMode(void)
{
  // ��������� ��������� ������� � Suspended
  bDeviceState = SUSPENDED;
}

// ����� �� ������ ������� �����������������. �������� ����� �������.
void Leave_LowPowerMode(void)
{
  DEVICE_INFO *pInfo = &Device_Info;

  // ������ ���������� ��������� �������
  if (pInfo->Current_Configuration != 0)
  {
    bDeviceState = CONFIGURED;
  }
  else
  {
    bDeviceState = ATTACHED;
  }

}

// ������������ USB-����������
void USB_Interrupts_Config(void)
{
	NVIC_InitTypeDef NVIC_InitStructure;

	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);  // NVIC_PriorityGroup_1

	NVIC_InitStructure.NVIC_IRQChannel = TIM2_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 0; //2
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_Init(&NVIC_InitStructure);

	NVIC_InitStructure.NVIC_IRQChannel = USB_LP_CAN1_RX0_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1; //1  3
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 2;        //1  1
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_Init(&NVIC_InitStructure);

	NVIC_InitStructure.NVIC_IRQChannel = USB_HP_CAN1_TX_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1; //1  3
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;        //0  0
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_Init(&NVIC_InitStructure);
}


// ����������� �������-���������� USB-������
void USB_Cable_Config (FunctionalState NewState)
{
#ifdef USB_DISCONNECT
  if (NewState != USB_DISCONNECT_LOG1)
  {
  	// ���. 0 - �������
    GPIO_ResetBits(USB_DISCONNECT, USB_DISCONNECT_PIN);
  }
  else
  {
  	// ���. 1 - ����������
    GPIO_SetBits(USB_DISCONNECT, USB_DISCONNECT_PIN);
  }
#endif
}


// �������� ��������� ������ ����������.
// �� �����������. ������ ��� ������������� � VID, PID � Windows-��������� �� STM
//void Get_SerialNum(void)
//{
//  uint32_t Device_Serial0, Device_Serial1, Device_Serial2;
//
//  Device_Serial0 = *(__IO uint32_t*)(0x1FFFF7E8);
//  Device_Serial1 = *(__IO uint32_t*)(0x1FFFF7EC);
//  Device_Serial2 = *(__IO uint32_t*)(0x1FFFF7F0);
//
//  if (Device_Serial0 != 0)
//  {
//    SomeDev_StringSerial[2] = (uint8_t)(Device_Serial0 & 0x000000FF);
//    SomeDev_StringSerial[4] = (uint8_t)((Device_Serial0 & 0x0000FF00) >> 8);
//    SomeDev_StringSerial[6] = (uint8_t)((Device_Serial0 & 0x00FF0000) >> 16);
//    SomeDev_StringSerial[8] = (uint8_t)((Device_Serial0 & 0xFF000000) >> 24);
//
//    SomeDev_StringSerial[10] = (uint8_t)(Device_Serial1 & 0x000000FF);
//    SomeDev_StringSerial[12] = (uint8_t)((Device_Serial1 & 0x0000FF00) >> 8);
//    SomeDev_StringSerial[14] = (uint8_t)((Device_Serial1 & 0x00FF0000) >> 16);
//    SomeDev_StringSerial[16] = (uint8_t)((Device_Serial1 & 0xFF000000) >> 24);
//
//    SomeDev_StringSerial[18] = (uint8_t)(Device_Serial2 & 0x000000FF);
//    SomeDev_StringSerial[20] = (uint8_t)((Device_Serial2 & 0x0000FF00) >> 8);
//    SomeDev_StringSerial[22] = (uint8_t)((Device_Serial2 & 0x00FF0000) >> 16);
//    SomeDev_StringSerial[24] = (uint8_t)((Device_Serial2 & 0xFF000000) >> 24);
//  }
//}

// ������������ ����, ����������� �� ����������� �������-���������� USB
// RCC_APB2Periph_GPIO_DISCONNECT, USB_DISCONNECT, USB_DISCONNECT_PIN ���������� ������� � platform_config.h
#ifdef USB_DISCONNECT
void USB_Disconnect_Config(void)
{
  GPIO_InitTypeDef GPIO_InitStructure;

  // �������� ������ ����
  RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIO_DISCONNECT, ENABLE);

  // ��� ��������������� ��� Out Push-Pull
  GPIO_SetBits(USB_DISCONNECT, USB_DISCONNECT_PIN);
  GPIO_InitStructure.GPIO_Pin = USB_DISCONNECT_PIN;
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
  GPIO_Init(USB_DISCONNECT, &GPIO_InitStructure);

  // ��������� �������� - ���. 1. ������������� ����������� USB.
  GPIO_SetBits(USB_DISCONNECT, USB_DISCONNECT_PIN);
}
#endif

// ����� �����
