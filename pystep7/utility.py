import struct

from datetime import date, datetime, timedelta
from .constants import (
    Area,
    CpuStatus,
    DataType,
    ModeSelector,
    StartupSwitch,
    SubBlockType
)


def BCDtoByte(B:int):
    return ((B >> 4) * 10) + (B & 0x0F)


def ByteToBCD(Value:int):
    return ((Value // 10) << 4) | (Value % 10)


def ByteToNibbles(Value:int):
    Value = Value & 0xFF
    return (Value >> 4, Value & 0x0F)


def DataSizeByte(DT:int) -> int:
    if DT == DataType.BIT: return 1  # S7 sends 1 byte per bit
    elif DT == DataType.BYTE: return 1
    elif DT == DataType.CHAR: return 2 # has terminating char
    elif DT == DataType.INT: return 2
    elif DT == DataType.WORD: return 2
    elif DT == DataType.DINT: return 4
    elif DT == DataType.DWORD: return 4
    elif DT == DataType.REAL: return 4
    elif DT == DataType.STRING: return 256
    elif DT == DataType.COUNTER: return 2
    elif DT == DataType.TIMER: return 2
    elif DT == DataType.S5TIME: return 2
    elif DT == DataType.DATE: return 2
    elif DT == DataType.TIME: return 4
    elif DT == DataType.TIME_OF_DAY: return 4
    elif DT == DataType.DATETIME: return 8
    else: return 0


def GetCpuStatus(Status:int) -> str:
    if Status == CpuStatus.UNKNOWN: return "Unknown"
    elif Status == CpuStatus.RUN: return "Run"
    else: return "Stop"


def GetModeSelector(Value:int) -> str:
    if Value == ModeSelector.RUN: return "Run"
    elif Value == ModeSelector.RUN_P: return "Run Program"
    elif Value == ModeSelector.STOP: return "Stop"
    elif Value == ModeSelector.MRES: return "Memory Reset"
    else: return "Undefined"


def GetStartupSwitchSelector(Value:int) -> str:
    if Value == StartupSwitch.COLD_RESTART: return "Cold Restart"
    elif Value == StartupSwitch.WARM_RESTART: return "Warm Restart"
    else: return "Undefined"


def GetBlockLanguage(Value:int) -> str:
    if Value == 0x01: return "AWL"
    elif Value == 0x02: return "KOP"
    elif Value == 0x03: return "FUP"
    elif Value == 0x04: return "SCL"
    elif Value == 0x05: return "DB"
    elif Value == 0x06: return "GRAPH"
    elif Value == 0x07: return "SDB"
    elif Value == 0x08: return "CPU-DB"                     # DB was created from Plc programm (CREAT_DB)
    elif Value == 0x11: return "SDB (after overall reset)"  # another SDB, don't know what it means, in SDB 1 and SDB 2, uncertain
    elif Value == 0x12: return "SDB (Routing)"              # another SDB, in SDB 999 and SDB 1000 (routing information), uncertain
    elif Value == 0x29: return "Encrypt"                    # block is encrypted with S7-Block-Privacy
    else: return "Undefined"


def GetSubblockType(Value:int) -> str:
    if Value == SubBlockType.OB: return "OB"
    elif Value == SubBlockType.DB: return "DB"
    elif Value == SubBlockType.SDB: return "SDB"
    elif Value == SubBlockType.FC: return "FC"
    elif Value == SubBlockType.SFC: return "SFC"
    elif Value == SubBlockType.FB: return "FB"
    elif Value == SubBlockType.SFB: return "SFB"
    else: return "Undefined"


def GetS5Time(Buffer:bytes, Offset:int=0) -> int:
    multiplier, timeHi = ByteToNibbles(Buffer[Offset+0])
    timeLo = BCDtoByte(Buffer[Offset+1])
    return (10**multiplier)*(timeHi*1000 + timeLo*10)


def SetS5Time(Value:int) -> bytes:
    Value = Value // 10
    sValue = str(Value)
    modLen = len(sValue) - 3
    if modLen > 0:
        expo = 10 ** modLen
        Value = Value // expo
        Value += 1000 * modLen

    return struct.pack(
        f'2s',
        bytearray.fromhex(str(Value).rjust(4, '0'))
    )


def GetTime(Milliseconds:int=0, DaysSince:int=0) -> datetime:
    return datetime(1984, 1, 1) + timedelta(days=DaysSince, milliseconds=Milliseconds)


def SetTime(DT:datetime, endian:str='>') -> bytes:
    if type(DT) != datetime:
        return b'\x00\x00\x00\x00\x00\x00'
    if DT.year < 1984:
        DT.year = 1984

    diff = DT - datetime(1984, 1, 1)
    milliseconds = DT.microsecond // 1000
    days = diff.days

    return struct.pack(f'{endian}IH', milliseconds, days)


def GetDate(DaysSince:int=0) -> date:
    return date(1990, 1, 1) + timedelta(days=DaysSince)


def SetDate(DT:date) -> int:
    if type(DT) != date:
        return 0
    return (DT - date(1990, 1, 1)).days


def GetDateTime(Buffer:bytes, Offset:int=0) -> datetime:
    Year = BCDtoByte(Buffer[Offset+0])
    if (Year < 90):
        Year += 2000
    else:
        Year += 1900

    Month = BCDtoByte(Buffer[Offset+1])
    Day = BCDtoByte(Buffer[Offset+2])
    Hour = BCDtoByte(Buffer[Offset+3])
    Minute = BCDtoByte(Buffer[Offset+4])
    Second = BCDtoByte(Buffer[Offset+5])
    Millisecond = BCDtoByte(Buffer[Offset+6]) * 10 + BCDtoByte(Buffer[Offset+7]) // 10
    try:
        return datetime(Year, Month, Day, Hour, Minute, Second, Millisecond*1000)
    except:
        return datetime(1990, 1, 1)


def SetDateTime(DT:datetime) -> bytes:
    year = DT.year
    if year > 1999:
        year -= 2000
    # shift python (sunday=6) to s7 (sunday=1)
    dow = (DT.weekday() + 1) % 7 + 1
    millisecond = DT.microsecond // 1000
    # first two digits of miliseconds
    # # MSecH = First two digits of miliseconds
    MsecH = millisecond // 10
    # MSecL = Last digit of miliseconds
    MsecL = (millisecond % 10) * 10 + dow

    return struct.pack(
        'BBBBBBBB',
        ByteToBCD(year),
        ByteToBCD(DT.month),
        ByteToBCD(DT.day),
        ByteToBCD(DT.hour),
        ByteToBCD(DT.minute),
        ByteToBCD(DT.second),
        ByteToBCD(MsecH),
        ByteToBCD(MsecL)
    )


# def GetDataType(Value:int) -> str:
#     if Value == DataType.NONE: return "None"
#     elif Value == DataType.OB: return "OB"
#     elif Value == DataType.DB: return "DB"
#     elif Value == DataType.SDB: return "SDB"
#     elif Value == DataType.FC: return "FC"
#     elif Value == DataType.SFC: return "SFC"
#     elif Value == DataType.FB: return "FB"
#     elif Value == DataType.SFB: return "SFB"
#     else: return "Undefined"


def GetAreaName(Value:int) -> str:
    if Value == Area.DATA_RECORD: return "Data Record"
    elif Value == Area.SYSTEM_INFO_200: return "System Info 200"
    elif Value == Area.SYSTEM_FLAGS_200: return "System Flags 200"
    elif Value == Area.ANALOG_INPUT_200: return "Analog Input 200"
    elif Value == Area.ANALOG_OUTPUT_200: return "Analog Output 200"
    elif Value == Area.COUNTER_S7: return "Counter S7"
    elif Value == Area.TIMER_S7: return "Timer S7"
    elif Value == Area.IEC_COUNTER_200: return "IEC Counter 200"
    elif Value == Area.IEC_TIMER_200: return "IEC Timer 200"
    elif Value == Area.DIRECT_ACCESS: return "Direct Access"
    elif Value == Area.PE_INPUTS: return "PE"
    elif Value == Area.PA_OUTPUTS: return "PA"
    elif Value == Area.MK_FLAGS: return "MK"
    elif Value == Area.DB_DATABLOCKS: return "DB"
    elif Value == Area.DI_DB_INSTANCE: return "DI"
    elif Value == Area.LOCAL_DATA: return "Local Data"
    else: return "Undefined"


def GetCpuDiagnostic(Value:int) -> str:
    if Value == 0x113A: return "Start request for cyclic interrupt OB with special handling (S7-300 only)"
    elif Value == 0x1155: return "Status alarm for PROFIBUS DP"
    elif Value == 0x1156: return "Update interrupt for PROFIBUS DP"
    elif Value == 0x1157: return "Manufacturer interrupt for PROFIBUS DP"
    elif Value == 0x1158: return "Status interrupt for PROFINET IO"
    elif Value == 0x1159: return "Update interrupt for PROFINET IO"
    elif Value == 0x115A: return "Manufacturer interrupt for PROFINET IO"
    elif Value == 0x115B: return "IO: Profile-specific interrupt"
    elif Value == 0x116A: return "Technology synchronization interrupt"
    elif Value == 0x1381: return "Request for manual warm restart"
    elif Value == 0x1382: return "Request for automatic warm restart"
    elif Value == 0x1383: return "Request for manual hot restart"
    elif Value == 0x1384: return "Request for automatic hot restart"
    elif Value == 0x1385: return "Request for manual cold restart"
    elif Value == 0x1386: return "Request for automatic cold restart"
    elif Value == 0x1387: return "Master CPU: request for manual cold restart"
    elif Value == 0x1388: return "Master CPU: request for automatic cold restart"
    elif Value == 0x138A: return "Master CPU: request for manual warm restart"
    elif Value == 0x138B: return "Master CPU: request for automatic warm restart"
    elif Value == 0x138C: return "Standby CPU: request for manual hot restart"
    elif Value == 0x138D: return "Standby CPU: request for automatic hot restart"
    elif Value == 0x2521: return "BCD conversion error"
    elif Value == 0x2522: return "Area length error when reading"
    elif Value == 0x2523: return "Area length error when writing"
    elif Value == 0x2524: return "Area error when reading"
    elif Value == 0x2525: return "Area error when writing"
    elif Value == 0x2526: return "Timer number error"
    elif Value == 0x2527: return "Counter number error"
    elif Value == 0x2528: return "Alignment error when reading"
    elif Value == 0x2529: return "Alignment error when writing"
    elif Value == 0x2530: return "Write error when accessing the DB"
    elif Value == 0x2531: return "Write error when accessing the DI"
    elif Value == 0x2532: return "Block number error when opening a DB"
    elif Value == 0x2533: return "Block number error when opening a DI"
    elif Value == 0x2534: return "Block number error when calling an FC"
    elif Value == 0x2535: return "Block number error when calling an FB"
    elif Value == 0x253A: return "DB not loaded"
    elif Value == 0x253C: return "FC not loaded"
    elif Value == 0x253D: return "SFC not loaded"
    elif Value == 0x253E: return "FB not loaded"
    elif Value == 0x253F: return "SFB not loaded"
    elif Value == 0x2942: return "I/O access error, reading"
    elif Value == 0x2943: return "I/O access error, writing"
    elif Value == 0x3267: return "End of module reconfiguration"
    elif Value == 0x3367: return "Start of module reconfiguration"
    elif Value == 0x34A4: return "PROFInet Interface DB can be addressed again"
    elif Value == 0x3501: return "Cycle time exceeded"
    elif Value == 0x3502: return "User interface (OB or FRB) request error"
    elif Value == 0x3503: return "Delay too long processing a priority class"
    elif Value == 0x3505: return "Time-of-day interrupt(s) skipped due to new clock setting"
    elif Value == 0x3506: return "Time-of-day interrupt(s) skipped when changing to RUN after HOLD"
    elif Value == 0x3507: return "Multiple OB request errors caused internal buffer overflow"
    elif Value == 0x3508: return "Synchronous cycle interrupt-timing error"
    elif Value == 0x3509: return "Interrupt loss due to excess interrupt load"
    elif Value == 0x350A: return "Resume RUN mode after CiR"
    elif Value == 0x350B: return "Technology synchronization interrupt - timing error"
    elif Value == 0x3571: return "Nesting depth too high in nesting levels"
    elif Value == 0x3572: return "Nesting depth for Master Control Relays too high"
    elif Value == 0x3573: return "Nesting depth too high after synchronous errors"
    elif Value == 0x3574: return "Nesting depth for block calls (U stack) too high"
    elif Value == 0x3575: return "Nesting depth for block calls (B stack) too high"
    elif Value == 0x3576: return "Local data allocation error"
    elif Value == 0x3578: return "Unknown instruction"
    elif Value == 0x357A: return "Jump instruction to target outside of the block"
    elif Value == 0x3582: return "Memory error detected and corrected by operating system"
    elif Value == 0x3583: return "Accumulation of detected and corrected memo errors"
    elif Value == 0x3585: return "Error in the PC operating system (only for LC RTX)"
    elif Value == 0x3587: return "Multi-bit memory error detected and corrected"
    elif Value == 0x35A1: return "User interface (OB or FRB) not found"
    elif Value == 0x35A2: return "OB not loaded (started by SFC or operating system due to configuration)"
    elif Value == 0x35A3: return "Error when operating system accesses a block"
    elif Value == 0x35A4: return "PROFInet Interface DB cannot be addressed"
    elif Value == 0x35D2: return "Diagnostic entries cannot be sent at present"
    elif Value == 0x35D3: return "Synchronization frames cannot be sent"
    elif Value == 0x35D4: return "Illegal time jump resulting from synchronization"
    elif Value == 0x35D5: return "Error adopting the synchronization time"
    elif Value == 0x35E1: return "Incorrect frame ID in GD"
    elif Value == 0x35E2: return "GD packet status cannot be entered in DB"
    elif Value == 0x35E3: return "Frame length error in GD"
    elif Value == 0x35E4: return "Illegal GD packet number received"
    elif Value == 0x35E5: return "Error accessing DB in communication SFBs for configured S7 connections"
    elif Value == 0x35E6: return "GD total status cannot be entered in DB"
    elif Value == 0x3821: return "BATTF: failure on at least one backup battery of the central rack, problem eliminated"
    elif Value == 0x3822: return "BAF: failure of backup voltage on central rack, problem eliminated"
    elif Value == 0x3823: return "24 volt supply failure on central rack, problem eliminated"
    elif Value == 0x3825: return "BATTF: failure on at least one backup battery of the redundant central rack, problem eliminated"
    elif Value == 0x3826: return "BAF: failure of backup voltage on redundant central rack, problem eliminated"
    elif Value == 0x3827: return "24 volt supply failure on redundant central rack, problem eliminated"
    elif Value == 0x3831: return "BATTF: failure of at least one backup battery of the expansion rack, problem eliminated"
    elif Value == 0x3832: return "BAF: failure of backup voltage on expansion rack, problem eliminated"
    elif Value == 0x3833: return "24 volt supply failure on at least one expansion rack, problem eliminated"
    elif Value == 0x3842: return "Module OK"
    elif Value == 0x3854: return "PROFINET IO interface submodule/submodule and matches the configured interface submodule/submodule"
    elif Value == 0x3855: return "PROFINET IO interface submodule/submodule inserted, but does not match the configured interface submodule/submodule"
    elif Value == 0x3856: return "PROFINET IO interface submodule/submodule inserted, but error in module parameter assignment"
    elif Value == 0x3858: return "PROFINET IO interface submodule access error corrected"
    elif Value == 0x3861: return "Module/interface module inserted, module type OK"
    elif Value == 0x3863: return "Module/interface module plugged in, but wrong module type"
    elif Value == 0x3864: return "Module/interface module plugged in, but causing problem (type ID unreadable)"
    elif Value == 0x3865: return "Module plugged in, but error in module parameter assignment"
    elif Value == 0x3866: return "Module can be addressed again, load voltage error removed"
    elif Value == 0x3881: return "Interface error leaving state"
    elif Value == 0x3884: return "Interface module plugged in"
    elif Value == 0x38B3: return "I/O access error when updating the process image input table"
    elif Value == 0x38B4: return "I/O access error when transferring the process image to the output modules"
    elif Value == 0x38C1: return "Expansion rack operational again (1 to 21), leaving state"
    elif Value == 0x38C2: return "Expansion rack operational again but mismatch between setpoint and actual configuration"
    elif Value == 0x38C4: return "Distributed I/Os: station failure, leaving state"
    elif Value == 0x38C5: return "Distributed I/Os: station fault, leaving state"
    elif Value == 0x38C6: return "Expansion rack operational again, but error(s) in module parameter assignment"
    elif Value == 0x38C7: return "DP: station operational again, but error(s) in module parameter assignment"
    elif Value == 0x38C8: return "DP: station operational again, but mismatch between setpoint and actual configuration"
    elif Value == 0x38CB: return "PROFINET IO station operational again"
    elif Value == 0x38CC: return "PROFINET IO station error corrected"
    elif Value == 0x3921: return "BATTF: failure on at least one backup battery of the central rack"
    elif Value == 0x3922: return "BAF: failure of backup voltage on central rack"
    elif Value == 0x3923: return "24 volt supply failure on central rack"
    elif Value == 0x3925: return "BATTF: failure on at least one backup battery of the redundant central rack"
    elif Value == 0x3926: return "BAF: failure of backup voltage on redundant central rack"
    elif Value == 0x3927: return "24 volt supply failure on redundant central rack"
    elif Value == 0x3931: return "BATTF: failure of at least one backup battery of the expansion rack"
    elif Value == 0x3932: return "BAF: failure of backup voltage on expansion rack"
    elif Value == 0x3933: return "24 volt supply failure on at least one expansion rack"
    elif Value == 0x3942: return "Module error"
    elif Value == 0x3951: return "PROFINET IO submodule removed"
    elif Value == 0x3954: return "PROFINET IO interface submodule/submodule removed"
    elif Value == 0x3961: return "Module/interface module removed, cannot be addressed"
    elif Value == 0x3966: return "Module cannot be addressed, load voltage error"
    elif Value == 0x3968: return "Module reconfiguration has ended with error"
    elif Value == 0x3981: return "Interface error entering state"
    elif Value == 0x3984: return "Interface module removed"
    elif Value == 0x3986: return "Performance of an H-Sync link negatively affected"
    elif Value == 0x39B1: return "I/O access error when updating the process image input table"
    elif Value == 0x39B2: return "I/O access error when transferring the process image to the output modules"
    elif Value == 0x39B3: return "I/O access error when updating the process image input table"
    elif Value == 0x39B4: return "I/O access error when transferring the process image to the output modules"
    elif Value == 0x39C1: return "Expansion rack failure (1 to 21), entering state"
    elif Value == 0x39C3: return "Distributed I/Os: master system failure entering state"
    elif Value == 0x39C4: return "Distributed I/Os: station failure, entering state"
    elif Value == 0x39C5: return "Distributed I/Os: station fault, entering state"
    elif Value == 0x39CA: return "PROFINET IO system failure"
    elif Value == 0x39CB: return "PROFINET IO station failure"
    elif Value == 0x39CC: return "PROFINET IO station error"
    elif Value == 0x39CD: return "PROFINET IO station operational again, but expected configuration does not match actual configuration"
    elif Value == 0x39CE: return "PROFINET IO station operational again, but error(s) in module parameter assignment"
    elif Value == 0x42F3: return "Checksum error detected and corrected by the operating system"
    elif Value == 0x42F4: return "Standby CPU: connection/update via SFC90 is locked in the master CPU"
    elif Value == 0x4300: return "Backed-up power on"
    elif Value == 0x4301: return "Mode transition from STOP to STARTUP"
    elif Value == 0x4302: return "Mode transition from STARTUP to RUN"
    elif Value == 0x4303: return "STOP caused by stop switch being activated"
    elif Value == 0x4304: return "STOP caused by PG STOP operation or by SFB 20 STOP"
    elif Value == 0x4305: return "HOLD: breakpoint reached"
    elif Value == 0x4306: return "HOLD: breakpoint exited"
    elif Value == 0x4307: return "Memory reset started by PG operation"
    elif Value == 0x4308: return "Memory reset started by switch setting"
    elif Value == 0x4309: return "Memory reset started automatically (power on not backed up)"
    elif Value == 0x430A: return "HOLD exited, transition to STOP"
    elif Value == 0x430D: return "STOP caused by other CPU in multicomputing"
    elif Value == 0x430E: return "Memory reset executed"
    elif Value == 0x430F: return "STOP on the module due to STOP on a CPU"
    elif Value == 0x4318: return "Start of CiR"
    elif Value == 0x4319: return "CiR completed"
    elif Value == 0x4357: return "Module watchdog started"
    elif Value == 0x4358: return "All modules are ready for operation"
    elif Value == 0x43B0: return "Firmware update was successful"
    elif Value == 0x43B4: return "Error in firmware fuse"
    elif Value == 0x43B6: return "Firmware updates canceled by redundant modules"
    elif Value == 0x43D3: return "STOP on standby CPU"
    elif Value == 0x43DC: return "Abort during link-up with switchover"
    elif Value == 0x43DE: return "Updating aborted due to monitoring time being exceeded during the n-th attempt, new update attempt initiated"
    elif Value == 0x43DF: return "Updating aborted for final time due to monitoring time being exceeded after completing the maximum amount of attempts. User intervention required"
    elif Value == 0x43E0: return "Change from solo mode after link-up"
    elif Value == 0x43E1: return "Change from link-up after updating"
    elif Value == 0x43E2: return "Change from updating to redundant mode"
    elif Value == 0x43E3: return "Master CPU: change from redundant mode to solo mode"
    elif Value == 0x43E4: return "Standby CPU: change from redundant mode after error-search mode"
    elif Value == 0x43E5: return "Standby CPU: change from error-search mode after link-up or STOP"
    elif Value == 0x43E6: return "Link-up aborted on the standby CPU"
    elif Value == 0x43E7: return "Updating aborted on the standby CPU"
    elif Value == 0x43E8: return "Standby CPU: change from link-up after startup"
    elif Value == 0x43E9: return "Standby CPU: change from startup after updating"
    elif Value == 0x43F1: return "Reserve-master switchover"
    elif Value == 0x43F2: return "Coupling of incompatible H-CPUs blocked by system program"
    elif Value == 0x4510: return "STOP violation of the CPU's data range"
    elif Value == 0x4520: return "DEFECTIVE: STOP not possible"
    elif Value == 0x4521: return "DEFECTIVE: failure of instruction processing processor"
    elif Value == 0x4522: return "DEFECTIVE: failure of clock chip"
    elif Value == 0x4523: return "DEFECTIVE: failure of clock pulse generator"
    elif Value == 0x4524: return "DEFECTIVE: failure of timer update function"
    elif Value == 0x4525: return "DEFECTIVE: failure of multicomputing synchronization"
    elif Value == 0x4527: return "DEFECTIVE: failure of I/O access monitoring"
    elif Value == 0x4528: return "DEFECTIVE: failure of scan time monitoring"
    elif Value == 0x4530: return "DEFECTIVE: memory test error in internal memory"
    elif Value == 0x4532: return "DEFECTIVE: failure of core resources"
    elif Value == 0x4536: return "DEFECTIVE: switch defective"
    elif Value == 0x4540: return "STOP: Memory expansion of the internal work memory has gaps. First memory expansion too small or missing"
    elif Value == 0x4541: return "STOP caused by priority class system"
    elif Value == 0x4542: return "STOP caused by object management system"
    elif Value == 0x4543: return "STOP caused by test functions"
    elif Value == 0x4544: return "STOP caused by diagnostic system"
    elif Value == 0x4545: return "STOP caused by communication system"
    elif Value == 0x4546: return "STOP caused by CPU memory management"
    elif Value == 0x4547: return "STOP caused by process image management"
    elif Value == 0x4548: return "STOP caused by I/O management"
    elif Value == 0x454A: return "STOP caused by configuration: an OB deselected with STEP 7 was being loaded into the CPU during STARTUP"
    elif Value == 0x4550: return "DEFECTIVE: internal system error"
    elif Value == 0x4555: return "No restart possible, monitoring time elapsed"
    elif Value == 0x4556: return "STOP: memory reset request from communication system / due to data inconsistency"
    elif Value == 0x4562: return "STOP caused by programming error (OB not loaded or not possible)"
    elif Value == 0x4563: return "STOP caused by I/O access error (OB not loaded or not possible)"
    elif Value == 0x4567: return "STOP caused by H event"
    elif Value == 0x4568: return "STOP caused by time error (OB not loaded or not possible)"
    elif Value == 0x456A: return "STOP caused by diagnostic interrupt (OB not loaded or not possible)"
    elif Value == 0x456B: return "STOP caused by removing/inserting module (OB not loaded or not possible)"
    elif Value == 0x456C: return "STOP caused by CPU hardware error (OB not loaded or not possible, or no FRB)"
    elif Value == 0x456D: return "STOP caused by program sequence error (OB not loaded or not possible)"
    elif Value == 0x456E: return "STOP caused by communication error (OB not loaded or not possible)"
    elif Value == 0x456F: return "STOP caused by rack failure OB (OB not loaded or not possible)"
    elif Value == 0x4570: return "STOP caused by process interrupt (OB not loaded or not possible)"
    elif Value == 0x4571: return "STOP caused by nesting stack error"
    elif Value == 0x4572: return "STOP caused by master control relay stack error"
    elif Value == 0x4573: return "STOP caused by exceeding the nesting depth for synchronous errors"
    elif Value == 0x4574: return "STOP caused by exceeding interrupt stack nesting depth in the priority class stack"
    elif Value == 0x4575: return "STOP caused by exceeding block stack nesting depth in the priority class stack"
    elif Value == 0x4576: return "STOP caused by error when allocating the local data"
    elif Value == 0x4578: return "STOP caused by unknown opcode"
    elif Value == 0x457A: return "STOP caused by code length error"
    elif Value == 0x457B: return "STOP caused by DB not being loaded on on-board I/Os"
    elif Value == 0x457D: return "Reset/clear request because the version of the internal interface to the integrated technology was changed"
    elif Value == 0x457F: return "STOP caused by STOP command"
    elif Value == 0x4580: return "STOP: back-up buffer contents inconsistent (no transition to RUN)"
    elif Value == 0x4590: return "STOP caused by overloading the internal functions"
    elif Value == 0x45D5: return "LINK-UP rejected due to mismatched CPU memory configuration of the sub-PLC"
    elif Value == 0x45D6: return "LINK-UP rejected due to mismatched system program of the sub-PLC"
    elif Value == 0x45D8: return "DEFECTIVE: hardware fault detected due to other error"
    elif Value == 0x45D9: return "STOP due to SYNC module error"
    elif Value == 0x45DA: return "STOP due to synchronization error between H CPUs"
    elif Value == 0x45DD: return "LINK-UP rejected due to running test or other online functions"
    elif Value == 0x4926: return "DEFECTIVE: failure of the watchdog for I/O access"
    elif Value == 0x4931: return "STOP or DEFECTIVE: memory test error in memory submodule"
    elif Value == 0x4933: return "Checksum error"
    elif Value == 0x4934: return "DEFECTIVE: memory not available"
    elif Value == 0x4935: return "DEFECTIVE: cancelled by watchdog/processor exceptions"
    elif Value == 0x4949: return "STOP caused by continuous hardware interrupt"
    elif Value == 0x494D: return "STOP caused by I/O error"
    elif Value == 0x494E: return "STOP caused by power failure"
    elif Value == 0x494F: return "STOP caused by configuration error"
    elif Value == 0x4959: return "One or more modules not ready for operation"
    elif Value == 0x497C: return "STOP caused by integrated technology"
    elif Value == 0x49A0: return "STOP caused by parameter assignment error or non-permissible variation of setpoint and actual extension: Start-up blocked"
    elif Value == 0x49A1: return "STOP caused by parameter assignment error: memory reset request"
    elif Value == 0x49A2: return "STOP caused by error in parameter modification: startup disabled"
    elif Value == 0x49A3: return "STOP caused by error in parameter modification: memory reset request"
    elif Value == 0x49A4: return "STOP: inconsistency in configuration data"
    elif Value == 0x49A5: return "STOP: distributed I/Os: inconsistency in the loaded configuration information"
    elif Value == 0x49A6: return "STOP: distributed I/Os: invalid configuration information"
    elif Value == 0x49A7: return "STOP: distributed I/Os: no configuration information"
    elif Value == 0x49A8: return "STOP: error indicated by the interface module for the distributed I/Os"
    elif Value == 0x49B1: return "Firmware update data incorrect"
    elif Value == 0x49B2: return "Firmware update: hardware version does not match firmware"
    elif Value == 0x49B3: return "Firmware update: module type does not match firmware"
    elif Value == 0x49D0: return "LINK-UP aborted due to violation of coordination rules"
    elif Value == 0x49D1: return "LINK-UP/UPDATE sequence aborted"
    elif Value == 0x49D2: return "Standby CPU changed to STOP due to STOP on the master CPU during link-up"
    elif Value == 0x49D4: return "STOP on a master, since partner CPU is also a master (link-up error)"
    elif Value == 0x49D7: return "LINK-UP rejected due to change in user program or in configuration"
    elif Value == 0x510F: return "A problem as occurred with WinLC. This problem has caused the CPU to go into STOP mode or has caused a fault in the CPU"
    elif Value == 0x530D: return "New startup information in the STOP mode"
    elif Value == 0x5311: return "Startup despite Not Ready message from module(s)"
    elif Value == 0x5371: return "Distributed I/Os: end of the synchronization with a DP master"
    elif Value == 0x5380: return "Diagnostic buffer entries of interrupt and asynchronous errors disabled"
    elif Value == 0x5395: return "Distributed I/Os: reset of a DP master"
    elif Value == 0x53A2: return "Download of technology firmware successful"
    elif Value == 0x53A4: return "Download of technology DB not successful"
    elif Value == 0x53FF: return "Reset to factory setting"
    elif Value == 0x5445: return "Start of System reconfiguration in RUN mode"
    elif Value == 0x5481: return "All licenses for runtime software are complete again"
    elif Value == 0x5498: return "No more inconsistency with DP master systems due to CiR"
    elif Value == 0x5545: return "Start of System reconfiguration in RUN mode"
    elif Value == 0x5581: return "One or several licenses for runtime software are missing"
    elif Value == 0x558A: return "Difference between the MLFB of the configured and inserted CPU"
    elif Value == 0x558B: return "Difference in the firmware version of the configured and inserted CPU"
    elif Value == 0x5598: return "Start of possible inconsistency with DP master systems due to CiR"
    elif Value == 0x55A5: return "Version conflict: internal interface with integrated technology"
    elif Value == 0x55A6: return "The maximum number of technology objects has been exceeded"
    elif Value == 0x55A7: return "A technology DB of this type is already present"
    elif Value == 0x5879: return "Diagnostic message from DP interface: EXTF LED off"
    elif Value == 0x5960: return "Parameter assignment error when switching"
    elif Value == 0x5961: return "Parameter assignment error"
    elif Value == 0x5962: return "Parameter assignment error preventing startup"
    elif Value == 0x5963: return "Parameter assignment error with memory reset request"
    elif Value == 0x5966: return "Parameter assignment error when switching"
    elif Value == 0x5969: return "Parameter assignment error with startup blocked"
    elif Value == 0x596A: return "PROFINET IO: IP address of an IO device already present"
    elif Value == 0x596B: return "IP address of an Ethernet interface already exists"
    elif Value == 0x596C: return "Name of an Ethernet interface already exists"
    elif Value == 0x596D: return "The existing network configuration does not mach the system requirements or configuration"
    elif Value == 0x5979: return "Diagnostic message from DP interface: EXTF LED on"
    elif Value == 0x597C: return "DP Global Control command failed or moved"
    elif Value == 0x59A0: return "The interrupt can not be associated in the CPU"
    elif Value == 0x59A1: return "Configuration error in the integrated technology"
    elif Value == 0x59A3: return "Error when downloading the integrated technology"
    elif Value == 0x6253: return "Firmware update: End of firmware download over the network"
    elif Value == 0x6316: return "Interface error when starting programmable controller"
    elif Value == 0x6353: return "Firmware update: Start of firmware download over the network"
    elif Value == 0x6390: return "Formatting of Micro Memory Card complete"
    elif Value == 0x6500: return "Connection ID exists twice on module"
    elif Value == 0x6501: return "Connection resources inadequate"
    elif Value == 0x6502: return "Error in the connection description"
    elif Value == 0x6510: return "CFB structure error detected in instance DB when evaluating EPROM"
    elif Value == 0x6514: return "GD packet number exists twice on the module"
    elif Value == 0x6515: return "Inconsistent length specifications in GD configuration information"
    elif Value == 0x6521: return "No memory submodule and no internal memory available"
    elif Value == 0x6522: return "Illegal memory submodule: replace submodule and reset memory"
    elif Value == 0x6523: return "Memory reset request due to error accessing submodule"
    elif Value == 0x6524: return "Memory reset request due to error in block header"
    elif Value == 0x6526: return "Memory reset request due to memory replacement"
    elif Value == 0x6527: return "Memory replaced, therefore restart not possible"
    elif Value == 0x6528: return "Object handling function in the STOP/HOLD mode, no restart possible"
    elif Value == 0x6529: return "No startup possible during the \"load user program\" function"
    elif Value == 0x652A: return "No startup because block exists twice in user memory"
    elif Value == 0x652B: return "No startup because block is too long for submodule - replace submodule"
    elif Value == 0x652C: return "No startup due to illegal OB on submodule"
    elif Value == 0x6532: return "No startup because illegal configuration information on submodule"
    elif Value == 0x6533: return "Memory reset request because of invalid submodule content"
    elif Value == 0x6534: return "No startup: block exists more than once on submodule"
    elif Value == 0x6535: return "No startup: not enough memory to transfer block from submodule"
    elif Value == 0x6536: return "No startup: submodule contains an illegal block number"
    elif Value == 0x6537: return "No startup: submodule contains a block with an illegal length"
    elif Value == 0x6538: return "Local data or write-protection ID (for DB) of a block illegal for CPU"
    elif Value == 0x6539: return "Illegal command in block (detected by compiler)"
    elif Value == 0x653A: return "Memory reset request because local OB data on submodule too short"
    elif Value == 0x6543: return "No startup: illegal block type"
    elif Value == 0x6544: return "No startup: attribute \"relevant for processing\" illegal"
    elif Value == 0x6545: return "Source language illegal"
    elif Value == 0x6546: return "Maximum amount of configuration information reached"
    elif Value == 0x6547: return "Parameter assignment error assigning parameters to modules (not on P bus, cancel download)"
    elif Value == 0x6548: return "Plausibility error during block check"
    elif Value == 0x6549: return "Structure error in block"
    elif Value == 0x6550: return "A block has an error in the CRC"
    elif Value == 0x6551: return "A block has no CRC"
    elif Value == 0x6560: return "SCAN overflow"
    elif Value == 0x6805: return "Resource problem on configured connections, eliminated"
    elif Value == 0x6881: return "Interface error leaving state"
    elif Value == 0x6905: return "Resource problem on configured connections"
    elif Value == 0x6981: return "Interface error entering state"
    elif Value == 0x72A2: return "Failure of a DP master or a DP master system"
    elif Value == 0x72A3: return "Redundancy restored on the DP slave"
    elif Value == 0x72DB: return "Safety program: safety mode disabled"
    elif Value == 0x72E0: return "Loss of redundancy in communication, problem eliminated"
    elif Value == 0x7301: return "Loss of redundancy (1 of 2) due to failure of a CPU"
    elif Value == 0x7302: return "Loss of redundancy (1 of 2) due to STOP on the standby triggered by user"
    elif Value == 0x7303: return "H system (1 of 2) changed to redundant mode"
    elif Value == 0x7323: return "Discrepancy found in operating system data"
    elif Value == 0x7331: return "Standby-master switchover due to master failure"
    elif Value == 0x7333: return "Standby-master switchover due to system modification during runtime"
    elif Value == 0x7334: return "Standby-master switchover due to communication error at the synchronization module"
    elif Value == 0x7340: return "Synchronization error in user program due to elapsed wait time"
    elif Value == 0x7341: return "Synchronization error in user program due to waiting at different synchronization points"
    elif Value == 0x7342: return "Synchronization error in operating system due to waiting at different synchronization points"
    elif Value == 0x7343: return "Synchronization error in operating system due to elapsed wait time"
    elif Value == 0x7344: return "Synchronization error in operating system due to incorrect data"
    elif Value == 0x734A: return "The \"Re-enable\" job triggered by SFC 90 \"H_CTRL\" was executed"
    elif Value == 0x73A3: return "Loss of redundancy on the DP slave"
    elif Value == 0x73C1: return "Update process canceled"
    elif Value == 0x73C2: return "Updating aborted due to monitoring time being exceeded during the n-th attempt (1 = n = max. possible number of update attempts after abort due to excessive monitoring time)"
    elif Value == 0x73D8: return "Safety mode disabled"
    elif Value == 0x73DB: return "Safety program: safety mode enabled"
    elif Value == 0x73E0: return "Loss of redundancy in communication"
    elif Value == 0x74DD: return "Safety program: Shutdown of a fail-save runtime group disabled"
    elif Value == 0x74DE: return "Safety program: Shutdown of the F program disabled"
    elif Value == 0x74DF: return "Start of F program initialization"
    elif Value == 0x7520: return "Error in RAM comparison"
    elif Value == 0x7521: return "Error in comparison of process image output value"
    elif Value == 0x7522: return "Error in comparison of memory bits, timers, or counters"
    elif Value == 0x75D1: return "Safety program: Internal CPU error"
    elif Value == 0x75D2: return "Safety program error: Cycle time time-out"
    elif Value == 0x75D6: return "Data corrupted in safety program prior to the output to F I/O"
    elif Value == 0x75D7: return "Data corrupted in safety program prior to the output to partner F-CPU"
    elif Value == 0x75D9: return "Invalid REAL number in a DB"
    elif Value == 0x75DA: return "Safety program: Error in safety data format"
    elif Value == 0x75DC: return "Runtime group, internal protocol error"
    elif Value == 0x75DD: return "Safety program: Shutdown of a fail-save runtime group enabled"
    elif Value == 0x75DE: return "Safety program: Shutdown of the F program enabled"
    elif Value == 0x75DF: return "End of F program initialization"
    elif Value == 0x75E1: return "Safety program: Error in FB \"F_PLK\" or \"F_PLK_O\" or \"F_CYC_CO\" or \"F_TEST\" or \"F_TESTC\""
    elif Value == 0x75E2: return "Safety program: Area length error"
    elif Value == 0x7852: return "SYNC module inserted"
    elif Value == 0x7855: return "SYNC module eliminated"
    elif Value == 0x78D3: return "Communication error between PROFIsafe and F I/O"
    elif Value == 0x78D4: return "Error in safety relevant communication between F CPUs"
    elif Value == 0x78D5: return "Error in safety relevant communication between F CPUs"
    elif Value == 0x78E3: return "F-I/O device input channel depassivated"
    elif Value == 0x78E4: return "F-I/O device output channel depassivated"
    elif Value == 0x78E5: return "F-I/O device depassivated"
    elif Value == 0x7934: return "Standby-master switchover due to connection problem at the SYNC module"
    elif Value == 0x7950: return "Synchronization module missing"
    elif Value == 0x7951: return "Change at the SYNC module without Power On"
    elif Value == 0x7952: return "SYNC module removed"
    elif Value == 0x7953: return "Change at the SYNC-module without reset"
    elif Value == 0x7954: return "SYNC module: rack number assigned twice"
    elif Value == 0x7955: return "SYNC module error"
    elif Value == 0x7956: return "Illegal rack number set on SYNC module"
    elif Value == 0x7960: return "Redundant I/O: Time-out of discrepancy time at digital input, error is not yet localized"
    elif Value == 0x7961: return "Redundant I/O, digital input error: Signal change after expiration of the discrepancy time"
    elif Value == 0x7962: return "Redundant I/O: Digital input error"
    elif Value == 0x796F: return "Redundant I/O: The I/O was globally disabled"
    elif Value == 0x7970: return "Redundant I/O: Digital output error"
    elif Value == 0x7980: return "Redundant I/O: Time-out of discrepancy time at analog input"
    elif Value == 0x7981: return "Redundant I/O: Analog input error"
    elif Value == 0x7990: return "Redundant I/O: Analog output error"
    elif Value == 0x79D3: return "Communication error between PROFIsafe and F I/O"
    elif Value == 0x79D4: return "Error in safety relevant communication between F CPUs"
    elif Value == 0x79D5: return "Error in safety relevant communication between F CPUs"
    elif Value == 0x79E3: return "F-I/O device input channel passivated"
    elif Value == 0x79E4: return "F-I/O device output channel passivated"
    elif Value == 0x79E5: return "F-I/O device passivated"
    elif Value == 0x79E6: return "Inconsistent safety program"
    elif Value == 0x79E7: return "Simulation block (F system block) loaded"
    else: return "Undefined"


def GetCpuLed(Value:int) -> str:
    if Value == 0x0001: return "SF (group error)"
    elif Value == 0x0002: return "INTF (internal error)"
    elif Value == 0x0003: return "EXTF (external error)"
    elif Value == 0x0004: return "RUN"
    elif Value == 0x0005: return "STOP"
    elif Value == 0x0006: return "FRCE (force)"
    elif Value == 0x0007: return "CRST (cold restart)"
    elif Value == 0x0008: return "BAF (battery fault/overload, short circuit of battery voltage on bus)"
    elif Value == 0x0009: return "USR (user-defined)"
    elif Value == 0x000a: return "USR1 (user-defined)"
    elif Value == 0x000b: return "BUS1F (bus error interface 1)"
    elif Value == 0x000c: return "BUS2F (bus error interface 2)"
    elif Value == 0x000d: return "REDF (redundancy error)"
    elif Value == 0x000e: return "MSTR (master)"
    elif Value == 0x000f: return "RACK0 (rack number 0)"
    elif Value == 0x0010: return "RACK1 (rack number 1)"
    elif Value == 0x0011: return "RACK2 (rack number 2)"
    elif Value == 0x0012: return "IFM1F (interface error interface module 1)"
    elif Value == 0x0013: return "IFM2F (interface error interface module 2)"
    elif Value == 0x0014: return "BUS3F (bus error interface 3)"
    elif Value == 0x0015: return "MAINT (maintenance demand)"
    elif Value == 0x0016: return "DC24V"
    elif Value == 0x0080: return "IF (init failure)"
    elif Value == 0x0081: return "UF (user failure)"
    elif Value == 0x0082: return "MF (monitoring failure)"
    elif Value == 0x0083: return "CF (communication failure)"
    elif Value == 0x0084: return "TF (task failure)"
    elif Value == 0x00ec: return "APPL_STATE_RED"
    elif Value == 0x00ed: return "APPL_STATE_GREEN"
    else: return "Undefined"
