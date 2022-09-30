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
        self.tcp_connect(ip=self.host, port=self.port)
        self.set_connection_parameters(LocalTSAP=self.LocalTSAP, RemoteTSAP=self.RemoteTSAP)
        self.iso_connect()
        self.negotiate_pdu_length()
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


    def tcp_connect(self, ip:str, port:int):
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
            self.__log.error(f"self.tcp_connect(): {str(socket.timeout)}")
        

    def close(self):
        """
        Close connection.
        """

        self._sock.close()
        self._tcp_connected = self._iso_connected = self._pdu_negotiated = False


    def _tcp_send(self, send_data:bytes):
        """
        Send data 

        Args:
            send_data(bytes): Step7 Communication data
        """

        if self._tcp_connected:
            self.__log.debug(f'self._tcp_send(): \n{send_data.hex()}')
            try:
                self._sock.send(send_data)
            except socket.timeout:
                self.__log.error(f"self._tcp_send(): {str(socket.timeout)}")
        else:
            self.__log.error(f"self._tcp_send(): Socket is not connected. Please use connect method")
            raise CommTypeError("Socket is not connected. Please use connect method")


    def _iso_send(self, send_data:bytes):
        """
        Send data 

        Args:
            send_data(bytes): Step7 Communication data
        """

        if self._tcp_connected and self._iso_connected:
            self.__log.debug(f'self._iso_send(): \n{send_data.hex()}')
            try:
                self._sock.send(send_data)
            except socket.timeout:
                self.__log.error(f"self._iso_send(): {str(socket.timeout)}")
        else:
            self.__log.error(f"self._iso_send(): Socket is not connected. Please use connect method")
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


    def set_connection_parameters(self, LocalTSAP:int, RemoteTSAP:int):
        LocTSAP = LocalTSAP & 0x0000FFFF
        RemTSAP = RemoteTSAP & 0x0000FFFF
        self.LocalTSAP_HI = LocTSAP >> 8
        self.LocalTSAP_LO = (LocTSAP & 0x00FF)
        self.RemoteTSAP_HI = (RemTSAP >> 8)
        self.RemoteTSAP_LO = (RemTSAP & 0x00FF)


    def iso_connect(self):
        # connection request
        request = const.ISO_CR
        request[16] = self.LocalTSAP_HI
        request[17] = self.LocalTSAP_LO
        request[20] = self.RemoteTSAP_HI
        request[21] = self.RemoteTSAP_LO
        self._tcp_send(send_data=bytes(request))
        data = self._recv()
        length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
        self._iso_connected = False
        if (length == 22):
            PDUType = struct.unpack_from('B', data, 5)[0]
            if (PDUType != const.COTP.CONNECT_CONFIRM):
                self.__log.error(f"self.iso_connect(): Failed to perform ISO connect")
                raise CommTypeError("Failed to perform ISO connect")
            else:
                self._iso_connected = True
        else:
            self.__log.error(f"self.iso_connect(): Invalid PDU")
            raise CommTypeError("Invalid PDU")


    def negotiate_pdu_length(self):
        """
        ROSCTR:Job:Function:Setup Communication
        ROSCTR:Ack_Data:Function:Setup Communication
        """

        # Set PDU Size Requested
        request = bytearray(const.S7_PN)
        struct.pack_into(f'{self.endian}H', request, 23, self._PduSizeRequested)
        # Sends the connection request telegram
        self._iso_send(send_data=request)
        data = self._recv()
        length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
        header_error_class, header_error_code = struct.unpack_from('BB', data, 17)
        self._pdu_negotiated = False
        # check S7 Error
        if (length == 27 
            and header_error_class == const.ErrorClass.NO_ERROR
            and header_error_code == 0x00
        ):
            # Get PDU Size Negotiated
            self._pdu_length = struct.unpack_from(f'{self.endian}H', data, 25)[0]
            if (self._pdu_length > 0):
                self._pdu_negotiated = True
            else:
                self.__log.error(f"self.negotiate_pdu_length(): Unable to negotiate PDU")
                raise CommTypeError("Unable to negotiate PDU")
        else:
            self.__log.error(f"self.negotiate_pdu_length(): Unable to negotiate PDU")
            raise CommTypeError("Unable to negotiate PDU")


    def set_connection_type(self, ConnectionType:int):
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
            param_error_code, data_return_code = struct.unpack_from(f'{self.endian}HB', data, 27)
            if (param_error_code == const.ParamErrorCode.NO_ERROR 
                and data_return_code == const.ReturnCode.SUCCESS
            ):
                # year1 = util.bcd_to_byte(data[34])
                return util.get_datetime(buffer=data, offset=35)
            else:
                self.__log.error(f"self.read_plc_time(): {ErrorCode(param_error_code)}")
                raise ErrorCode(param_error_code)
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
        struct.pack_into('8s', request, 31, util.set_datetime(DT=dt))

        self._send(send_data=request)
        data = self._recv()

        length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
        if (length > 30): # the minimum expected
            param_error_code = struct.unpack_from(f'{self.endian}H', data, 27)[0]
            if (param_error_code != const.ParamErrorCode.NO_ERROR):
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
            param_error_code = struct.unpack_from(f'{self.endian}H', data, 27)[0]
            if (param_error_code == const.ParamErrorCode.NO_ERROR):
                status = struct.unpack_from('B', data, 44)[0]
                hiNib, loNib = util.byte_to_nibbles(status)
                cpuStatus = cpuStatus._replace(
                    requestedMode=util.get_cpu_status(Status=loNib),
                    previousMode=util.get_cpu_status(Status=hiNib)
                )
            else:
                self.__log.error(f"self.read_cpu_status(): {ErrorCode(param_error_code)}")
                raise ErrorCode(param_error_code)
        else:
            self.__log.error(f"self.read_cpu_status(): Invalid PDU size")
            raise CommTypeError("Invalid PDU size")
        return cpuStatus


    def read_catalog_code(self) -> CatalogCode:
        """
        Read Catalog Code.

        Returns:
            CatalogCode(NamedTuple)
        """

        catalogCode = CatalogCode()

        request = bytearray(const.S7_SZL_FIRST)
        struct.pack_into(f'{self.endian}H', request, 29, const.SystemStateList.CATALOG_CODE)

        self._send(send_data=request)
        data = self._recv()

        length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
        if (length > 30): # the minimum expected
            param_error_code, data_return_code = struct.unpack_from(f'{self.endian}HB', data, 27)
            if (param_error_code == const.ParamErrorCode.NO_ERROR 
                and data_return_code == const.ReturnCode.SUCCESS
            ):
                offset = 37
                section_length, szlCount = struct.unpack_from(f'{self.endian}HH', data, offset)
                offset += 4
                for item in range(szlCount):
                    (
                        index, 
                        mlfb, 
                        bgtype, 
                        ausbg, 
                        ausbe
                    ) = struct.unpack_from(f'{self.endian}H20sHHH', data, offset)
                    offset += section_length
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
                self.__log.error(f"self.read_catalog_code(): {ErrorCode(param_error_code)}")
                raise ErrorCode(param_error_code)
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
        section_length, szlCount = struct.unpack_from(f'{self.endian}HH', data, offset)
        offset += 4
        for item in range(szlCount):
            if offset + 34 >= totalLength:
                break
            index, name = struct.unpack_from(
                f'{self.endian}H32s', 
                data, 
                offset
            )
            offset += section_length
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
        """
        Read communication processor

        Returns:
            result(list): list of communication processor capabilities
        """
        result = []
        index = 0x0001
        data = self.read_szl(id=const.SystemStateList.COMM_PROC, index=index)

        totalLength = len(data)
        if totalLength < 34:
            return CommProc(error="Invalid PDU Length")

        offset = 4
        section_length, szlCount = struct.unpack_from(f'{self.endian}HH', data, offset)
        offset += 4
        reservedLength = section_length - 14
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
            offset += section_length
        return result


    def stop_plc(self) -> bool:
        """
        Stop PLC

        Returns:
            status(bool): command result
                            True (success)
                            False (not executed)
        """
        cpuStatus = self.read_cpu_status()

        if cpuStatus.requestedMode != "Stop":
            request = bytearray(const.S7_STOP)
            self._send(send_data=request)
            data = self._recv()

            length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
            if (length > 19): # the minimum expected
                header_error_class, header_error_code, function = struct.unpack_from('BBB', data, 17)
                if header_error_class != const.ErrorClass.NO_ERROR or header_error_code != 0:
                    return False
        return True


    def start_plc_cold(self) -> bool:
        """
        Start PLC cold (reset memory)

        Returns:
            status(bool): command result
                            True (success)
                            False (not executed)
        """
        cpuStatus = self.read_cpu_status()

        if cpuStatus.requestedMode != "Run":
            request = bytearray(const.S7_COLD_START)

            self._send(send_data=request)
            data = self._recv()

            length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
            if (length > 18): # the minimum expected
                header_error_class, header_error_code = struct.unpack_from(f'BB', data, 17)
                if header_error_class != const.ErrorClass.NO_ERROR or header_error_code != 0:
                    return False
        return True


    def start_plc_hot(self) -> bool:
        """
        Start PLC hot (resume)

        Returns:
            status(bool): command result
                            True (success)
                            False (not executed)
        """

        cpuStatus = self.read_cpu_status()

        if cpuStatus.requestedMode != "Run":
            request = bytearray(const.S7_HOT_START)

            self._send(send_data=request)
            data = self._recv()

            length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
            if (length > 18): # the minimum expected
                header_error_class, header_error_code = struct.unpack_from('BB', data, 17)
                if header_error_class != const.ErrorClass.NO_ERROR or header_error_code != 0:
                    return False
        return True


    def read_szl(self, id:int, index:int=0x0000) -> bytes:
        """
        Read CPU LEDs
        
        Args:
            id(int):  System status list (SZL) ID (e.g. 0x0232)
            index(int): index of SZL
                            0x0000 (default)
        Returns:
            result(list): list of CPU LEDs status
        """

        request = bytearray(const.S7_SZL_FIRST)
        struct.pack_into(f'{self.endian}HH', request, 29, id, index)
        
        self._send(send_data=request)
        data = self._recv()

        length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
        if (length > 32): # the minimum expected
            (
                pduRef, 
                lastDataUnit,
                param_error_code, 
                data_return_code, 
                transport_size, 
                length
            ) = struct.unpack_from(f'{self.endian}BBHBBH', data, 25)
            fragmented_data = data[33:]
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
                    param_error_code, 
                    data_return_code, 
                    transport_size,
                    length
                ) = struct.unpack_from(f'{self.endian}BBHBBH', data, 25)
                if (param_error_code == const.ParamErrorCode.NO_ERROR
                    and data_return_code == const.ReturnCode.SUCCESS 
                    and length > 0
                ):
                    fragmented_data += data[33:]
            return fragmented_data
        return data


    def read_protection(self) -> list:
        """
        Read CPU Protection levels

        Returns:
            result(list): list of CPU protection levels
        """
        result = []

        data = self.read_szl(id=const.SystemStateList.PROTECTION, index=0x0004)

        totalLength = len(data)
        if totalLength < 4:
            return result
        offset = 4
        section_length, szlCount = struct.unpack_from(f'{self.endian}HH', data, offset)
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
                    modeSelector=util.get_mode_selector(bart_sch), 
                    startupSwitch=util.get_startup_switch_selector(anl_sch)
                )
            )
            offset += section_length
        return result


    def read_cpu_diagnostic(self) -> list:
        """
        Read CPU Diagnostics

        Returns:
            result(list): list of CPU diagnostics
        """
        result = []

        data = self.read_szl(id=const.SystemStateList.CPU_DIAGOSTICS)

        totalLength = len(data)
        if totalLength < 20:
            return result

        # extract data
        offset = 4
        section_length, szlCount = struct.unpack_from(f'{self.endian}HH', data, offset)
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
                    description=util.get_cpu_diagnostic(struct.unpack(f'{self.endian}H', eventId)[0]),
                    priority=priority,
                    obNumber=obNumber,
                    datId=f"0x{datId.hex()}",
                    info1=f"0x{info1.hex()}",
                    info2=f"0x{info2.hex()}",
                    timestamp=util.get_datetime(timestamp)
                )
            )
            offset += section_length

        return result


    def read_cpu_leds(self) -> list:
        """
        Read CPU LEDs

        Returns:
            result(list): list of CPU LEDs status
        """

        result = []

        data = self.read_szl(id=const.SystemStateList.CPU_LEDS)

        totalLength = len(data)
        if totalLength < 4:
            return result

        # extract data
        offset = 4
        section_length, szlCount = struct.unpack_from(f'{self.endian}HH', data, offset)
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
                    id=util.get_cpu_led(id&0xFF),
                    on=bool(status),
                    flashing=bool(flashing)
                )
            )
            offset += section_length
        return result


    def read_block_info(self, block_type:int, block_number:int) -> list:
        """
        Read block info

        Args:
            block_type(int):
            block_number(int):
        """
        request = bytearray(const.S7_BLOCK_INFO)

        request[30] = block_type & 0xFF
        # Block Number
        request[31] = ((block_number // 10000) + 0x30) & 0xFF
        block_number = block_number % 10000
        request[32] = ((block_number // 1000) + 0x30) & 0xFF
        block_number = block_number % 1000
        request[33] = ((block_number // 100) + 0x30) & 0xFF
        block_number = block_number % 100
        request[34] = ((block_number // 10) + 0x30) & 0xFF
        block_number = block_number % 10
        request[35] = ((block_number // 1) + 0x30) & 0xFF

        self._send(send_data=request)
        data = self._recv()

        result = []

        length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
        if (length > 32): # the minimum expected
            param_error_code, data_return_code = struct.unpack_from(f'{self.endian}HB', data, 27)
            if (param_error_code == const.ParamErrorCode.NO_ERROR 
                and data_return_code == const.ReturnCode.SUCCESS
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
                    mc7_length,
                    author,
                    family,
                    name,
                    version,
                    reserved,
                    checksum
                ) = struct.unpack_from(f'{self.endian}1s B B H I I IH IH H H H H 8s 8s 8s B B 2s', data, 42)
                versionHi, versionLo = util.byte_to_nibbles(version)
                blockInfo = BlockInfo(
                    flags=f"0x{flags.hex()}",
                    language=util.get_block_language(language),
                    type=util.get_subblock_type(blockType),
                    number=number,
                    loadMemory=loadMemory,
                    security=security,
                    codeTimestamp=util.get_time(Milliseconds=codeMillis, DaysSince=codeDaysSince),
                    interfaceTimestamp=util.get_time(Milliseconds=interfaceMillis, DaysSince=interfaceDaysSince),
                    ssbLength=ssbLength,
                    addLength=addLength,
                    localDataLength=localDataLength,
                    mc7Length=mc7_length,
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
                self.__log.error(f"self.read_block_info(): {ErrorCode(param_error_code)}")
                raise ErrorCode(param_error_code)
        else:
            self.__log.error(f"self.read_block_info(): Invalid PDU")
            raise CommTypeError("Invalid PDU")
        return result


    def read_area_raw(self, address:str, elements:int) -> list:
        """
        Read area and return raw bytes

        Args:
            address(str): string address to be used for custom read
            elements(int): size of request in bytes
        """

        result = []
        # extract params from address
        # extract area type
        area_type = util.get_all_alpha(address=address)
        # get numbers 
        number_type = util.get_all_numeric(address=address)
        try:
            area = util.get_area_from_name(Name=area_type[0])
        except Exception as exception:
            return Tag(
                address=address,
                size=elements,
                error=str(exception)
            )

        # get DB number
        db_number = number_type[0]
        offset = number_type[1]

        # target S7300/S7400
        if (self.controller < 1200):
            try:
                if self.cache_data.get(area_type[0]) is None:
                    self.read_block_info(block_type=const.BlockType.DB, block_number=db_number)
                elif self.cache_data.get(area_type[0]).get(db_number) is None:
                    self.read_block_info(block_type=const.BlockType.DB, block_number=db_number)
                mc7_length = self.cache_data.get(area_type[0]).get(db_number).mc7Length
            except Exception:
                mc7_length = elements
                pass

            # Resize elements if bigger than block
            if offset + elements > mc7_length:
                elements = mc7_length - offset

        # Some adjustment
        if (area == const.Area.COUNTER_S7):
            transport_size = const.DataType.COUNTER
        elif (area == const.Area.TIMER_S7):
            transport_size = const.DataType.TIMER
        else:
            transport_size = const.DataType.BYTE

        # Calc Word size          
        word_size = util.get_data_size_byte(transport_size)
        if (word_size == 0):
            self.__log.error(f"self.read_area(): Invalid Data Size")
            raise DataTypeError("Invalid Data Size")

        if (transport_size == const.DataType.BIT):
            elements = 1  # Only 1 bit can be transferred at time
        else:
            if (transport_size != const.DataType.COUNTER 
                and transport_size != const.DataType.TIMER
            ):
                elements *= word_size
                word_size = 1
                transport_size = const.DataType.BYTE

        max_elements = (self._pdu_length - 18) // word_size # 18 = Reply telegram header
        total_elements = elements
        fragmented_data = bytes()

        while (total_elements > 0):
            number_of_elements = total_elements
            if (number_of_elements > max_elements):
                number_of_elements = max_elements

            # Setup the telegram
            # read only uses first 31 bytes
            request = bytearray(const.S7_READ_WRITE[0:31])
            # Set Area
            struct.pack_into('B', request, 27, area)
            # Set DB Number
            if (area == const.Area.DB_DATABLOCKS):
                struct.pack_into(f'{self.endian}H', request, 25, db_number)

            # Adjusts offset and word length
            if (transport_size == const.DataType.BIT 
                or transport_size == const.DataType.COUNTER
                 or transport_size == const.DataType.TIMER
            ):
                address = offset
                struct.pack_into('B', request, 22, transport_size)
            else:
                address = offset << 3

            # Num elements
            struct.pack_into(f'{self.endian}H', request, 23, number_of_elements)
            # address into the PLC
            struct.pack_into(
                f'BBB', 
                request, 
                28, 
                (address >> 16) & 0xFF,
                (address >> 8) & 0xFF,
                (address >> 0) & 0xFF
            )

            self._send(send_data=request)
            data = self._recv()

            length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
            if (length < 25):
                self.__log.error(f"self.read_area(): Invalid PDU size")
                raise CommTypeError("Invalid PDU size")
            else:
                (
                    header_error_class, 
                    header_error_code, 
                    param_function, 
                    param_item_count
                ) = struct.unpack_from('BBBB', data, 17)
                if header_error_class != const.ErrorClass.NO_ERROR or header_error_code != 0:
                    self.__log.error(f"self.read_area(): Invalid PDU size")
                    raise CommTypeError("Invalid PDU size")
                else:
                    for item in range(param_item_count):
                        data_return_code, transport_size, length = struct.unpack_from(
                            f'{self.endian}BBH', 
                            data,
                            21
                        )
                        if data_return_code == const.ReturnCode.SUCCESS:
                            fragmented_data += data[25:]
                        else:
                            self.__log.error(f"self.read_area(): {ReturnCode(data_return_code)}")
                            raise ReturnCode(data_return_code)
            total_elements -= number_of_elements
            offset += number_of_elements * word_size

        # return raw bytes
        result.append(
            Tag(
                address=address, 
                value=fragmented_data, 
                size=len(fragmented_data), 
                type=const.DataType.CHAR
            )
        )

        return result


    def write_area_raw(self, address:str, raw_bytes:bytes) -> list:
        """
        Custom write data area

        Args:
            address(str): string address to be used for custom read
            raw_bytes(bytes): raw bytes to be written to controller
            elements(int): specify how many bytes to write
        """

        # extract params from address
        # extract area type
        area_type = util.get_all_alpha(address=address)
        # get numbers 
        number_type = util.get_all_numeric(address=address)
        try:
            area = util.get_area_from_name(Name=area_type[0])
        except Exception as exception:
            return Tag(
                address=address,
                size=elements,
                error=str(exception)
            )

        # get DB number
        number = number_type[0]
        offset = number_type[1]

        # Generate total elements (bytes)
        elements = len(raw_bytes)

        mc7_length = elements
        if (self.controller < 1200):
            try:
                if self.cache_data.get(area_type[0]) is None:
                    self.read_block_info(block_type=const.BlockType.DB, block_number=number)
                elif self.cache_data.get(area_type[0]).get(number) is None:
                    self.read_block_info(block_type=const.BlockType.DB, block_number=number)
                mc7_length = self.cache_data.get(area_type[0]).get(number).mc7Length
            except Exception:
                pass

        # Resize elements if bigger than block
        if offset + elements > mc7_length:
            elements = mc7_length - offset

        # Some adjustment
        if (area == const.Area.COUNTER_S7):
            data_type = const.DataType.COUNTER
        elif (area == const.Area.TIMER_S7):
            data_type = const.DataType.TIMER
        else:
            data_type = const.DataType.BYTE

        # Calc Word size          
        word_size = util.get_data_size_byte(data_type)
        if (word_size == 0):
            self.__log.error(f"self.write_area(): Invalid data size")
            raise DataTypeError("Invalid Data Size")

        if (data_type == const.DataType.BIT):
            elements = 1  # Only 1 bit can be transferred at time
        else:
            if (data_type != const.DataType.COUNTER 
                and data_type != const.DataType.TIMER
            ):
                elements *= word_size
                word_size = 1

        tag = Tag(address=address, size=elements)

        max_elements = (self._pdu_length - 35) // word_size # 35 = Reply telegram header
        total_elements = elements
        data_offset = 0
        while (total_elements > 0):
            number_of_elements = total_elements
            if (number_of_elements > max_elements):
                number_of_elements = max_elements

            data_size = number_of_elements * word_size
            iso_size = 35 + data_size

            # Setup the telegram
            # Write uses all 35 bytes
            request = bytearray(const.S7_READ_WRITE)
            # Set telegram size
            struct.pack_into(f'{self.endian}H', request, 2, iso_size)
            # Data Length
            data_length = data_size + 4
            struct.pack_into(f'{self.endian}H', request, 15, data_length)
            # Update function
            request[17] = const.Function.WRITE_VARIABLE
            # Set Area
            struct.pack_into('B', request, 27, area)
            # Set DB number
            if (area == const.Area.DB_DATABLOCKS):
                struct.pack_into(f'{self.endian}H', request, 25, number)

            # Adjusts offset and word length
            if (data_type == const.DataType.BIT 
                or data_type == const.DataType.COUNTER
                 or data_type == const.DataType.TIMER
            ):
                address = offset
                data_length = data_size
                request[22] = data_type
            else:
                address = offset << 3
                data_length = data_size << 3

            # Num elements
            struct.pack_into(f'{self.endian}H', request, 23, number_of_elements)
            # Set address
            struct.pack_into(
                f'BBB', 
                request, 
                28, 
                (address >> 16) & 0xFF,
                (address >> 8) & 0xFF,
                (address >> 0) & 0xFF
            )

            # Set transport size and data length
            if (data_type == const.DataType.BIT):
                request[32] = const.TransportSize.BIT
            elif (data_type == const.DataType.COUNTER or data_type == const.DataType.TIMER):
                request[32] = const.TransportSize.OCTET_STRING
            else:
                request[32] = const.TransportSize.BYTE_WORD_DWORD
            struct.pack_into(f'{self.endian}H', request, 33, data_length)

            # attach payload to write request
            request += raw_bytes[data_offset:data_offset+data_size]

            self._send(send_data=request)
            try:
                data = self._recv()
            except:
                pass

            length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
            if (length == 22):
                header_error_class, header_error_code = struct.unpack_from('BB', data, 17)
                data_return_code = struct.unpack_from('B', data, 21)
                if (header_error_class != const.ErrorClass.NO_ERROR
                    and header_error_code != 0x00
                    and data_return_code != const.ReturnCode.SUCCESS
                ):
                    self.__log.error(f"self.write_area(): {ErrorClass(header_error_class)}")
                    tag = tag._replace(error=ErrorClass(header_error_class))
                    # raise ErrorClass(header_error_class)
            else:
                self.__log.error(f"self.write_area(): Invalid PDU size")
                tag = tag._replace(error="Invalid PDU size")
                # raise CommTypeError("Invalid PDU size")

            total_elements -= number_of_elements
            offset += number_of_elements * word_size
            data_offset += number_of_elements * word_size

        return [tag]


    def read_area(self, item_list:list=[]) -> list:
        """
        Read data area

        Args:
            item_list(list): list of items to be requested
        Returns:
            result(list): same list of items as input but with values       
        """

        # result = []
        request = bytearray(const.S7_READ_WRITE[0:19]) # up to item count

        item_size = 12 # bytes
        item_count = 0
        total_pdu = 0
        previous_index = 0

        total_items = len(item_list)
        result = [Tag()] * total_items
        total_items_index = 0
        while total_items_index < total_items:
            try:
                # extract item
                item = item_list[total_items_index]
                result[total_items_index] = item
                # extract area type
                skip = False
                area_type = util.get_all_alpha(address=item.address)
                try:
                    area = util.get_area_from_name(Name=area_type[0])
                except Exception as exception:
                    item = item._replace(error=str(exception))
                    skip = True

                # string is its own BS
                if item.type == const.DataType.STRING and not skip:
                    # read first half to determine if more reading is needed
                    response = self.read_area_raw(address=item.address, elements=128)
                    # parse buffer
                    (
                        max_length, 
                        string_length, 
                        string_value
                    ) = struct.unpack("BB126s", response[0].value)
                    if string_length > 126:
                        area = util.get_all_alpha(address=item.address)
                        number = util.get_all_numeric(address=item.address)
                        remaining_elements = string_length - 126
                        # new offset is orignal offset + remaining + first 2 string bytes
                        index_offset = number[1] + remaining_elements
                        address_offset = f'{area[0]}{number[0]}.{area[1]}{index_offset}.{number[2]}'
                        response = self.read_area_raw(address=address_offset, elements=remaining_elements)
                        string_value += response[0].value
                    item = item._replace(
                        value=string_value[:string_length].decode(), 
                        size=string_length
                    )
                    skip = True

                if skip:
                    result[total_items_index] = item
                    total_items_index += 1
                    continue

                total_items_index += 1
                # get item length
                item_length = util.get_data_size_byte(item.type)
                # batch read
                item_count += 1
                total_pdu = 2 + (item_count * item_size)
                if total_pdu + 2 < self._pdu_length:
                    # extract area type
                    # get numbers 
                    number_type = util.get_all_numeric(address=item.address)
                    # get DB number
                    db_number = number_type[0]
                    # get transport size
                    if (area == const.Area.COUNTER_S7):
                        transport_size = const.DataType.COUNTER
                    elif (area == const.Area.TIMER_S7):
                        transport_size = const.DataType.TIMER
                    else:
                        transport_size = item.type
                        if transport_size != const.DataType.BIT:
                            transport_size = const.DataType.BYTE

                    # calculate address
                    # byte address + bit address
                    address = (number_type[1] << 3) + number_type[2]
                    address_bytes = struct.pack(
                        'BBB',
                        (address >> 16) & 0xFF,
                        (address >> 8) & 0xFF,
                        (address >> 0) & 0xFF
                    )
                    item_info = struct.pack(
                        f'{self.endian}BBBBHHB', 
                        0x12, # variable specifications
                        0x0A, # length of address specification
                        0x10, # syntax id: S7ANY
                        transport_size, 
                        item_length,
                        db_number,
                        area
                    )
                    request += (item_info + address_bytes)
                # see if max PDU length has been exceed or that end of items list
                if total_pdu + item_size >= self._pdu_length or total_items_index >= total_items:
                    request[18] = item_count
                    # param length = (param_function + param_item_count) + items*12
                    header_param_length = total_pdu
                    struct.pack_into(f'{self.endian}H', request, 13, header_param_length)
                    tpkt_length = 17 + header_param_length
                    struct.pack_into(f'{self.endian}H', request, 2, tpkt_length)
                    # send request
                    self._send(send_data=request)
                    # reset param afer sending
                    total_pdu = 0
                    item_count = 0
                    request = bytearray(const.S7_READ_WRITE[0:19]) # up to item count
                    data = self._recv()
                    # parse up to this message
                    tpkt_length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
                    if (tpkt_length < 25):
                        self.__log.error(f"self.read_area(): Invalid PDU size")
                        raise CommTypeError("Invalid PDU size")
                    else:
                        (
                            header_error_class, 
                            header_error_code, 
                            param_function, 
                            param_item_count
                        ) = struct.unpack_from('BBBB', data, 17)
                        if header_error_class != const.ErrorClass.NO_ERROR or header_error_code != 0:
                            self.__log.error(f"self.read_area(): Invalid PDU size")
                            raise CommTypeError("Invalid PDU size")
                        else:
                            # match item from main loop
                            item_offset = 21 # index 0
                            data_offset = item_offset + 4
                            for parse_index in range(previous_index, total_items_index):
                                # string has been handled, so skip
                                if (
                                    item_list[parse_index].type != const.DataType.STRING
                                    and result[parse_index].error == ''
                                ):
                                    (
                                        data_return_code, 
                                        data_transport_size, 
                                        data_item_length
                                    ) = struct.unpack_from(
                                        f'{self.endian}BBH', 
                                        data,
                                        item_offset
                                    )
                                    if data_item_length > 0:
                                        if (
                                            item_list[parse_index].type != const.DataType.BIT
                                            and item_list[parse_index].type != const.DataType.COUNTER
                                            and item_list[parse_index].type != const.DataType.TIMER
                                        ):
                                            data_item_length = data_item_length >> 3
                                        value = util.decode(
                                            data=data, 
                                            item_type=item_list[parse_index].type,
                                            offset=data_offset,
                                            endian=self.endian
                                        )
                                        item_offset += (4 + data_item_length)
                                        # padding for odd bytes
                                        if bool(data_item_length & 1):
                                            item_offset += 1
                                        data_offset = item_offset + 4
                                        result[parse_index] = result[parse_index]._replace(
                                            value=value, 
                                            size=data_item_length
                                        )
                                    if data_return_code != const.ReturnCode.SUCCESS:
                                        result[parse_index] = result[parse_index]._replace(
                                            error=str(ReturnCode(data_return_code))
                                        )
                    previous_index = total_items_index
            except Exception as exception:
                item = item._replace(error=str(exception))
                result[total_items_index] = item

        return result


    def write_area(self, item_list:list=[]) -> list:
        """
        Write data area

        Args:
            item_list(list): list of items to be requested
        Returns:
            result(list): same list of items as input but with values       
        """

        request = bytearray(const.S7_READ_WRITE[0:19]) # up to item count
        data_payload = bytearray()
        item_count = 0
        total_pdu = 0
        previous_index = 0

        total_items = len(item_list)
        result = [Tag()] * total_items 
        total_items_index = 0
        while total_items_index < total_items:
            try:
                # extract item
                item = item_list[total_items_index]
                item = item._replace(error="Not Sent")
                result[total_items_index] = item
                # extract area type
                skip = False
                area_type = util.get_all_alpha(address=item.address)
                try:
                    area = util.get_area_from_name(Name=area_type[0])
                except Exception as exception:
                    item = item._replace(error=str(exception))
                    skip = True

                if item.value is None:
                    item = item._replace(error="Missing Value")
                    skip = True

                # string is its own BS
                if item.type == const.DataType.STRING and not skip:
                    string_length = len(item.value)
                    string_value = item.value
                    if string_length > 254:
                        string_length = 254
                        string_value = string_value[:string_length]
                    item = item._replace(value=string_value, size=string_length)
                    response = self.write_area_raw(
                        address=item.address, 
                        raw_bytes=util.encode(item=item, endian=self.endian)
                    )
                    item = item._replace(error=response[0].error)
                    skip = True

                if skip:
                    result[total_items_index] = item
                    total_items_index += 1
                    continue

                # get item length
                data_item_length = util.get_data_size_byte(item.type)

                if total_items_index < total_items:
                    next_item_size = util.calculate_write_item_size(item_list[total_items_index])
                else:
                    next_item_size = util.calculate_write_item_size(item_list[total_items_index-1])

                # message must not exceed total PDU length
                send = True
                # frame_header (up to item count) + current_pdu + next_item
                if 19 + total_pdu + next_item_size < self._pdu_length:
                    send = False
                    total_pdu += util.calculate_write_item_size(item)
                    total_items_index += 1
                    item_count += 1
                    # get numbers 
                    number_type = util.get_all_numeric(address=item.address)
                    # get transport size
                    if (area == const.Area.COUNTER_S7):
                        transport_size = const.DataType.COUNTER
                    elif (area == const.Area.TIMER_S7):
                        transport_size = const.DataType.TIMER
                    else:
                        transport_size = item.type
                        if transport_size != const.DataType.BIT:
                            transport_size = const.DataType.BYTE

                    # get DB number
                    db_number = number_type[0]
                    # calculate address
                    # byte address + bit address
                    address = (number_type[1] << 3) + number_type[2]
                    address_bytes = struct.pack(
                        'BBB',
                        (address >> 16) & 0xFF,
                        (address >> 8) & 0xFF,
                        (address >> 0) & 0xFF
                    )
                    item_info = struct.pack(
                        f'{self.endian}BBBBHHB', 
                        0x12, # variable specifications
                        0x0A, # length of address specification
                        0x10, # syntax id: S7ANY
                        transport_size, 
                        data_item_length,
                        db_number,
                        area
                    )
                    request += (item_info + address_bytes)
                    # set data transport size
                    # Set transport size and data length
                    if (transport_size == const.DataType.BIT):
                        transport_size = const.TransportSize.BIT
                        corrected_data_item_length = data_item_length
                    elif (transport_size == const.DataType.COUNTER or transport_size == const.DataType.TIMER):
                        transport_size = const.TransportSize.OCTET_STRING
                        corrected_data_item_length = data_item_length + 1
                    else:
                        transport_size = const.TransportSize.BYTE_WORD_DWORD
                        corrected_data_item_length = data_item_length << 3
                    data_payload += (
                        struct.pack(
                            f'{self.endian}BBH', 
                            const.ReturnCode.RESERVED,
                            transport_size,
                            corrected_data_item_length
                        ) + util.encode(item=item, endian=self.endian)
                    )

                # see if max PDU length has been exceed or that end of items list
                if send or total_items_index >= total_items:
                    # update parameter
                    request[17] = const.Function.WRITE_VARIABLE
                    request[18] = item_count
                    # append data
                    request += data_payload
                    header_param_length = 2 + (item_count * 12)
                    struct.pack_into(f'{self.endian}H', request, 13, header_param_length)
                    header_data_length = len(data_payload)
                    struct.pack_into(f'{self.endian}H', request, 15, header_data_length)
                    tpkt_length = 17 + header_param_length + header_data_length
                    struct.pack_into(f'{self.endian}H', request, 2, tpkt_length)
                    # send request
                    self._send(send_data=request)
                    # reset param afer sending
                    total_pdu = 0
                    item_count = 0
                    request = bytearray(const.S7_READ_WRITE[0:19]) # up to item count
                    data_payload = bytearray()
                    data = self._recv()
                    # parse up to this message
                    tpkt_length = struct.unpack_from(f'{self.endian}H', data, 2)[0]
                    # minimum is 1 response
                    if (tpkt_length < 22):
                        self.__log.error(f"self.write_area(): Invalid PDU size")
                        raise CommTypeError("Invalid PDU size")
                    else:
                        (
                            header_error_class, 
                            header_error_code, 
                            param_function, 
                            param_item_count
                        ) = struct.unpack_from('BBBB', data, 17)
                        if header_error_class != const.ErrorClass.NO_ERROR or header_error_code != 0:
                            self.__log.error(f"self.write_area(): Invalid PDU size")
                            raise CommTypeError("Invalid PDU size")
                        else:
                            # match item from main loop
                            data_offset = 21 # index 0
                            for parse_index in range(previous_index, total_items_index):
                                # string has been handled, so skip
                                if (
                                    item_list[parse_index].type != const.DataType.STRING 
                                    and item_list[parse_index].value != None
                                    and result[parse_index].error == ''
                                ):
                                    data_return_code = struct.unpack_from(
                                        'B', 
                                        data,
                                        data_offset
                                    )[0]
                                    if data_return_code != const.ReturnCode.SUCCESS:
                                        result[parse_index] = result[parse_index]._replace(
                                            error=str(ReturnCode(data_return_code))
                                        )
                                    else:
                                        result[parse_index] = result[parse_index]._replace(error='')
                                    data_offset += 1
                    previous_index = total_items_index
            except Exception as exception:
                item = item._replace(error=str(exception))
                result[total_items_index] = item

        return result
