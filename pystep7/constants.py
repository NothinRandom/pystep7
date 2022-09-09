"""
File holds enumeration
"""


class Area:
    DATA_RECORD         = 0x01
    SYSTEM_INFO_200     = 0x03
    SYSTEM_FLAGS_200    = 0x05
    ANALOG_INPUT_200    = 0x06
    ANALOG_OUTPUT_200   = 0x07
    COUNTER_S7          = 0x1C # CT
    TIMER_S7            = 0x1D # TM
    IEC_COUNTER_200     = 0x1E
    IEC_TIMER_200       = 0x1F
    DIRECT_ACCESS       = 0x80
    PE_INPUTS           = 0x81 # PE
    PA_OUTPUTS          = 0x82 # PA
    MK_FLAGS            = 0x83 # MK
    DB_DATABLOCKS       = 0x84 # DB
    DI_DB_INSTANCE      = 0x85
    LOCAL_DATA          = 0x86


class COTP:
    NOP                 = 0x00
    EXPEDITED_DATA      = 0x10
    CLTP_USER_DATA      = 0x20
    EXPEDITED_DATA_ACK  = 0x40
    REJECT              = 0x50
    ACK_DATA            = 0x70
    DISCONNECT_REQUEST  = 0x80
    DISCONNECT_CONFIRM  = 0xC0
    CONNECT_CONFIRM     = 0xD0
    CONNECT_REQUEST     = 0xE0
    DATA                = 0xF0


class CpuStatus:
    UNKNOWN = 0x00
    RUN     = 0x08
    STOP    = 0x04


class CpuSubfunction:
    READ_SZL            = 0x01
    MESSAGE_SERVICE     = 0x02
    STOP                = 0x03
    ALARM_INDICATION    = 0x04
    ALARM_INITIATE      = 0x05
    ALARM_ACK1          = 0x06
    ALARM_ACK2          = 0x07


class DataType:
    NONE        = 0x00
    BIT         = 0x01
    BYTE        = 0x02
    CHAR        = 0x03
    WORD        = 0x04
    INT         = 0x05
    DWORD       = 0x06
    DINT        = 0x07
    REAL        = 0x08
    DATE        = 0x09
    TIME_OF_DAY = 0x0A
    TIME        = 0x0B
    S5TIME      = 0x0C
    DATETIME    = 0x0E
    STRING      = 0x13
    COUNTER     = 0x1C
    TIMER       = 0x1D
    IECTIMER    = 0x1E
    IECCOUNTER  = 0x1F
    HSCOUNTER   = 0x20


class TransportSize:
    NULL			= 0x00
    BIT				= 0x03
    BYTE_WORD_DWORD	= 0x04
    INT				= 0x05
    DINT			= 0x06
    REAL			= 0x07
    OCTET_STRING	= 0x09
    NCK_ADDRESS1	= 0x11
    NCK_ADDRESS2	= 0x12


class LastDataUnit:
    YES = 0x00
    NO  = 0x01


class ErrorClass:
    NO_ERROR                    = 0x00
    APPLICATION_RELATIONSHIP    = 0x81
    OBJECT_DEFINITION           = 0x82
    NO_RESOURCE_AVAILABLE       = 0x83
    ERROR_ON_SERVICE_PROCESSING = 0x84
    ERROR_ON_SUPPLIES           = 0x85
    ACCESS_ERROR                = 0x87


class Function:
    CPU_SERVICES        = 0x00
    READ_VARIABLE       = 0x04
    WRITE_VARIABLE      = 0x05
    REQUEST_DOWNLOAD    = 0x1A
    DOWNLOAD_BLOCK      = 0x1B
    DOWNLOAD_ENDED      = 0x1C
    START_UPLOAD        = 0x1D
    UPLOAD              = 0x1E
    END_UPLOAD          = 0x1F
    PLC_SERVICE         = 0x28
    PLC_STOP            = 0x29
    SETUP_COMMUNICATION = 0xF0


