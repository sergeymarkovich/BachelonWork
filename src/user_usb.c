#include "usb_lib.h"

#include "user_usb.h"
#include "hw_config.h"

#include "stm32f10x.h"
#include "stm32f10x_rcc.h"
#include "stm32f10x_gpio.h"

#define USB_RECIEVE_OK   0x01
#define USB_RECIEVE_FAIL 0x02
#define USB_BAD_LENGTH   0x03

bool usbBufferLocked = FALSE;
bool usbBufferUpdated = FALSE;

uint8_t usbInternalBuffer[USB_PACKET_SIZE];

bool usbIsBufferUpdated()
{
	return usbBufferUpdated;
}

void usbSetReceivedData(uint8_t *inData, uint16_t byteCount)
{
	uint16_t k = 0;

	if (byteCount > USB_PACKET_SIZE)
		byteCount = USB_PACKET_SIZE;

	usbBufferLocked = TRUE;
	for (k = 0; k < byteCount; k++)
		usbInternalBuffer[k] = inData[k];
	usbBufferLocked = FALSE;

	usbBufferUpdated = TRUE;
}

bool usbGetReceivedData(uint8_t *outData, uint16_t byteCount)
{
	if (!usbBufferLocked)
	{
		uint16_t k = 0;

		if (byteCount > USB_PACKET_SIZE)
			byteCount = USB_PACKET_SIZE;

		usbBufferLocked = TRUE;
		for (k = 0; k < byteCount; k++)
			outData[k] = usbInternalBuffer[k];
		usbBufferLocked = FALSE;

		usbBufferUpdated = FALSE;

		return TRUE;
	}

	return FALSE;
}

void usbSendData(uint8_t *inData, uint16_t byteCount)
{
	if (byteCount > USB_PACKET_SIZE)
		byteCount = USB_PACKET_SIZE;

	USB_SIL_Write(EP1_IN, inData, byteCount);

	SetEPTxValid(ENDP1);
}

// Check include interrupt (interrupt in interrupt)
void usbIRQHandler()
{
	uint16_t k = 0;
	uint16_t readCount = 0;
	uint8_t request[USB_PACKET_SIZE] = {0x00};
	uint8_t response[USB_PACKET_SIZE] = {0x00};

	readCount = USB_SIL_Read(EP2_OUT, request);

//	if (readCount != USB_PACKET_SIZE)
//	{
//		response[0] = USB_BAD_LENGTH;
//		USB_SIL_Write(EP1_IN, response, readCount);
//	}
//	else
//	{
	if (!usbBufferLocked)
	{
		//GPIOC->ODR &= ~GPIO_Pin_0;

		usbBufferLocked = TRUE;
		for (k = 0; k < readCount; k++)
			usbInternalBuffer[k] = request[k];
		usbBufferLocked = FALSE;

		usbBufferUpdated = TRUE;
		response[0] = USB_RECIEVE_OK;
		USB_SIL_Write(EP1_IN, response, USB_PACKET_SIZE);
	}
	else
	{
		response[0] = USB_RECIEVE_FAIL;
		USB_SIL_Write(EP1_IN, response, USB_PACKET_SIZE);
	}
//	}

	SetEPTxValid(ENDP1);
}
