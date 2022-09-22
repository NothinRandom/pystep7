"""
This file implements Step7 Communication client.
"""


import logging
import socket
import struct

from datetime import datetime
from . import constants as const
from . import utility as util
from .exceptions import (
    CommTypeError,
    DataTypeError,
    ErrorClass,
    ErrorCode,
    ReturnCode
)
from .tag import (
    BlockInfo,
    CatalogCode,
    CommProc,
    CPUDiagnostics,
    CPUInfo,
    CPULed,
    CPUStatus,
    Protection,
    Tag
)

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s %(message)s',
    handlers=[
        #logging.FileHandler("output.log"),
        logging.StreamHandler()
    ]
)

class Client:
    """
    Step7 Communication class.

    Attributes:
        plc_type(str):          connect PLC type. "Q", "L", "QnA", "iQ-L", "iQ-R"
        comm_type(str):         communication type. "binary" or "ascii". (Default: "binary") 
        subheader(int):         Subheader for Step7 Communication
        network(int):           network No. of an access target. (0<= network <= 255)
        pc(int):                network module station No. of an access target. (0<= pc <= 255)
        dest_moduleio(int):     When accessing a multidrop connection station via network, 
                                specify the start input/output number of a multidrop connection source module.
                                the CPU module of the multiple CPU system and redundant system.
        dest_modulesta(int):    accessing a multidrop connection station via network, 
                                specify the station No. of aaccess target module
        timer(int):             time to raise Timeout error(/250msec). default=4(1sec)
                                If PLC elapsed this time, PLC returns Timeout response.
                                Note: python socket timeout is always set timer+1sec. To recieve Timeout response.
    """

    LocalTSAP = 0x0100
    LocalTSAP_HI = 0
    LocalTSAP_LO = 0
    RemoteTSAP_HI = 0
    RemoteTSAP_LO = 0

    _pdu_length = 0
    _PduSizeRequested = 480

    ConnType        = const.ClientConnectionType.PG
    sock_timeout    = 2 # in seconds
    _tcp_connected  = False
    _iso_connected  = False
    _pdu_negotiated = False
    _SOCKBUFSIZE    = 4096
    cpu_info        = CPUInfo()
    controller      = 1500 # S7-300, S7-400, S7-1500, etc

    endian          = const.Endian.big
    cache_data      = {}

    __log = logging.getLogger(f"{__module__}.{__qualname__}")


    def __init__(self, host:str, port:int=102, rack:int=0, slot:int=0):
        """
        Constructor
        """

        # specify host and port
        self.host = host
        self.port = port
        self.rack = rack
        self.slot = slot
        self.RemoteTSAP = (self.ConnType << 8) + (self.rack * 0x20) + self.slot


    def __enter__(self):
        """
        Used by with statement: https://peps.python.org/pep-0343/
        Does a 2 stage TCP and ISO connect
        """
        self.TCPConnect(ip=self.host, port=self.port)
        self.SetConnectionParams(LocalTSAP=self.LocalTSAP, RemoteTSAP=self.RemoteTSAP)
        self.ISOConnect()
        self.NegotiatePduLength()
        self.cpu_info = self.read_cpu_info()
        self.controller = int(self.cpu_info.systemName.split("/")[0][2:])
        return self


    # used by with statement
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Used by with statement: https://peps.python.org/pep-0343/
        """

        try:
            self.close()
        except:
            self.__log.exception("Error closing connection.")
            return False
        else:
            if not exc_type:
                return True
            self.__log.exception("Unhandled Client Error", exc_info=(exc_type, exc_val, exc_tb))
            return False


    def set_debug(self, enable:bool=False):
        """
        Set debug mode
        """
        if enable:
            self.__log.setLevel(logging.DEBUG)
        else:
            self.__log.setLevel(logging.ERROR)


    def TCPConnect(self, ip:str, port:int):
        """
        Connect to PLC.

        Args:
            ip (str):           ip address(IPV4) to connect PLC
            port (int):         port number of connect PLC   
            timeout (float):    timeout second in communication
        """

        self._ip = ip
        self._port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(self.sock_timeout)
        try:
            self._sock.connect((ip, port))
            self._tcp_connected = True
        except socket.timeout:
            self.__log.error(f"self.TCPConnect(): {str(socket.timeout)}")
        

    def close(self):
        """
        Close connection.
        """

        self._sock.close()
        self._tcp_connected = self._iso_connected = self._pdu_negotiated = False


    def _TCPSend(self, send_data:bytes):
        """
        Send data 

        Args:
            send_data(bytes): Step7 Communication data
        """

        if self._tcp_connected:
            self.__log.debug(f'self._TCPSend(): \n{send_data.hex()}')
            try:
                self._sock.send(send_data)
            except socket.timeout:
                self.__log.error(f"self._TCPSend(): {str(socket.timeout)}")
        else:
            self.__log.error(f"self._TCPSend(): Socket is not connected. Please use connect method")
            raise CommTypeError("Socket is not connected. Please use connect method")


    def _ISOSend(self, send_data:bytes):
        """
        Send data 

        Args:
            send_data(bytes): Step7 Communication data
        """

        if self._tcp_connected and self._iso_connected:
            self.__log.debug(f'self._ISOSend(): \n{send_data.hex()}')
            try:
                self._sock.send(send_data)
            except socket.timeout:
                self.__log.error(f"self._ISOSend(): {str(socket.timeout)}")
        else:
            self.__log.error(f"self._ISOSend(): Socket is not connected. Please use connect method")
            raise CommTypeError("Socket is not connected. Please use connect method")


    def _send(self, send_data:bytes):
        """
        Send data 

        Args:
            send_data(bytes): Step7 Communication data
        """

        if self._tcp_connected and self._iso_connected and self._pdu_negotiated:
            self.__log.debug(f'self._send(): \n{send_data.hex()}')
            try:
                self._sock.send(send_data)
            except socket.timeout:
                self.__log.error(f"self._send(): {str(socket.timeout)}")
        else:
            self.__log.error(f"self._send(): ISO COTP is not set up.")
            raise CommTypeError("ISO COTP is not set up.")


    def _recv(self):
        """
        Receive data

        Returns:
            data(bytes)
        """
        data = bytes()
        try:
            data = self._sock.recv(self._SOCKBUFSIZE)
        except socket.timeout:
            self.__log.error(f"self._recv(): {str(socket.timeout)}")
        return data


    def SetConnectionParams(self, LocalTSAP:int, RemoteTSAP:int):
        LocTSAP = LocalTSAP & 0x0000FFFF
        RemTSAP = RemoteTSAP & 0x0000FFFF
        self.LocalTSAP_HI = LocTSAP >> 8
        self.LocalTSAP_LO = (LocTSAP & 0x00FF)
        self.RemoteTSAP_HI = (RemTSAP >> 8)
        self.RemoteTSAP_LO = (RemTSAP & 0x00FF)


    def ISOConnect(self):
        # connection request
        request = const.ISO_CR
        request[16] = self.LocalTSAP_HI
        request[17] = self.LocalTSAP_LO
        request[20] = self.RemoteTSAP_HI
        request[21] = self.RemoteTSAP_LO
        self._TCPSend(send_data=bytes(request))
        data = self._recv()
        length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
        self._iso_connected = False
        if (length == 22):
            PDUType = struct.unpack_from('B', data, 5)[0]
            if (PDUType != const.COTP.CONNECT_CONFIRM):
                self.__log.error(f"self.ISOConnect(): Failed to perform ISO connect")
                raise CommTypeError("Failed to perform ISO connect")
            else:
                self._iso_connected = True
        else:
            self.__log.error(f"self.ISOConnect(): Invalid PDU")
            raise CommTypeError("Invalid PDU")


    def NegotiatePduLength(self):
        """
        ROSCTR:Job:Function:Setup Communication
        ROSCTR:Ack_Data:Function:Setup Communication
        """

        # Set PDU Size Requested
        request = bytearray(const.S7_PN)
        struct.pack_into(f'{self.endian}H', request, 23, self._PduSizeRequested)
        # Sends the connection request telegram
        self._ISOSend(send_data=request)
        data = self._recv()
        length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
        headerErrorClass, headerErrorCode = struct.unpack_from('BB', data, 17)
        self._pdu_negotiated = False
        # check S7 Error
        if (length == 27 
            and headerErrorClass == const.ErrorClass.NO_ERROR
            and headerErrorCode == 0x00
        ):
            # Get PDU Size Negotiated
            self._pdu_length = struct.unpack_from(f'{self.endian}H', data, 25)[0]
            if (self._pdu_length > 0):
                self._pdu_negotiated = True
            else:
                self.__log.error(f"self.NegotiatePduLength(): Unable to negotiate PDU")
                raise CommTypeError("Unable to negotiate PDU")
        else:
            self.__log.error(f"self.NegotiatePduLength(): Unable to negotiate PDU")
            raise CommTypeError("Unable to negotiate PDU")


    def SetConnectionType(self, ConnectionType:int):
        self.ConnType = ConnectionType


    def read_plc_time(self) -> datetime:
        """
        Read PLC time.

        Returns:
            datetime:   datetime object of PLC
        """

        request = bytes(const.S7_GET_CLOCK)
        self._send(send_data=request)
        data = self._recv()

        length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
        if (length > 30):  # the minimum expected
            paramErrorCode, dataReturnCode = struct.unpack_from(f'{self.endian}HB', data, 27)
            if (paramErrorCode == const.ParamErrorCode.NO_ERROR 
                and dataReturnCode == const.ReturnCode.SUCCESS
            ):
                # year1 = util.BCDtoByte(data[34])
                return util.GetDateTime(Buffer=data, Offset=35)
            else:
                self.__log.error(f"self.read_plc_time(): {ErrorCode(paramErrorCode)}")
                raise ErrorCode(paramErrorCode)
        else:
            self.__log.error(f"self.read_plc_time(): Invalid PDU size")
            raise CommTypeError("Invalid PDU size")


    def sync_plc_time(self, utc:bool=False) -> datetime:
        """
        Sync PLC time to host time.

        Args:
            utc(bool):   use UTC time (True) or local time (False)
        """

        now = datetime.utcnow() if utc else datetime.now()

        return self.set_plc_time(dt=now)


    def set_plc_time(self, dt:datetime) -> str:
        """
        Set PLC time by specifying datetime object.

        Args:
            dt(datetime):   datetime object (e.g. datetime.now())
        """

        request = bytearray(const.S7_SET_CLOCK)
        struct.pack_into('8s', request, 31, util.SetDateTime(DT=dt))

        self._send(send_data=request)
        data = self._recv()

        length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
        if (length > 30): # the minimum expected
            paramErrorCode = struct.unpack_from(f'{self.endian}H', data, 27)[0]
            if (paramErrorCode != const.ParamErrorCode.NO_ERROR):
                self.__log.error(f"self.set_plc_time(): Invalid Response")
                raise CommTypeError("Invalid Response")
        else:
            self.__log.error(f"self.set_plc_time(): Invalid PDU size")
            raise CommTypeError("Invalid PDU size")
        return f"{dt}"


    def read_cpu_status(self) -> CPUStatus:
        """
        Read CPU model.

        Returns:
            CPUStatus(NamedTuple): (requestedMode(str), previousMode(str), error(str))
        """

        request = bytearray(const.S7_SZL_FIRST)
        struct.pack_into(f'{self.endian}H', request, 29, const.SystemStateList.CPU_STATUS)

        self._send(send_data=request)
        data = self._recv()

        cpuStatus = CPUStatus()
        length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
        if (length > 30): # the minimum expected
            paramErrorCode = struct.unpack_from(f'{self.endian}H', data, 27)[0]
            if (paramErrorCode == const.ParamErrorCode.NO_ERROR):
                status = struct.unpack_from('B', data, 44)[0]
                hiNib, loNib = util.ByteToNibbles(status)
                cpuStatus = cpuStatus._replace(
                    requestedMode=util.GetCpuStatus(Status=loNib),
                    previousMode=util.GetCpuStatus(Status=hiNib)
                )
            else:
                self.__log.error(f"self.read_cpu_status(): {ErrorCode(paramErrorCode)}")
                raise ErrorCode(paramErrorCode)
        else:
            self.__log.error(f"self.read_cpu_status(): Invalid PDU size")
            raise CommTypeError("Invalid PDU size")
        return cpuStatus


    def read_catalog_code(self) -> CatalogCode:
        catalogCode = CatalogCode()

        request = bytearray(const.S7_SZL_FIRST)
        struct.pack_into(f'{self.endian}H', request, 29, const.SystemStateList.CATALOG_CODE)

        self._send(send_data=request)
        data = self._recv()

        length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
        if (length > 30): # the minimum expected
            paramErrorCode, dataReturnCode = struct.unpack_from(f'{self.endian}HB', data, 27)
            if (paramErrorCode == const.ParamErrorCode.NO_ERROR 
                and dataReturnCode == const.ReturnCode.SUCCESS
            ):
                offset = 37
                sectionLength, szlCount = struct.unpack_from(f'{self.endian}HH', data, offset)
                offset += 4
                for item in range(szlCount):
                    (
                        index, 
                        mlfb, 
                        bgtype, 
                        ausbg, 
                        ausbe
                    ) = struct.unpack_from(f'{self.endian}H20sHHH', data, offset)
                    offset += sectionLength
                    mlfb = mlfb.decode().strip()
                    if index == 0x0001:
                        catalogCode = catalogCode._replace(moduleOrderNumber=mlfb)
                        catalogCode = catalogCode._replace(moduleVersion=f"{ausbg}.{ausbe}")
                    elif index == 0x0006:
                        catalogCode = catalogCode._replace(basicHardwareId=mlfb)
                        catalogCode = catalogCode._replace(hardwareVersion=f"{ausbg}.{ausbe}")
                    elif index == 0x0007:
                        catalogCode = catalogCode._replace(basicFirmwareId=mlfb)
                        catalogCode = catalogCode._replace(firmwareVersion=f"{ausbg}.{ausbe}")
                    elif index == 0x0081:
                        catalogCode = catalogCode._replace(firmwareExtensionId=mlfb)
                        catalogCode = catalogCode._replace(firmwareExtVersion=f"{ausbg}.{ausbe}")
            else:
                self.__log.error(f"self.read_catalog_code(): {ErrorCode(paramErrorCode)}")
                raise ErrorCode(paramErrorCode)
        else:
            self.__log.error(f"self.read_catalog_code(): Invalid PDU size")
            raise CommTypeError("Invalid PDU size")
        return catalogCode


    def read_cpu_info(self) -> CPUInfo:
        """
        Read CPU model.

        Returns:
            CPUInfo(NamedTuple)
        """

        cpuInfo = CPUInfo()
        
        data = self.read_szl(id=const.SystemStateList.CPU_ID)

        totalLength = len(data)
        if totalLength < 34:
            return cpuInfo(error="Invalid PDU Length")

        offset = 4
        sectionLength, szlCount = struct.unpack_from(f'{self.endian}HH', data, offset)
        offset += 4
        for item in range(szlCount):
            if offset + 34 >= totalLength:
                break
            index, name = struct.unpack_from(
                f'{self.endian}H32s', 
                data, 
                offset
            )
            offset += sectionLength
            if index == 0x0001:
                name = name.decode().strip()
                cpuInfo = cpuInfo._replace(systemName=name)
            elif index == 0x0002:
                name = name.decode().strip()
                cpuInfo = cpuInfo._replace(moduleName=name)
            elif index == 0x0003:
                name = name.decode().strip()
                cpuInfo = cpuInfo._replace(plantId=name)
            elif index == 0x0004:
                name = name.decode().strip()
                cpuInfo = cpuInfo._replace(copyright=name)
            elif index == 0x0005:
                name = name.decode().strip()
                cpuInfo = cpuInfo._replace(serialNumber=name)
            elif index == 0x0007:
                name = name.decode().strip()
                cpuInfo = cpuInfo._replace(cpuType=name)
            elif index == 0x0008:
                name = name.decode().strip()
                cpuInfo = cpuInfo._replace(memSerialNumber=name)
            elif index == 0x0009:
                manufacturerId = f"0x{name[0:2].hex()}"
                cpuInfo = cpuInfo._replace(manufacturerId=manufacturerId)
                profileId = f"0x{name[2:4].hex()}"
                cpuInfo = cpuInfo._replace(profileId=profileId)
                profileSpec = f"0x{name[4:6].hex()}"
                cpuInfo = cpuInfo._replace(profileSpec=profileSpec)
            elif index == 0x000a:
                oemCopyright = name[0:26].decode().strip()
                cpuInfo = cpuInfo._replace(oemCopyright=oemCopyright)
                oemId = f"0x{name[26:28].hex()}"
                cpuInfo = cpuInfo._replace(oemId=oemId)
                oemAddId = f"0x{name[28:32].hex()}"
                cpuInfo = cpuInfo._replace(oemAddId=oemAddId)
            elif index == 0x000b:
                name = name.decode().strip()
                cpuInfo = cpuInfo._replace(locationId=name)
        return cpuInfo


    def read_comm_proc(self) -> list:
        result = []
        index = 0x0001
        data = self.read_szl(id=const.SystemStateList.COMM_PROC, index=index)

        totalLength = len(data)
        if totalLength < 34:
            return CommProc(error="Invalid PDU Length")

        offset = 4
        sectionLength, szlCount = struct.unpack_from(f'{self.endian}HH', data, offset)
        offset += 4
        reservedLength = sectionLength - 14
        for item in range(szlCount):
            if offset + 14 + reservedLength -1 >= totalLength:
                break
            index, pdu, anz, mpiBPS, mkbusBPS, res = struct.unpack_from(
                f'{self.endian}HHHII{reservedLength}s', 
                data, 
                offset
            )
            result.append(
                CommProc(
                    maxPDU=pdu, 
                    maxConnections=anz, 
                    mpiRate=mpiBPS, 
                    mkbusRate=mkbusBPS
                )
            )
            offset += sectionLength
        return result


    def stop_plc(self) -> bool:
        cpuStatus = self.read_cpu_status()

        if cpuStatus.requestedMode != "Stop":
            request = bytearray(const.S7_STOP)
            self._send(send_data=request)
            data = self._recv()

            length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
            if (length > 19): # the minimum expected
                headerErrorClass, headerErrorCode, function = struct.unpack_from('BBB', data, 17)
                if headerErrorClass != const.ErrorClass.NO_ERROR or headerErrorCode != 0:
                    return False
        return True


    def start_plc_cold(self) -> bool:
        cpuStatus = self.read_cpu_status()

        if cpuStatus.requestedMode != "Run":
            request = bytearray(const.S7_COLD_START)

            self._send(send_data=request)
            data = self._recv()

            length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
            if (length > 18): # the minimum expected
                headerErrorClass, headerErrorCode = struct.unpack_from(f'BB', data, 17)
                if headerErrorClass != const.ErrorClass.NO_ERROR or headerErrorCode != 0:
                    return False
        return True


    def start_plc_hot(self) -> bool:
        cpuStatus = self.read_cpu_status()

        if cpuStatus.requestedMode != "Run":
            request = bytearray(const.S7_HOT_START)

            self._send(send_data=request)
            data = self._recv()

            length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
            if (length > 18): # the minimum expected
                headerErrorClass, headerErrorCode = struct.unpack_from('BB', data, 17)
                if headerErrorClass != const.ErrorClass.NO_ERROR or headerErrorCode != 0:
                    return False
        return True


    def read_szl(self, id:int, index:int=0x0000) -> bytes:

        request = bytearray(const.S7_SZL_FIRST)
        struct.pack_into(f'{self.endian}HH', request, 29, id, index)
        
        self._send(send_data=request)
        data = self._recv()

        length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
        if (length > 32): # the minimum expected
            (
                pduRef, 
                lastDataUnit,
                paramErrorCode, 
                dataReturnCode, 
                transportSize, 
                length
            ) = struct.unpack_from(f'{self.endian}BBHBBH', data, 25)
            fragmentedData = data[33:]
            # use lastDataUnit to iterate
            while lastDataUnit != const.LastDataUnit.YES:
                pduRef += 1
                requestNext = bytearray(const.S7_SZL_NEXT)
                struct.pack_into(f'{self.endian}H', requestNext, 11, pduRef)
                try:
                    self._send(send_data=requestNext)
                except:
                    break
                data = self._recv()
                (
                    pduRef, 
                    lastDataUnit, 
                    paramErrorCode, 
                    dataReturnCode, 
                    transportSize,
                    length
                ) = struct.unpack_from(f'{self.endian}BBHBBH', data, 25)
                if (paramErrorCode == const.ParamErrorCode.NO_ERROR
                    and dataReturnCode == const.ReturnCode.SUCCESS 
                    and length > 0
                ):
                    fragmentedData += data[33:]
            return fragmentedData
        return data


    def read_protection(self) -> list:
        result = []

        data = self.read_szl(id=const.SystemStateList.PROTECTION, index=0x0004)

        totalLength = len(data)
        if totalLength < 4:
            return result
        offset = 4
        sectionLength, szlCount = struct.unpack_from(f'{self.endian}HH', data, offset)
        offset += 4
        for item in range(szlCount):
            if offset + 12 > totalLength:
                break
            (
                index, 
                sch_schal, 
                sch_par, 
                sch_rel, 
                bart_sch, 
                anl_sch
            ) = struct.unpack_from(f'{self.endian}HHHHHH', data, offset)
            result.append(
                Protection(
                    protectionLevel=sch_schal, 
                    passwordLevel=sch_par, 
                    validProtectionLevel=sch_rel, 
                    modeSelector=util.GetModeSelector(bart_sch), 
                    startupSwitch=util.GetStartupSwitchSelector(anl_sch)
                )
            )
            offset += sectionLength
        return result


    def read_cpu_diagnostic(self) -> list:
        result = []

        data = self.read_szl(id=const.SystemStateList.CPU_DIAGOSTICS)

        totalLength = len(data)
        if totalLength < 20:
            return result

        # extract data
        offset = 4
        sectionLength, szlCount = struct.unpack_from(f'{self.endian}HH', data, offset)
        offset += 4
        for item in range(szlCount):
            if offset + 20 >= totalLength:
                break
            (
                eventId, 
                priority,
                obNumber,
                datId,
                info1,
                info2,
                timestamp
            ) = struct.unpack_from(f'{self.endian}2sBB2s2s4s8s', data, offset)
            result.append(
                CPUDiagnostics(
                    eventId=f"0x{eventId.hex()}",
                    description=util.GetCpuDiagnostic(struct.unpack(f'{self.endian}H', eventId)[0]),
                    priority=priority,
                    obNumber=obNumber,
                    datId=f"0x{datId.hex()}",
                    info1=f"0x{info1.hex()}",
                    info2=f"0x{info2.hex()}",
                    timestamp=util.GetDateTime(timestamp)
                )
            )
            offset += sectionLength

        return result


    def read_cpu_leds(self) -> list:

        result = []

        data = self.read_szl(id=const.SystemStateList.CPU_LEDS)

        totalLength = len(data)
        if totalLength < 4:
            return result

        # extract data
        offset = 4
        sectionLength, szlCount = struct.unpack_from(f'{self.endian}HH', data, offset)
        offset += 4
        for item in range(szlCount):
            if offset > totalLength:
                break
            (
                id, 
                status,
                flashing,
            ) = struct.unpack_from(f'{self.endian}HBB', data, offset)
            result.append(
                CPULed(
                    rack=(id>>8)&0x07,
                    type=(id>>11)&0x01,
                    id=util.GetCpuLed(id&0xFF),
                    on=bool(status),
                    flashing=bool(flashing)
                )
            )
            offset += sectionLength
        return result


    def read_block_info(self, BlockType:int, BlockNumber:int) -> list:

        request = bytearray(const.S7_BLOCK_INFO)

        request[30] = BlockType & 0xFF
        # Block Number
        request[31] = ((BlockNumber // 10000) + 0x30) & 0xFF
        BlockNumber = BlockNumber % 10000
        request[32] = ((BlockNumber // 1000) + 0x30) & 0xFF
        BlockNumber = BlockNumber % 1000
        request[33] = ((BlockNumber // 100) + 0x30) & 0xFF
        BlockNumber = BlockNumber % 100
        request[34] = ((BlockNumber // 10) + 0x30) & 0xFF
        BlockNumber = BlockNumber % 10
        request[35] = ((BlockNumber // 1) + 0x30) & 0xFF

        self._send(send_data=request)
        data = self._recv()

        result = []

        length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
        if (length > 32): # the minimum expected
            paramErrorCode, dataReturnCode = struct.unpack_from(f'{self.endian}HB', data, 27)
            if (paramErrorCode == const.ParamErrorCode.NO_ERROR 
                and dataReturnCode == const.ReturnCode.SUCCESS
            ):
                # IH IH: timestamps
                (
                    flags,
                    language,
                    blockType,
                    number,
                    loadMemory,
                    security,
                    codeMillis,
                    codeDaysSince,
                    interfaceMillis,
                    interfaceDaysSince,
                    ssbLength,
                    addLength,
                    localDataLength,
                    mc7Length,
                    author,
                    family,
                    name,
                    version,
                    reserved,
                    checksum
                ) = struct.unpack_from(f'{self.endian}1s B B H I I IH IH H H H H 8s 8s 8s B B 2s', data, 42)
                versionHi, versionLo = util.ByteToNibbles(version)
                blockInfo = BlockInfo(
                    flags=f"0x{flags.hex()}",
                    language=util.GetBlockLanguage(language),
                    type=util.GetSubblockType(blockType),
                    number=number,
                    loadMemory=loadMemory,
                    security=security,
                    codeTimestamp=util.GetTime(Milliseconds=codeMillis, DaysSince=codeDaysSince),
                    interfaceTimestamp=util.GetTime(Milliseconds=interfaceMillis, DaysSince=interfaceDaysSince),
                    ssbLength=ssbLength,
                    addLength=addLength,
                    localDataLength=localDataLength,
                    mc7Length=mc7Length,
                    author=author.decode().rstrip('\x00'),
                    family=family.decode().rstrip('\x00'),
                    name=name.decode().rstrip('\x00'),
                    version=f"{versionHi}.{versionLo}",
                    checksum=f"0x{checksum.hex()}"
                )
                result.append(blockInfo)
                # update cache
                if self.cache_data.get(blockInfo.type) is None:
                    self.cache_data[blockInfo.type] = {}   
                self.cache_data[blockInfo.type][blockInfo.number] = blockInfo
            else:
                self.__log.error(f"self.read_block_info(): {ErrorCode(paramErrorCode)}")
                raise ErrorCode(paramErrorCode)
        else:
            self.__log.error(f"self.read_block_info(): Invalid PDU")
            raise CommTypeError("Invalid PDU")
        return result


    def read_area(self, Address:str, Elements:int=0, ItemList:list=[]) -> list:
        result = []

        # extract params from address
        AreaName, Area, Number, Offset = util.GetAreaAddress(id=Address)

        if Elements < 1:
            for item in ItemList:
                length = util.DataSizeByte(item.type)
                Elements += length
            if Elements < 1:
                return result

        if (self.controller < 1500):
            try:
                if self.cache_data.get(AreaName) is None:
                    self.read_block_info(BlockType=const.BlockType.DB, BlockNumber=Number)
                elif self.cache_data.get(AreaName).get(Number) is None:
                    self.read_block_info(BlockType=const.BlockType.DB, BlockNumber=Number)
                mc7Length = self.cache_data.get(AreaName).get(Number).mc7Length
            except Exception:
                mc7Length = Elements
                pass

            # Resize elements if bigger than block
            if Offset + Elements > mc7Length:
                Elements = mc7Length - Offset

        # Some adjustment
        if (Area == const.Area.COUNTER_S7):
            TransportSize = const.DataType.COUNTER
        elif (Area == const.Area.TIMER_S7):
            TransportSize = const.DataType.TIMER
        else:
            TransportSize = const.DataType.BYTE

        # Calc Word size          
        WordSize = util.DataSizeByte(TransportSize)
        if (WordSize == 0):
            self.__log.error(f"self.read_area(): Invalid Data Size")
            raise DataTypeError("Invalid Data Size")

        if (TransportSize == const.DataType.BIT):
            Elements = 1  # Only 1 bit can be transferred at time
        else:
            if (TransportSize != const.DataType.COUNTER 
                and TransportSize != const.DataType.TIMER
            ):
                Elements *= WordSize
                WordSize = 1
                TransportSize = const.DataType.BYTE

        MaxElements = (self._pdu_length - 18) // WordSize # 18 = Reply telegram header
        TotalElements = Elements
        fragmentedData = bytes()

        while (TotalElements > 0):
            NumElements = TotalElements
            if (NumElements > MaxElements):
                NumElements = MaxElements

            # SizeRequested = NumElements * WordSize

            # Setup the telegram
            # read only uses first 31 bytes
            request = bytearray(const.S7_READ_WRITE[0:31])
            # Set Area
            struct.pack_into('B', request, 27, Area)
            # Set DB Number
            if (Area == const.Area.DB_DATABLOCKS):
                struct.pack_into(f'{self.endian}H', request, 25, Number)

            # Adjusts Offset and word length
            if (TransportSize == const.DataType.BIT 
                or TransportSize == const.DataType.COUNTER
                 or TransportSize == const.DataType.TIMER
            ):
                Address = Offset
                struct.pack_into('B', request, 22, TransportSize)
            else:
                Address = Offset << 3

            # Num elements
            struct.pack_into(f'{self.endian}H', request, 23, NumElements)
            # Address into the PLC
            struct.pack_into(
                f'BBB', 
                request, 
                28, 
                (Address >> 16) & 0xFF,
                (Address >> 8) & 0xFF,
                (Address >> 0) & 0xFF
            )

            self._send(send_data=request)
            data = self._recv()

            length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
            if (length < 25):
                self.__log.error(f"self.read_area(): Invalid PDU size")
                raise CommTypeError("Invalid PDU size")
            else:
                headerErrorClass, headerErrorCode, paramFunction, itemCount = struct.unpack_from('BBBB', data, 17)
                if headerErrorClass != const.ErrorClass.NO_ERROR or headerErrorCode != 0:
                    self.__log.error(f"self.read_area(): Invalid PDU size")
                    raise CommTypeError("Invalid PDU size")
                else:
                    for item in range(itemCount):
                        dataReturnCode, transportSize, length = struct.unpack_from(
                            f'{self.endian}BBH', 
                            data,
                            21
                        )
                        if dataReturnCode == const.ReturnCode.SUCCESS:
                            fragmentedData += data[25:]
                        else:
                            self.__log.error(f"self.read_area(): {ReturnCode(dataReturnCode)}")
                            raise ReturnCode(dataReturnCode)
            TotalElements -= NumElements
            Offset += NumElements * WordSize
        
        
        # return raw bytes
        if not ItemList:
            result.append(
                Tag(
                    address=Address, 
                    value=fragmentedData, 
                    size=len(fragmentedData), 
                    type=const.DataType.CHAR
                )
            )
        else:
            # loop through item list to unpack data
            offset = 0
            for item in ItemList:
                encode = False
                length = util.DataSizeByte(item.type)
                if (item.type == const.DataType.BIT
                    or item.type == const.DataType.BYTE
                ):
                    unpackFormat = "B"
                elif item.type == const.DataType.CHAR:
                    unpackFormat = "1sB"
                elif item.type == const.DataType.INT:
                    unpackFormat = "h"
                elif item.type == const.DataType.WORD:
                    unpackFormat = "H"
                elif item.type == const.DataType.DATE:
                    unpackFormat = "H" # days since 1990-01-01
                    encode = True
                elif item.type == const.DataType.DATETIME:
                    unpackFormat = "8s"
                    encode = True
                elif item.type == const.DataType.S5TIME:
                    unpackFormat = "2s"
                    encode = True
                elif item.type == const.DataType.DINT:
                    unpackFormat = "i"
                elif item.type == const.DataType.DWORD:
                    unpackFormat = "I"
                elif item.type == const.DataType.REAL:
                    unpackFormat = "f"
                elif item.type == const.DataType.TIME:
                    unpackFormat = "I"
                elif item.type == const.DataType.TIME_OF_DAY:
                    unpackFormat = "I"
                elif item.type == const.DataType.STRING:
                    unpackFormat = "BB254s"
                    encode = True
                # string decode is its own thing
                if item.type != const.DataType.STRING:
                    value = struct.unpack_from(f'{self.endian}{unpackFormat}', fragmentedData, offset)[0]
                if encode:
                    if item.type == const.DataType.DATE:
                        value = util.GetDate(DaysSince=value)
                    elif item.type == const.DataType.DATETIME:
                        value = util.GetDateTime(Buffer=value)
                    elif item.type == const.DataType.S5TIME:
                        value = util.GetS5Time(Buffer=value)
                    elif item.type == const.DataType.STRING:
                        (
                            maxLen, 
                            strLen, 
                            string
                        ) = struct.unpack_from(f'{self.endian}{unpackFormat}', fragmentedData, offset)
                        value = string[:strLen].decode()
                item = item._replace(
                    address=f"{AreaName}{Number}.{offset}",
                    value=value,
                    size=length,
                    type=item.type
                )
                result.append(item)
                offset += length

        return result


    def write_area(self, Address:str, ItemList:list=[]):
        # extract params from address
        AreaName, Area, Number, Offset = util.GetAreaAddress(id=Address)

        # Generate total elements (bytes)
        dataLength = 0
        totalPayload = bytes()
        for item in ItemList:
            if type(item) != Tag:
                self.__log.error(f"self.write_area(): Invalid data type")
                raise DataTypeError("Invalid data type")
            length = util.DataSizeByte(item.type)
            if (item.type == const.DataType.BIT
                or item.type == const.DataType.BYTE
            ):
                payload = struct.pack('B', abs(int(item.value)&0xFF))
            elif item.type == const.DataType.CHAR:
                payload = struct.pack('1sB', str(item.value).encode(), 0)
            elif item.type == const.DataType.INT:
                payload = struct.pack(f'{self.endian}h', int(item.value))
            elif item.type == const.DataType.WORD:
                payload = struct.pack(f'{self.endian}H', abs(item.value))
            elif item.type == const.DataType.DINT:
                payload = struct.pack(f'{self.endian}i', int(item.value))
            elif item.type == const.DataType.DWORD:
                payload = struct.pack(f'{self.endian}I', abs(int(item.value)))
            elif item.type == const.DataType.REAL:
                payload = struct.pack(f'{self.endian}f', item.value)
            elif item.type == const.DataType.STRING:
                payload = struct.pack(
                    f'{self.endian}BB254s', 
                    254, 
                    len(item.value), 
                    item.value.encode()
                )
            elif item.type == const.DataType.DATE: # days since 1990-01-01
                payload = struct.pack(f'{self.endian}H', util.SetDate(item.value))
            elif item.type == const.DataType.TIME:
                payload = struct.pack(f'{self.endian}I', abs(int(item.value)))
            elif item.type == const.DataType.DATETIME:
                payload = struct.pack('8s', util.SetDateTime(item.value))
            elif item.type == const.DataType.TIME_OF_DAY:
                payload = struct.pack(f'{self.endian}I', abs(int(item.value)))
            elif item.type == const.DataType.S5TIME:
                payload = struct.pack('2s', util.SetS5Time(item.value))
            # get total payload and its length
            totalPayload += payload
            dataLength += length

        mc7Length = Elements
        if (self.controller < 1500):
            try:
                if self.cache_data.get(AreaName) is None:
                    self.read_block_info(BlockType=const.BlockType.DB, BlockNumber=Number)
                elif self.cache_data.get(AreaName).get(Number) is None:
                    self.read_block_info(BlockType=const.BlockType.DB, BlockNumber=Number)
                mc7Length = self.cache_data.get(AreaName).get(Number).mc7Length
            except Exception:
                pass

        Elements = dataLength
        # Resize elements if bigger than block
        if Offset + Elements > mc7Length:
            Elements = mc7Length - Offset

        # Some adjustment
        if (Area == const.Area.COUNTER_S7):
            dataType = const.DataType.COUNTER
        elif (Area == const.Area.TIMER_S7):
            dataType = const.DataType.TIMER
        else:
            dataType = const.DataType.BYTE

        # Calc Word size          
        WordSize = util.DataSizeByte(dataType)
        if (WordSize == 0):
            self.__log.error(f"self.write_area(): Invalid data size")
            raise DataTypeError("Invalid Data Size")

        if (dataType == const.DataType.BIT):
            Elements = 1  # Only 1 bit can be transferred at time
        else:
            if (dataType != const.DataType.COUNTER 
                and dataType != const.DataType.TIMER
            ):
                Elements *= WordSize
                WordSize = 1

        MaxElements = (self._pdu_length - 35) // WordSize # 35 = Reply telegram header
        TotalElements = dataLength # Elements

        while (TotalElements > 0):
            NumElements = TotalElements
            if (NumElements > MaxElements):
                NumElements = MaxElements

            DataSize = NumElements * WordSize
            IsoSize = 35 + DataSize

            # Setup the telegram
            # Write uses all 35 bytes
            request = bytearray(const.S7_READ_WRITE)
            # Set telegram size
            struct.pack_into(f'{self.endian}H', request, 2, IsoSize)
            # Data Length
            Length = DataSize + 4
            struct.pack_into(f'{self.endian}H', request, 15, Length)
            # Update function
            request[17] = const.Function.WRITE_VARIABLE
            # Set Area
            struct.pack_into('B', request, 27, Area)
            # Set DB Number
            if (Area == const.Area.DB_DATABLOCKS):
                struct.pack_into(f'{self.endian}H', request, 25, Number)

            # Adjusts Offset and word length
            if (dataType == const.DataType.BIT 
                or dataType == const.DataType.COUNTER
                 or dataType == const.DataType.TIMER
            ):
                Address = Offset
                Length = DataSize
                request[22] = dataType
            else:
                Address = Offset << 3
                Length = DataSize << 3

            # Num elements
            struct.pack_into(f'{self.endian}H', request, 23, NumElements)
            # Set address
            struct.pack_into(
                f'BBB', 
                request, 
                28, 
                (Address >> 16) & 0xFF,
                (Address >> 8) & 0xFF,
                (Address >> 0) & 0xFF
            )

            # Set transport size and data length
            if (dataType == const.DataType.BIT):
                request[32] = const.TransportSize.BIT
            elif (dataType == const.DataType.COUNTER or dataType == const.DataType.TIMER):
                request[32] = const.TransportSize.OCTET_STRING
            else:
                request[32] = const.TransportSize.BYTE_WORD_DWORD
            struct.pack_into(f'{self.endian}H', request, 33, Length)

            # attach payload to write request
            request += totalPayload[Offset:Offset+DataSize]

            self._send(send_data=request)
            try:
                data = self._recv()
            except:
                pass

            length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
            if (length == 22):
                headerErrorClass, headerErrorCode = struct.unpack_from('BB', data, 17)
                dataReturnCode = struct.unpack_from('B', data, 21)
                if (headerErrorClass != const.ErrorClass.NO_ERROR
                    and headerErrorCode != 0x00
                    and dataReturnCode != const.ReturnCode.SUCCESS
                ):
                    self.__log.error(f"self.write_area(): {ErrorClass(headerErrorClass)}")
                    raise ErrorClass(headerErrorClass)
            else:
                self.__log.error(f"self.write_area(): Invalid PDU size")
                raise CommTypeError("Invalid PDU size")

            TotalElements -= NumElements
            Offset += NumElements * WordSize