class FunctionGroup:
    BLOCK_REQUEST   = 0x43
    BLOCK_RESPONSE  = 0x83
    CPU_REQUEST     = 0x44
    CPU_RESPONSE    = 0x84
    TIME_REQUEST    = 0x47
    TIME_RESPONSE   = 0x87


class ParamMethod:
    REQUEST     = 0x11
    RESPONSE    = 0x12


class ParamErrorCode:
    NO_ERROR                    = 0x0000
    INVALID_BLOCK_NUMBER        = 0x0110
    INVALID_REQUEST_LENGTH      = 0x0111
    INVALID_PARAMETER           = 0x0112
    INVALID_BLOCK_TYPE          = 0x0113
    BLOCK_NOT_FOUND             = 0x0114
    BLOCK_ALREADY_EXISTS        = 0x0115
    BLOCK_WRITE_PROTECTED       = 0x0116
    BLOCK_OS_UPDATE_TOO_LARGE   = 0x0117
    INVALID_BLOCK_NUMBER1       = 0x0118
    INCORRECT_PASSWORD_ENTERED  = 0x0119
    PG_RESOURCE_ERROR           = 0x011A
    PLC_RESOURCE_ERROR          = 0x011B
    PROTOCOL_ERROR              = 0x011C
    TOO_MANY_BLOCKS             = 0x011D
    INVALID_DB_CONNECTION       = 0x011E
    RESULT_BUFFER_TOO_SMALL     = 0x011F


class ReturnCode:
    RESERVED                        = 0x00
    HARDWARE_ERROR                  = 0x01
    ACCESSING_OBJECT_NOT_ALLOWED    = 0x03
    INVALID_ADDRESS                 = 0x05
    DATATYPE_NOT_SUPPORTED          = 0x06
    DATATYPE_INCONSISTENT           = 0x07
    OBJECT_NOT_EXIST                = 0x0A
    SUCCESS                         = 0xFF


class ROSCTR:
    JOB         = 0x01
    ACK         = 0x02
    ACK_DATA    = 0x03
    USER_DATA   = 0x07


class SyntaxId:
    S7_ANY              = 0x10
    PBCR_ID	            = 0x13
    ALARM_LOCK_FREE     = 0x15
    ALARM_INDICATOR     = 0x16
    ALARM_ACK           = 0x19
    ALARM_QUERY_REQUEST = 0x1A
    NOTIFIER_INDICATOR  = 0x1C
    NCK                 = 0x82
    DRIVE_ES_ANY        = 0xA2
    DATA_BLOCK_READ     = 0xB0
    S7_1200_SYM         = 0xB2


class SystemStateList:
    CATALOG_CODE    = 0x0011
    CPU_DIAGOSTICS  = 0x00A0
    CPU_LEDS        = 0x0074 # 0x0019
    CPU_ID          = 0x001C
    CPU_STATUS      = 0x0424
    COMM_PROC       = 0x0131
    PROTECTION      = 0x0232 # index 0x0004


class TimeSubfunction:
    READ_CLOCK              = 0x01
    SET_CLOCK               = 0x02
    READ_CLOCK_FOLLOWING    = 0x03
    SET_CLOCK_2             = 0x04


class UserDataBlockSubfunction:
    MEMORY      = 0x01
    UNSUBSCRIBE = 0x04


class UserDataCyclicSubfunction:
    LIST_BLOCKS             = 0x01
    LIST_BLOCK_OF_TYPES     = 0x02
    GET_BLOCK_INFORMATION   = 0x03


class UserDataProgrammerSubfunction:
    requestDiagnosticData1	= 0x01
    varTab					= 0x02
    varTabResponse			= 0x04
    erase					= 0x0C
    readDiagnosticData		= 0x0E
    removeDiagnosticData	= 0x1F
    forces					= 0x10
    requestDiagnosticData2	= 0x13
    varTabRequest			= 0x14


class BLockSubfunction:
    LIST        = 0x01
    LIST_TYPE   = 0x02
    INFO        = 0x03

