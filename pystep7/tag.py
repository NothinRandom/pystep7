"""
This file is a collection of data storage mechanisms.
"""

from typing import NamedTuple, Any, Optional
from reprlib import repr as _r


__all__ = ["Tag"]


class Tag(NamedTuple):
    name: Optional[str] = ''        #: friendly ID
    address: Optional[str] = ''     #: address space
    value: Optional[Any] = None     #: value read/written, may be ``None`` on error
    size: Optional[int] = 0         #: length of value, useful for string
    type: Optional[str] = ''        #: data type of element (bit, byte, char, etc)
    error: Optional[str] = ''       #: error message if unsuccessful, else ``None``


    def __bool__(self):
        """
        ``True`` if both ``value`` is not ``None`` and ``error`` is ``None``
        ``False`` otherwise
        """
        return self.value is not None and self.error is None


    def __str__(self):
        return (
            f"{self.name}, "
            f"{self.address}, "
            f"{_r(self.value)}, "
            f"{self.size}, "
            f"{self.type}, "
            f"{self.error}"
        )


    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"address={self.address!r}, "
            f"value={self.value!r}, "
            f"size={self.size!r}, "
            f"type={self.type!r}, "
            f"error={self.error!r})"
        )


class CPUInfo(NamedTuple):
    systemName: Optional[str] = ''      # name (e.g. 'R08ENCPU')
    moduleName: Optional[str] = ''      # code (e.g. '4806')
    plantId: Optional[str] = ''         # code (e.g. '4806')
    copyright: Optional[str] = ''       # code (e.g. '4806')
    serialNumber: Optional[str] = ''    # code (e.g. '4806')
    cpuType: Optional[str] = ''         # code (e.g. '4806')
    memSerialNumber: Optional[str] = '' # code (e.g. '4806')
    manufacturerId: Optional[str] = ''  # code (e.g. '4806')
    profileId: Optional[str] = ''       # code (e.g. '4806')
    profileSpec: Optional[str] = ''     # code (e.g. '4806')
    oemCopyright: Optional[str] = ''    # code (e.g. '4806')
    oemId: Optional[str] = ''           # code (e.g. '4806')
    oemAddId: Optional[str] = ''        # code (e.g. '4806')
    locationId: Optional[str] = ''      # code (e.g. '4806')
    error: Optional[str] = ''


    def __str__(self):
        return (
            f"{self.systemName},"
            f"{self.moduleName},"
            f"{self.plantId},"
            f"{self.copyright},"
            f"{self.serialNumber},"
            f"{self.cpuType},"
            f"{self.memSerialNumber},"
            f"{self.manufacturerId},"
            f"{self.profileId},"
            f"{self.profileSpec},"
            f"{self.oemCopyright},"
            f"{self.oemId},"
            f"{self.oemAddId},"
            f"{self.locationId},"
            f"{self.error}"
        )


    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"systemName={self.systemName!r}, "
            f"moduleName={self.moduleName!r}, "
            f"plantId={self.plantId!r}, "
            f"copyright={self.copyright!r}, "
            f"serialNumber={self.serialNumber!r}, "
            f"cpuType={self.cpuType!r}, "
            f"memSerialNumber={self.memSerialNumber!r}, "
            f"manufacturerId={self.manufacturerId!r}, "
            f"profileId={self.profileId!r}, "
            f"profileSpec={self.profileSpec!r}, "
            f"oemCopyright={self.oemCopyright!r}, "
            f"oemId={self.oemId!r}, "
            f"oemAddId={self.oemAddId!r}, "
            f"locationId={self.locationId!r}"
            f"error={self.error!r}"
            ")"
        )


