import json
import os
import sys

WORKING_PATH = os.path.dirname(sys.argv[0])
RESOURCE_PATH = os.path.join(WORKING_PATH,"resources")

# ---------------------------------------------------------------------------- #
# All message from client to server and from server to client transmiting using
# json format. Because this format quite simple and trasforming from python dict
# and to python dict can be done easily
# JSON -> PYTHON-DICT -> CMD -> RESPONSE
# Example of JSON Message for servo set new angular position command:
# { "Command": "SERVO_SET_ANGLE", "ServoName": ["FLT","FRC"], "ServoPos": [30.0,50.0] }
# { "Command": "SERVO_SET_ANGLE", "ServoName": ["ALL"], "ServoPos": [0.0,0.0,45.0,0.0,0.0,45.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,45.0,0.0,0.0,45.0,10.0,10.0,0.0] }
# { "Command": "SERVO_GET_ANGLE", "ServoName": ["ALL"] }
# { "Command": "ERROR", "ErrorType": "ERROR_BAD_CMD_FORMAT", "Message": "...." }
# { "Command": "RESPONSE", "Message": "........" }
# ---------------------------------------------------------------------------- #

HXAS_JSON_CMD          = "Command"

# HXAS_CMD_ERROR
HXAS_JSON_ERRTYPE      = "ErrorType" # Formal error name

# HXAS_CMD_ERROR, HXAS_CMD_TEXT
HXAS_JSON_MESSAGE      = "Message" # For transmitting error and text messages

# HXAS_CMD_STATUS, HXAS_CMD_ENABLE, HXAS_CMD_DISABLE,
# HXAS_CMD_SET_ANGLE, HXAS_CMD_GET_ANGLE
HXAS_JSON_SERVO_NAME   = "ServoName"

# HXAS_CMD_SET_ANGLE, HXAS_CMD_GET_ANGLE
HXAS_JSON_SERVO_POS    = "ServoPos" # Used to set new angles of servos horn

# HXAS_CMD_STATUS, HXAS_CMD_ENABLE, HXAS_CMD_DISABLE
HXAS_JSON_SERVO_STATE  = "ServoState" # Used to set enable/disable state

HXAS_CMD_DISCONNECT  = "DISCONNECT"       # Client disconnect command
HXAS_CMD_RESPONSE    = "RESPONSE"         # Transmit response text message or value message if command is OK
HXAS_CMD_ERROR       = "ERROR"            # Transmit an error type and error message if occurried
HXAS_CMD_SET_ANGLE   = "SERVO_SET_ANGLE"  # Set new angular position for specified servos
HXAS_CMD_GET_ANGLE   = "SERVO_GET_ANGLE"  # Get new angular position for specified servos
HXAS_CMD_DISABLE     = "SERVO_DISABLE"    # Disable specified servos
HXAS_CMD_ENABLE      = "SERVO_ENABLE"     # Enable specified servos
HXAS_CMD_STATUS      = "SERVO_STATUS"     # Get servo status: enable or disable
HXAS_CMD_REMOVE_LUT  = "SERVO_REMOVE_LUT" # Remove current lookup table for servo calibration

# HXAS_CMD_ERROR: formalized error names
HXAS_ERROR_STATE_UNK    = "ERROR_SERVO_STATE_UNKNOWN"
HXAS_ERROR_BAD_FORMAT   = "ERROR_BAD_CMD_FORMAT"
HXAS_ERROR_BAD_JSON     = "ERROR_BAD_JSON_FORMAT"
HXAS_ERROR_USB_TRANSMIT = "ERROR_USB_TRANSMIT"

# Routines for generating some of commands
def genResponseMessage(text):
    return json.dumps({HXAS_JSON_CMD:HXAS_CMD_RESPONSE,
                       HXAS_JSON_MESSAGE:text})

def genResponseServoState(names,values,text):
    return json.dumps({HXAS_JSON_CMD:HXAS_CMD_RESPONSE,
                       HXAS_JSON_SERVO_NAME:names,
                       HXAS_JSON_SERVO_POS:values,
                       HXAS_JSON_MESSAGE:text})

def genErrorMessage(errorType,text):
    return json.dumps({HXAS_JSON_CMD:HXAS_CMD_ERROR,
                       HXAS_JSON_ERRTYPE:errorType,
                       HXAS_JSON_MESSAGE:text})

def genDisconnectMessage():
    return json.dumps({HXAS_JSON_CMD:HXAS_CMD_DISCONNECT})

def genGetAllAngleMessage():
    return json.dumps({HXAS_JSON_CMD:HXAS_CMD_GET_ANGLE,
                       HXAS_JSON_SERVO_NAME:[SERVO_ALL]})

def genSetAngleMessage(names,values):
    return json.dumps({HXAS_JSON_CMD:HXAS_CMD_SET_ANGLE,
                       HXAS_JSON_SERVO_NAME:names,
                       HXAS_JSON_SERVO_POS:values})