class VartabArea:
    MB        = 0x01
    MW        = 0x02
    MD        = 0x03
    IB        = 0x11
    IW        = 0x12
    ID        = 0x13
    QB        = 0x21
    QW        = 0x22
    QD        = 0x23
    PIB       = 0x31
    PIW       = 0x32
    PID       = 0x33
    TIMER     = 0x54
    COUNTER   = 0x64
    DBB       = 0x71
    DBW       = 0x72
    DBD       = 0x73


class ClientConnectionType:
    PG      = 0x01  # Programming
    OP      = 0x02  # 
    BASIC   = 0x03  #


class BlockLanguages:
    AWL     = 0x01
    KOP     = 0x02
    FUP     = 0x03
    SCL     = 0x04
    DB      = 0x05
    GRAPH   = 0x06


class BlockType:
    OB  = 0x38
    DB  = 0x41
    SDB = 0X42
    FC  = 0X43
    SFC = 0X44
    FB  = 0X45
    SFB = 0X46


class SubBlockType:
    OB  = 0x08
    DB  = 0x0A
    SDB = 0x0B
    FC  = 0x0C
    SFC = 0x0D
    FB  = 0x0E
    SFB = 0x0F

# ISO Connection Request telegram (22 bytes)
# Contains also ISO Header and COTP (Connection Oriented Transport Protocol) Header
ISO_CR = [
    # TPKT (RFC1006 Header)
    0x03, # RFC 1006 ID (3) 
    0x00, # Reserved, always 0
    0x00, # High part of packet length (entire frame, payload and TPDU included)
    0x16, # Low part of packet length (entire frame, payload and TPDU included)
    # ISO COTP (ISO 8073 Header)
    0x11, # PDU Size Length
    0xE0, # Connection Request ID
    0x00, # Destination Reference HI
    0x00, # Destination Reference LO
    0x00, # Source Reference HI
    0x01, # Source Reference LO
    0x00, # Class + Options Flags
    0xC0, # PDU Max Length ID
    0x01, # PDU Max Length HI
    0x0A, # PDU Max Length LO
    0xC1, # Source TSAP Identifier
    0x02, # Source TSAP Length (2 bytes)
    0x01, # Source TSAP HI (will be overwritten)
    0x00, # Source TSAP LO (will be overwritten)
    0xC2, # Destination TSAP Identifier
    0x02, # Destination TSAP Length (2 bytes)
    0x01, # Destination TSAP HI (will be overwritten)
    0x02  # Destination TSAP LO (will be overwritten)
]

# TPKT + ISO COTP Header (bytes)
TPKT_ISO = [
    # TPKT (RFC1006 Header)
    0x03, 0x00,
    0x00, 0x1f,         # Telegram Length (Data Size + 31 or 35)
    # ISO COTP (ISO 8073 Header)
    0x02, 0xf0,0x80     # COTP (see above for info)
]

# S7 PDU Negotiation Telegram (25 bytes)
S7_PN = [
    # TPKT (RFC1006 Header)
    0x03, 0x00, 
    0x00, 0x19,                 # Telegram Length (Data Size + 31 or 35)
    # ISO COTP (ISO 8073 Header)
    0x02, 0xf0, 0x80,           # TPKT + COTP (see above for info)
    # S7 Communication
    #   Header
    0x32,                       # S7 Protocol ID
    ROSCTR.JOB,                 # ROSCTR
    0x00, 0x00,                 # Redundancy identification
    0x04, 0x00,                 # PDU Reference
    0x00, 0x08,                 # Parameters Length
    0x00, 0x00,                 # Data Length = Size(bytes) + 4
    #   Parameter
    0xf0,                       # Function: setup comm
    0x00,                       # reserved
    0x00, 0x01,                 # Max AmQ: calling
    0x00, 0x01,                 # Max AmQ: called
    0x00, 0x1e                  # PDU Length Requested (Default 480 bytes)
]