class CatalogCode(NamedTuple):
    moduleOrderNumber: Optional[str] = ''   # status (e.g. 'Stop')
    moduleVersion: Optional[str] = ''
    basicHardwareId: Optional[str] = ''     # status (e.g. 'Unknown')
    hardwareVersion: Optional[str] = ''
    basicFirmwareId: Optional[str] = ''     # status (e.g. 'Unknown')
    firmwareVersion: Optional[str] = ''
    firmwareExtensionId: Optional[str] = '' # status (e.g. 'Unknown')
    firmwareExtVersion: Optional[str] = ''  # status (e.g. '9.1')
    error: Optional[str] = ''


    def __str__(self):
        return (
            f"{self.moduleOrderNumber},"
            f"{self.moduleVersion},"
            f"{self.basicHardwareId},"
            f"{self.hardwareVersion},"
            f"{self.basicFirmwareId},"
            f"{self.firmwareVersion},"
            f"{self.firmwareExtensionId},"
            f"{self.firmwareExtVersion},"
            f"{self.error}"
        )


    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"moduleOrderNumber={self.moduleOrderNumber!r}, "
            f"moduleVersion={self.moduleVersion!r}, "
            f"basicHardwareId={self.basicHardwareId!r}), "
            f"hardwareVersion={self.hardwareVersion!r}), "
            f"basicFirmwareId={self.basicFirmwareId!r}, "
            f"firmwareVersion={self.firmwareVersion!r}, "
            f"firmwareExtensionId={self.firmwareExtensionId!r}, "
            f"firmwareExtVersion={self.firmwareExtVersion!r}, "
            f"error={self.error!r}"
            ")"
        )


class CPUStatus(NamedTuple):
    requestedMode: Optional[str] = ''   # status (e.g. 'Stop')
    previousMode: Optional[str] = ''    # status (e.g. 'Unknown')
    error: Optional[str] = ''

    def __str__(self):
        return f"{self.requestedMode},{self.previousMode},{self.error}"


    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"requestedMode={self.requestedMode!r}, "
            f"previousMode={self.previousMode!r}, "
            f"error={self.error!r}"
            ")"
        )


class CommProc(NamedTuple):
    maxPDU: Optional[int] = 0           # status (e.g. 240)
    maxConnections: Optional[int] = 0   # status (e.g. 32)
    mpiRate: Optional[int] = 0          # status (e.g. 12000000)
    mkbusRate: Optional[int] = 0        # status (e.g. 187500)
    error: Optional[str] = ''


    def __str__(self):
        return (
            f"{self.maxPDU},"
            f"{self.maxConnections},"
            f"{self.mpiRate},"
            f"{self.mkbusRate},"
            f"{self.error}"
        )


    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"maxPDU={self.maxPDU!r}, "
            f"maxConnections={self.maxConnections!r}, "
            f"mpiRate={self.mpiRate!r}, "
            f"mkbusRate={self.mkbusRate!r}, "
            f"error={self.error!r}"
            ")"
        )


class Protection(NamedTuple):
    protectionLevel: Optional[int] = 1      # protection level (1,2,3)
    passwordLevel: Optional[int] = 0        # password level (0,1,2,3)
    validProtectionLevel: Optional[int] = 0 # valid protection level (0,1,2,3)
    modeSelector: Optional[str] = ''        # mode selector setting
                                            #   1: Run
                                            #   2: Run-Protected
                                            #   3: Stop
                                            #   4: Memory Reset
    startupSwitch: Optional[str] = ''       # startup switch setting (0,1,2)
                                            #   0: Undefined
                                            #   1: Cold Restart
                                            #   2: Warm Restart
    error: Optional[str] = ''


    def __str__(self):
        return (
            f"{self.protectionLevel},"
            f"{self.passwordLevel},"
            f"{self.validProtectionLevel},"
            f"{self.modeSelector},"
            f"{self.startupSwitch},"
            f"{self.error}"
        )


    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"protectionLevel={self.protectionLevel!r}, "
            f"passwordLevel={self.passwordLevel!r}, "
            f"validProtectionLevel={self.validProtectionLevel!r}, "
            f"modeSelector={self.modeSelector!r}, "
            f"startupSwitch={self.startupSwitch!r}, "
            f"error={self.error!r}"
            ")"
        )