# HXAS_JSON_SERVO_NAME: Name of servos
# If SERVO_ALL and any other name is in servo names list then error occurried
SERVO_ALL                 = "ALL"
SERVO_FRONT_LEFT_TIBIA    = "FLT"
SERVO_FRONT_LEFT_FEMUR    = "FLF"
SERVO_FRONT_LEFT_COXA     = "FLC"
SERVO_FRONT_RIGHT_TIBIA   = "FRT"
SERVO_FRONT_RIGHT_FEMUR   = "FRF"
SERVO_FRONT_RIGHT_COXA    = "FRC"
SERVO_MIDDLE_LEFT_TIBIA   = "MLT"
SERVO_MIDDLE_LEFT_FEMUR   = "MLF"
SERVO_MIDDLE_LEFT_COXA    = "MLC"
SERVO_MIDDLE_RIGHT_TIBIA  = "MRT"
SERVO_MIDDLE_RIGHT_FEMUR  = "MRF"
SERVO_MIDDLE_RIGHT_COXA   = "MRC"
SERVO_REAR_LEFT_TIBIA     = "RLT"
SERVO_REAR_LEFT_FEMUR     = "RLF"
SERVO_REAR_LEFT_COXA      = "RLC"
SERVO_REAR_RIGHT_TIBIA    = "RRT"
SERVO_REAR_RIGHT_FEMUR    = "RRF"
SERVO_REAR_RIGHT_COXA     = "RRC"
SERVO_HEAD_MANDIBLE_LEFT  = "HML"
SERVO_HEAD_MANDIBLE_RIGHT = "HMR"
SERVO_HEAD_NECK_ROLL      = "HNR"

# Servo indexes used to transmit data to USB servo driver
SRV_ID_FRONT_LEFT_TIBIA    =  0
SRV_ID_FRONT_LEFT_FEMUR    =  1
SRV_ID_FRONT_LEFT_COXA     =  2
SRV_ID_MIDDLE_LEFT_TIBIA   =  3
SRV_ID_MIDDLE_LEFT_FEMUR   =  4
SRV_ID_MIDDLE_LEFT_COXA    =  5
SRV_ID_REAR_LEFT_TIBIA     =  6
SRV_ID_REAR_LEFT_FEMUR     =  7
SRV_ID_REAR_LEFT_COXA      =  8
SRV_ID_FRONT_RIGHT_TIBIA   =  9
SRV_ID_FRONT_RIGHT_FEMUR   = 10
SRV_ID_FRONT_RIGHT_COXA    = 11
SRV_ID_MIDDLE_RIGHT_TIBIA  = 12
SRV_ID_MIDDLE_RIGHT_FEMUR  = 13
SRV_ID_MIDDLE_RIGHT_COXA   = 14
SRV_ID_REAR_RIGHT_TIBIA    = 15
SRV_ID_REAR_RIGHT_FEMUR    = 16
SRV_ID_REAR_RIGHT_COXA     = 17
SRV_ID_HEAD_MANDIBLE_LEFT  = 18
SRV_ID_HEAD_MANDIBLE_RIGHT = 19
SRV_ID_HEAD_NECK_ROLL      = 20

# Dictionary to translating indexes into names and vica versa
servoNamesList = {SERVO_FRONT_LEFT_TIBIA:    SRV_ID_FRONT_LEFT_TIBIA,
                  SERVO_FRONT_LEFT_FEMUR:    SRV_ID_FRONT_LEFT_FEMUR,
                  SERVO_FRONT_LEFT_COXA:     SRV_ID_FRONT_LEFT_COXA,
                  SERVO_FRONT_RIGHT_TIBIA:   SRV_ID_FRONT_RIGHT_TIBIA,
                  SERVO_FRONT_RIGHT_FEMUR:   SRV_ID_FRONT_RIGHT_FEMUR,
                  SERVO_FRONT_RIGHT_COXA:    SRV_ID_FRONT_RIGHT_COXA,
                  SERVO_MIDDLE_LEFT_TIBIA:   SRV_ID_MIDDLE_LEFT_TIBIA,
                  SERVO_MIDDLE_LEFT_FEMUR:   SRV_ID_MIDDLE_LEFT_FEMUR,
                  SERVO_MIDDLE_LEFT_COXA:    SRV_ID_MIDDLE_LEFT_COXA,
                  SERVO_MIDDLE_RIGHT_TIBIA:  SRV_ID_MIDDLE_RIGHT_TIBIA,
                  SERVO_MIDDLE_RIGHT_FEMUR:  SRV_ID_MIDDLE_RIGHT_FEMUR,
                  SERVO_MIDDLE_RIGHT_COXA:   SRV_ID_MIDDLE_RIGHT_COXA,
                  SERVO_REAR_LEFT_TIBIA:     SRV_ID_REAR_LEFT_TIBIA,
                  SERVO_REAR_LEFT_FEMUR:     SRV_ID_REAR_LEFT_FEMUR,
                  SERVO_REAR_LEFT_COXA:      SRV_ID_REAR_LEFT_COXA,
                  SERVO_REAR_RIGHT_TIBIA:    SRV_ID_REAR_RIGHT_TIBIA,
                  SERVO_REAR_RIGHT_FEMUR:    SRV_ID_REAR_RIGHT_FEMUR,
                  SERVO_REAR_RIGHT_COXA:     SRV_ID_REAR_RIGHT_COXA,
                  SERVO_HEAD_MANDIBLE_LEFT:  SRV_ID_HEAD_MANDIBLE_LEFT,
                  SERVO_HEAD_MANDIBLE_RIGHT: SRV_ID_HEAD_MANDIBLE_RIGHT,
                  SERVO_HEAD_NECK_ROLL:      SRV_ID_HEAD_NECK_ROLL}

# Reverse dictionary, using for converting routines. If SERVO_ALL specified
servoIndexesList = { }
for name in servoNamesList:
    servoIndexesList[servoNamesList[name]] = name

sortedIndexes = sorted(servoIndexesList)

# Total servo count
SERVO_COUNT = len(servoNamesList)

# USB transmit commands and variables
USB_PACKET_SIZE = 0x40
USB_CMD_SET_CONTROL_VALUES = 0x53
USB_CMD_GET_CONTROL_VALUES = 0x47
USB_UNKNOWN_SERVO_POSITION = "UNK"

# Servo angles limits
SERVO_ANGLE_MAX = 90.0
SERVO_ANGLE_MIN = -90.0