# S7 Read/Write Request Header (Read: 31 bytes, Write: 35 bytes)
S7_READ_WRITE = [
    # TPKT (RFC1006 Header)
    0x03, 0x00,
    0x00, 0x1f,                 # Telegram Length (Data Size + 31 or 35)
    # ISO COTP (ISO 8073 Header)
    0x02, 0xf0, 0x80,           # COTP (see above for info)
    # S7 Communication
    #   Header
    0x32,                       # S7 Protocol ID
    ROSCTR.JOB,                 # ROSCTR
    0x00, 0x00,                 # Redundancy identification
    0x05, 0x00,                 # PDU Reference
    0x00, 0x0e,                 # Parameters Length
    0x00, 0x00,                 # Data Length = Size(bytes) + 4
    #   Parameter
    Function.READ_VARIABLE,     # Function (modify to write)
    0x01,                       # Items count
    0x12,                       # Var spec.
    0x0a,                       # Length of remaining bytes
    SyntaxId.S7_ANY,            # Syntax ID 
    DataType.BYTE,              # Transport Size
    0x00, 0x00,                 # Num Elements
    0x00, 0x00,                 # DB Number (if any, else 0)
    Area.DB_DATABLOCKS,         # Area
    0x00, 0x00, 0x00,           # Address
    # Write params
    0x00,                       # Reserved
    0x04,                       # Transport size
    0x00, 0x00                  # Data Length * 8 (if not bit or timer or counter)
]

# S7 PLC time request (29 bytes)
S7_GET_CLOCK = [
    # TPKT (RFC1006 Header)
    0x03, 0x00,
    0x00, 0x1D,                 # Telegram Length (29)
    # ISO COTP (ISO 8073 Header)
    0x02, 0xf0, 0x80,           # COTP (see above for info)
    # S7 Communication
    #   Header
    0x32,                       # S7 Protocol ID
    ROSCTR.USER_DATA,           # ROSCTR
    0x00, 0x00,                 # Redundancy identification
    0x38, 0x00,                 # PDU Reference
    0x00, 0x08,                 # Parameters Length
    0x00, 0x04,                 # Data Length = Size(bytes) + 4
    #   Parameter
    0x00, 0x01, 0x12,           # Parameter head
    0x04,                       # Parameter length
    ParamMethod.REQUEST,        # Method
    FunctionGroup.TIME_REQUEST, # Function group
    TimeSubfunction.READ_CLOCK, # Subfunction: read clock
    0x00,                       # Sequence number
    #   Data
    ReturnCode.OBJECT_NOT_EXIST,# Return code
    TransportSize.NULL,         # Transport size
    0x00, 0x00                  # Length
]

# Set Date/Time command (39 bytes)
S7_SET_CLOCK = [
    # TPKT (RFC1006 Header)
    0x03, 0x00, 
    0x00, 0x27,                 # Telegram Length (39)
    # ISO COTP (ISO 8073 Header)
    0x02, 0xf0, 0x80, 
    # S7 Communication
    #   Header
    0x32,                       # S7 Protocol ID
    ROSCTR.USER_DATA,           # ROSCTR
    0x00, 0x00,                 # Redundancy identification
    0x89, 0x03,                 # PDU Reference
    0x00, 0x08,                 # Parameters Length
    0x00, 0x0e,                 # Data Length = Size(bytes) + 4
    #   Parameter
    0x00, 0x01, 0x12,           # Parameter head
    0x04,                       # Parameter length
    ParamMethod.REQUEST,        # Method
    FunctionGroup.TIME_REQUEST, # Function group
    TimeSubfunction.SET_CLOCK,  # Subfunction
    0x00,                       # Sequence number
    #   Data
    ReturnCode.SUCCESS,         # Return code
    TransportSize.OCTET_STRING, # Transport size
    0x00, 0x0a,                 # Length
    0x00,                       # reserved
    0x19,                       # Hi part of Year (index 30)
    0x13,                       # Lo part of Year
    0x12,                       # Month
    0x06,                       # Day
    0x17,                       # Hour
    0x37,                       # Minute
    0x13,                       # Second
    0x00, 0x01                  # ms + Day of week   
]