class BlockInfo(NamedTuple):
    flags: Optional[str] = ''
    language: Optional[str] = ''
    type: Optional[str] = ''
    number: Optional[int] = 0
    loadMemory: Optional[int] = 0
    security: Optional[str] = ''
    codeTimestamp: Optional[str] = ''
    interfaceTimestamp: Optional[str] = ''
    ssbLength: Optional[int] = 0
    addLength: Optional[int] = 0
    localDataLength: Optional[int] = 0
    mc7Length: Optional[int] = 0
    author: Optional[str] = ''
    family: Optional[str] = ''
    name: Optional[str] = ''
    version: Optional[str] = ''
    checksum: Optional[str] = ''
    error: Optional[str] = ''

    def __str__(self):
        return (
            f"{self.flags},"
            f"{self.language},"
            f"{self.type},"
            f"{self.number},"
            f"{self.loadMemory},"
            f"{self.security},"
            f"{self.codeTimestamp},"
            f"{self.interfaceTimestamp},"
            f"{self.ssbLength},"
            f"{self.addLength},"
            f"{self.localDataLength},"
            f"{self.mc7Length},"
            f"{self.author},"
            f"{self.family},"
            f"{self.name},"
            f"{self.version},"
            f"{self.checksum},"
            f"{self.error}"
        )


    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"flags={self.flags!r}, "
            f"language={self.language!r}, "
            f"type={self.type!r}, "
            f"number={self.number!r}, "
            f"loadMemory={self.loadMemory!r}, "
            f"security={self.security!r}, "
            f"codeTimestamp={self.codeTimestamp!r}, "
            f"interfaceTimestamp={self.interfaceTimestamp!r}, "
            f"ssbLength={self.ssbLength!r}, "
            f"addLength={self.addLength!r}, "
            f"localDataLength={self.localDataLength!r}, "
            f"mc7Length={self.mc7Length!r}, "
            f"author={self.author!r}, "
            f"family={self.family!r}, "
            f"name={self.name!r}, "
            f"version={self.version!r}, "
            f"checksum={self.checksum!r}, "
            f"error={self.error!r}"
            ")"
        )


class CPUDiagnostics(NamedTuple):
    eventId: Optional[str] = ''     #
    description: Optional[str] = '' #
    priority: Optional[int] = 0     #
    obNumber: Optional[int] = 0     #
    datId: Optional[str] = ''       #
    info1: Optional[str] = ''       #
    info2: Optional[str] = ''       #
    timestamp: Optional[Any] = None #
    error: Optional[str] = ''       #


    def __str__(self):
        return (
            f"{self.eventId},"
            f"{self.description},"
            f"{self.priority},"
            f"{self.obNumber},"
            f"{self.datId},"
            f"{self.info1},"
            f"{self.info2},"
            f"{self.timestamp},"
            f"{self.error}"
        )


    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"eventId={self.eventId!r}, "
            f"description={self.description!r}, "
            f"priority={self.priority!r}, "
            f"obNumber={self.obNumber!r}, "
            f"datId={self.datId!r}, "
            f"info1={self.info1!r}, "
            f"info2={self.info2!r}, "
            f"timestamp={self.timestamp!r}, "
            f"error={self.error!r}"
            ")"
        )


class CPULed(NamedTuple):
    rack: Optional[int] = 0             #
    type: Optional[int] = 0             #
    id: Optional[str] = ''              #
    on: Optional[int] = 0               #
    flashing: Optional[bool] = False    #
    error: Optional[str] = ''           #

    def __str__(self):
        return (
            f"{self.rack},"
            f"{self.type},"
            f"{self.id},"
            f"{self.on},"
            f"{self.flashing},"
            f"{self.error}"
        )


    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"rack={self.rack!r}, "
            f"type={self.type!r}, "
            f"id={self.id!r}, "
            f"on={self.on!r}, "
            f"flashing={self.flashing!r}, "
            f"error={self.error!r}"
            ")"
        )
