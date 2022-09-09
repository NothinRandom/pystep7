# pystep7
A Python3 implementation of Siemens Step7 protocol

## Installation 
```console 
pip3 install pystep7
```


## How to use pystep7 
### 1. Connect and Send Commands
```python
from datetime import datetime
from pystep7 import Client
from pystep7.constants import Area, BlockType, DataType
from pystep7.tag import Tag


__RTAGS1 = [
    Tag(name="BIT", type=DataType.BIT),                # BIT
    Tag(name="BYTE", type=DataType.BYTE),              # BYTE
    Tag(name="CHAR", type=DataType.CHAR),              # CHAR
    Tag(name="DINT", type=DataType.DINT),              # DINT
    Tag(name="DWORD", type=DataType.DWORD),            # DWORD
    Tag(name="S7 DATE", type=DataType.DATE),           # S7 DATE
    Tag(name="S7 DATETIME", type=DataType.DATETIME),   # S7 DATETIME
    Tag(name="INT", type=DataType.INT),                # INT
    Tag(name="REAL", type=DataType.REAL),              # REAL
    Tag(name="S5 TIME", type=DataType.S5TIME),         # S5 TIME
    Tag(name="STRING", type=DataType.STRING),          # STRING
    Tag(name="S7 TIME", type=DataType.TIME),           # S7 TIME
    Tag(name="S7 TOD", type=DataType.TIME_OF_DAY),     # S7 TIME OF DAY
    Tag(name="WORD", type=DataType.WORD),              # WORD
]

__WTAGS2 = [
    Tag(name="BIT", value=1, type=DataType.BIT),         # BIT
    Tag(name="BYTE", value=1, type=DataType.BYTE),     # BYTE
    Tag(name="CHAR", value='T', type=DataType.CHAR),     # CHAR
    Tag(name="DINT", value=-10000, type=DataType.DINT),  # DINT
    Tag(name="DWORD", value=10000, type=DataType.DWORD), # DWORD
    Tag(
        name="S7 DATE", 
        value=date(2000,1,1), 
        type=DataType.DATE
    ),  # S7 DATE
    Tag(
        name="S7 DATETIME", 
        value=datetime(2022,9,4,10,11,12,130000),
        type=DataType.DATETIME
    ),   # S7 DATETIME
    Tag(name="INT", value=-100, type=DataType.INT),      # INT
    Tag(name="REAL", value=6.6, type=DataType.REAL),     # REAL
    Tag(
        name="S5 TIME",
        value=16990, 
        type=DataType.S5TIME
    ),  # S5 TIME (milliseconds) smallest is 10, largest is 9990000 (2H:46M:30S)
    Tag(
        name="STRING", 
        value='Hello World', 
        type=DataType.STRING
    ),  # STRING (max char is 254)
    Tag(
        name="S7 TIME", 
        value=1,    # time in milliseconds 
        type=DataType.TIME
    ),  # S7 TIME
    Tag(
        name="S7 TOD", 
        value=18000000,
        type=DataType.TIME_OF_DAY
    ),  # S7 TIME OF DAY: milliseconds since midnight
    Tag(name="WORD", value=1000, type=DataType.WORD),   # WORD

__HOST = '192.168.1.15' # REQUIRED
__PORT = 102            # OPTIONAL: default is 102
__RACK = 0              # OPTIONAL: default is 0
__SLOT = 0              # OPTIONAL: default is 0


with Client(host=__HOST, port=__PORT, rack=__RACK, slot=__SLOT) as plc:
    """
    Read PLC time

    Returns:
        datetime: datetime object that represents PLC time
            example:
                2022-09-08 17:07:25.380000
    """
    response = plc.read_plc_time()



    """
    Set PLC time
        example: Set PLC time using local time

    Args:
        dt(datetime): datetime object

    Returns:
        dt(datetime): the same datetime object passed in
    """
    response =plc.read_plc_time(dt=datetime.now())



    """
    Synchronize PLC time to PC time
        example: Set PLC time using UTC time

    Args:
        utc(bool): True to use UTC time and false using local time

    Returns:
        dt(datetime): the datetime object that was used
            example:
                2022-09-08 17:07:25.380000
    """
    response = plc.sync_plc_time(utc=True)



    """
    Read CPU Status

    Returns:
        CPUStatus(NamedTuple): (requestedMode(str), previousMode(str), error(str))
            example:
                Run,Unknown,
    """
    response = plc.read_cpu_status()



    """
    Read catalog (order) code

    Returns:
        CatalogCode(NamedTuple): (
            moduleOrderNumber(str), 
            moduleVersion(str), 
            basicHardwareId(str),
            hardwareVersion(str),
            basicFirmwareId(str),
            firmwareVersion(str),
            firmwareExtensionId(str),
            firmwareExtVersion(str),
            error(str)
        )
            example: 
                6ES7 318-3FL01-0AB0,9.1,6ES7 318-3FL01-0AB0,9.1,,22019.525,Boot Loader,16677.3084,
    """
    response = plc.read_catalog_code()



    """
    Read CPU information

    Returns:
        CatalogCode(NamedTuple): (
            systemName(str), 
            moduleName(str), 
            plantId(str),
            copyright(str),
            serialNumber(str),
            cpuType(str),
            memSerialNumber(str),
            manufacturerId(str),
            profileId(str),
            profileSpec(str),
            oemCopyright(str),
            oemId(str),
            oemAddId(str),
            locationId(str),
            error(str)
        )
            example:
                S7300/ET200M station_1,PLC_1,,Original Siemens Equipment,
                S C-J3LX93592017,CPU 319F-3 PN/DP,MMC 86A97F09,0x002a,
                0xf600,0x0001,,0x0000,0x00000000,,
    """
    response = plc.read_cpu_info()



    """
    Read communication processor

    Returns:
        list[CommProc]:
            example:
                [
                    CommProc(maxPDU=240, maxConnections=32, mpiRate=12000000, mkbusRate=187500, error='')
                ]
    """
    response = plc.read_comm_proc()



    """
    Stop PLC

    Returns:
        bool: True for successful, and False for failed
    """
    response = plc.stop()



    """
    Start PLC with initial settings

    Returns:
        bool: True for successful, and False for failed
    """
    response = plc.start_plc_cold()



    """
    Start PLC from previous state

    Returns:
        bool: True for successful, and False for failed
    """
    response = plc.start_plc_hot()



    """
    Read system state list (SZL-ID)

    Returns:
        bytes: Raw bytes that would need parsing
    """
    response = plc.read_szl(id=0x001C, index=0x0000)



    """
    Read protection level

    Returns:
        list[Protection]: (
            protectionLevel(int),
            passwordLevel(int),
            validProtectionLevel(int),
            modeSelector(str),
            startupSwitch(str),
            error(str)
        )
            example:
                [
                    Protection(
                        protectionLevel=1, 
                        passwordLevel=0, 
                        validProtectionLevel=1, 
                        modeSelector='Run Program', 
                        startupSwitch='Undefined', 
                        error=''
                    )
                ]
    """
    response = plc.read_protection()



    """
    Read CPU diagnostics

    Returns:
        list[CPUDiagnostics]: (
            eventId(str),
            description(str),
            priority(int),
            obNumber(int),
            datId(str),
            info1(str),
            info2(str),
            timestamp(datetime),
            error(str)
        )
            example:
                [
                    CPUDiagnostics(
                        eventId='0x4302', 
                        description='Mode transition from STARTUP to RUN', 
                        priority=255, 
                        obNumber=104, 
                        datId='0xc700', 
                        info1='0x0000', 
                        info2='0x08147714', 
                        timestamp=datetime.datetime(2022, 9, 8, 15, 23, 19, 521000), 
                        error=''
                    ),
                    ... 
                    CPUDiagnostics(
                        eventId='0x4302', 
                        description='Mode transition from STARTUP to RUN', 
                        priority=255, 
                        obNumber=104, 
                        datId='0xc700', 
                        info1='0x0000', 
                        info2='0x08147714', 
                        timestamp=datetime.datetime(2022, 9, 8, 8, 59, 44, 546000), 
                        error=''
                    )
                ]
    """
    response = plc.read_protection()



    """
    Read CPU LEDs

    Returns:
        list[CPULed]: (
            rack(int),
            type(int),
            id(str),
            on(int),
            flashing(bool),
            error(str)
        )
            example:
                [
                    CPULed(
                        rack=0, 
                        type=0, 
                        id='SF (group error)', 
                        on=False, 
                        flashing=False, 
                        error=''
                    ),
                    ...
                    CPULed(
                        rack=0, 
                        type=0, 
                        id='MAINT (maintenance demand)', 
                        on=False, 
                        flashing=False, 
                        error=''
                    )
                ]
    """
    response = plc.read_cpu_leds()



    """
    Read block info
        example: read info of data block 1

    Args:
        BlockType(int):
        BlockNumber(int):

    Returns:
        BlockInfo(NamedTuple): (
            flags(str),
            language(str),
            type(str),
            number(int),
            loadMemory(int),
            security(str),
            codeTimestamp(str),
            interfaceTimestamp(str),
            ssbLength(int),
            addLength(int),
            localDataLength(int),
            mc7Length(int),
            author(str),
            family(str),
            name(str),
            version(str),
            checksum(str),
            error(str)
        )
            example:
                [
                    BlockInfo(
                        flags='0x01', 
                        language='DB', 
                        type='DB', 
                        number=1, 
                        loadMemory=410, 
                        security=0, 
                        codeTimestamp=datetime.datetime(2022, 9, 8, 5, 44, 42, 465000), 
                        interfaceTimestamp=datetime.datetime(2022, 9, 6, 16, 48, 45, 568000), 
                        ssbLength=42, 
                        addLength=0, 
                        localDataLength=0, 
                        mc7Length=296, 
                        author='', 
                        family='', 
                        name='', 
                        version='10.1', 
                        checksum='0xf3db', 
                        error=''
                    )
                ]
    """
    response = plc.read_block_info(BlockType=BlockType.DB, BlockNumber=1)



    """
    Read area
        example: read area memory of data block 1 with list of items

    Args:
        Area(int)[Required]
        Number(int)[Required]
        Offset(int)[Required]
        Elements(int)[Optional]
        ItemList(list)[Optional]

    Returns:
        list(Tag): list that contains parsed data
            example:
                [
                    Tag(name='BIT', area='DB', number=1, offset=0, value=0, size=1, type=1, error=''), 
                    Tag(name='BYTE', area='DB', number=1, offset=1, value=1, size=1, type=2, error=''), 
                    Tag(name='CHAR', area='DB', number=1, offset=2, value=b'a', size=2, type=3, error=''), 
                    Tag(name='DINT', area='DB', number=1, offset=4, value=1, size=4, type=7, error=''), 
                    Tag(name='DWORD', area='DB', number=1, offset=8, value=1, size=4, type=6, error=''), 
                    ... 
                    Tag(name='WORD', area='DB', number=1, offset=294, value=1, size=2, type=4, error='')
                ]
    """
    response = plc.read_area(Area=Area.DB_DATABLOCKS, Number=1, Offset=0, ItemList=__RTAGS1)



    """
    Write area
        example: write area memory of data block 2 with list of items

    Args:
        Area(int)[Required]
        Number(int)[Required]
        Offset(int)[Required]
        Elements(int)[Optional]
        ItemList(list)[Optional]

    """
    plc.write_area(Area=Area.DB_DATABLOCKS, Number=2, Offset=0, ItemList=__WTAGS2)
```