# SZL First telegram request (33 bytes)
S7_SZL_FIRST = [
    # TPKT (RFC1006 Header)
    0x03, 0x00, 
    0x00, 0x21,                 # Telegram Length (33)
    # ISO COTP (ISO 8073 Header)
    0x02, 0xf0, 0x80,           # Parameter head
    # S7 Communication
    #   Header
    0x32,                       # S7 Protocol ID
    ROSCTR.USER_DATA,           # ROSCTR
    0x00, 0x00,                 # Redundancy identification
    0x05, 0x00,                 # PDU Reference
    0x00, 0x08,                 # Parameter length
    0x00, 0x08,                 # Data length
    #   Parameter
    0x00, 0x01, 0x12,           # Parameter head
    0x04,                       # Parameter length
    ParamMethod.REQUEST,        # Method
    FunctionGroup.CPU_REQUEST,  # Function group
    CpuSubfunction.READ_SZL,    # Subfunction
    0x00,                       # Sequence number
    #   Data
    ReturnCode.SUCCESS,         # Return code
    TransportSize.OCTET_STRING, # Transport size
    0x00, 0x04,                 # Length
    0x00, 0x00,                 # SZL-ID ID (29)
    0x00, 0x00                  # SZL-Index Index (31)
]

# SZL Next telegram request (33 bytes)
S7_SZL_NEXT = [
    # TPKT (RFC1006 Header)
    0x03, 0x00, 
    0x00, 0x21,                 # Telegram Length (33)
    # ISO COTP (ISO 8073 Header)
    0x02, 0xf0, 0x80,           # Parameter head
    # S7 Communication
    #   Header
    0x32,                       # S7 Protocol ID
    ROSCTR.USER_DATA,           # ROSCTR
    0x00, 0x00,                 # Redundancy identification
    0x06, 0x00,                 # PDU Reference
    0x00, 0x0c,                 # Parameter length
    0x00, 0x04,                 # Data length
    #   Parameter
    0x00, 0x01, 0x12,           # Parameter head
    0x08,                       # Parameter length
    ParamMethod.RESPONSE,       # Method
    FunctionGroup.CPU_REQUEST,  # Function group
    CpuSubfunction.READ_SZL,    # Subfunction
    0x01,                       # Sequence number
    0x00,                       # PDU Reference
    0x00,                       # Last data unit
    0x00, 0x00,                 # Error code
    #   Data
    ReturnCode.OBJECT_NOT_EXIST,# Return code
    TransportSize.NULL,         # Transport size
    0x00, 0x00                  # Length
]

# S7 STOP request (33 bytes)
S7_STOP = [
    # TPKT (RFC1006 Header)
    0x03, 0x00, 
    0x00, 0x21,                 # Telegram Length (33)
    # ISO COTP (ISO 8073 Header)
    0x02, 0xf0, 0x80,           # Parameter head
    # S7 Communication
    #   Header
    0x32,                       # S7 Protocol ID
    ROSCTR.JOB,                 # ROSCTR
    0x00, 0x00,                 # Redundancy identification
    0x0e, 0x00,                 # PDU Reference
    0x00, 0x10,                 # Parameter length
    0x00, 0x00,                 # Data length
    #   Parameter
    Function.PLC_STOP,          # Function: plc stop
    0x00, 0x00, 0x00,           # Reserved
    0x00, 0x00,                 # Reserved
    0x09,                       # string length
    0x50, 0x5f, 0x50,           # "P_PROGRAM"
    0x52, 0x4f, 0x47,           # "P_PROGRAM"
    0x52, 0x41, 0x4d            # "P_PROGRAM"
]

# S7 HOT Start request (37 bytes)
S7_HOT_START = [
    # TPKT (RFC1006 Header)
    0x03, 0x00, 
    0x00, 0x25,                 # Telegram Length (33)
    # ISO COTP (ISO 8073 Header)
    0x02, 0xf0, 0x80,           # Parameter head
    # S7 Communication
    #   Header
    0x32,                       # S7 Protocol ID
    ROSCTR.JOB,                 # ROSCTR: Job
    0x00, 0x00,                 # Redundancy identification
    0x0c, 0x00,                 # PDU Reference
    0x00, 0x14,                 # Parameter length
    0x00, 0x00,                 # Data length
    #   Parameter
    Function.PLC_SERVICE,       # Function
    0x00, 0x00, 0x00,           # Reserved
    0x00, 0x00, 0x00,           # Reserved
    0xfd,                       # Reserved
    0x00, 0x00,                 # Parameter block length 
    0x09,                       # string length
    0x50, 0x5f, 0x50,           # "P_PROGRAM"
    0x52, 0x4f, 0x47,           # "P_PROGRAM"
    0x52, 0x41, 0x4d            # "P_PROGRAM"
]

# S7 COLD Start request (39 bytes)
S7_COLD_START = [
    # TPKT (RFC1006 Header)
    0x03, 0x00, 
    0x00, 0x27,                 # Telegram Length (35)
    # ISO COTP (ISO 8073 Header)
    0x02, 0xf0, 0x80,           # Parameter head
    # S7 Communication
    #   Header
    0x32,                       # S7 Protocol ID
    ROSCTR.JOB,                 # ROSCTR: Job
    0x00, 0x00,                 # Redundancy identification
    0x0f, 0x00,                 # PDU Reference
    0x00, 0x16,                 # Parameter length
    0x00, 0x00,                 # Data length
    #   Parameter
    Function.PLC_SERVICE,       # Function
    0x00, 0x00, 0x00,           # Reserved
    0x00, 0x00, 0x00,           # Reserved
    0xfd,                       # Reserved
    0x00, 0x02,                 # Parameter block length 
    0x43, 0x20,                 # block argument
    0x09,                       # string length
    0x50, 0x5f, 0x50,           # "P_PROGRAM"
    0x52, 0x4f, 0x47,           # "P_PROGRAM"
    0x52, 0x41, 0x4d            # "P_PROGRAM"
]

# S7 Get Block Info Request Header (37 bytes)
S7_BLOCK_INFO = [
    # TPKT (RFC1006 Header)
    0x03, 0x00, 
    0x00, 0x25,                 # Telegram Length (37)
    # ISO COTP (ISO 8073 Header)
    0x02, 0xf0, 0x80,           # Parameter head
    # S7 Communication
    #   Header
    0x32,                       # S7 Protocol ID
    ROSCTR.USER_DATA,           # ROSCTR
    0x00, 0x00,                 # Redundancy identification
    0x05, 0x00,                 # PDU Reference
    0x00, 0x08,                 # Parameter length
    0x00, 0x0c,                 # Data length (12)
    #   Parameter
    0x00, 0x01, 0x12,           # Parameter head
    0x04,                       # Parameter length
    ParamMethod.REQUEST,        # Method
    FunctionGroup.BLOCK_REQUEST,# Function group
    BLockSubfunction.INFO,      # Subfunction
    0x00,                       # Sequence number
    ReturnCode.SUCCESS,         # Return code
    TransportSize.OCTET_STRING, # Transport size
    0x00, 0x08,                 # Length
    0x30, 0x41,                 # Block Type
    0x30, 0x30, 0x30,           # ASCII block number
    0x30, 0x30,                 # ASCII block number
    0x41                        # Filesystem
]

class Endian:
    native   = '='
    little   = '<'
    big      = '>'
    network  = '!'


class ModeSelector:
    RUN     = 0x01
    RUN_P   = 0x02
    STOP    = 0x03
    MRES    = 0x04


class StartupSwitch:
    COLD_RESTART    = 0x01
    WARM_RESTART    = 0x02
