from ctypes import cdll, CDLL, create_string_buffer, pointer
from enum import Enum
from os.path import abspath
from platform import system
from queue import Queue
from threading import Lock
from time import time
from typing import Any, Iterable, Literal, overload, Optional, Union

from config import DLL_PATH


class PrinterState(Enum):
    IDLE = "00"                 # 00 – 待機狀態
    OUT_OF_SUPPLIES = "01"      # 01 – 耗材用盡
    PAPER_JAM = "02"            # 02 – 卡紙
    RIBBON_OUT = "03"           # 03 – 碳帶用盡
    HEAD_OPEN = "04"            # 04 – 印表頭開啟(此功能限於有Door Open Switch Sensor 的機種)
    RECYCLER_FULL = "05"        # 05 – 背紙回收器已滿
    FILE_SYSTEM_FULL = "06"     # 06 – 檔案系統已滿
    FILE_NOT_FOUND = "07"       # 07 – 找不到檔案
    FILE_NAME_DUPLICATE = "08"  # 08 – 檔名重複
    SYNTAX_ERROR = "09"         # 09 – 指令語法錯誤
    CUTTER_JAMMED = "10"        # 10 – 裁刀卡住或未安裝裁刀
    NO_EXT_MEMORY = "11"        # 11 – 無延伸記憶體
    WAITING_FOR_LABEL = "13"    # 13 – 等待取走標籤
    PAUSED = "20"               # 20 – 暫停
    SETUP_MODE = "21"           # 21 – 設定模式
    KEYBOARD_MODE = "22"        # 22 – 鍵盤模式
    PRINTING = "50"             # 50 – 印表機列印中
    PROCESSING_DATA = "60"      # 60 – 資料處理中
    HEAD_OVERHEAT = "62"        # 62 – 印表頭過熱
    UNKNOWN = "99"              # 99 – 未知狀態

    @staticmethod
    def from_code(code: Union[str, bytes]) -> "PrinterState":
        if isinstance(code, str):
            key = code.strip()
        elif isinstance(code, bytes):
            key = code.decode("utf-8").strip()
        else:
            raise ValueError("Invalid type for code, must be str or bytes")

        result = PrinterState._value2member_map_.get(key, PrinterState.UNKNOWN)
        return result  # type: ignore


PrinterStateLiteral = Literal[
    "IDLE",
    "OUT_OF_SUPPLIES",
    "PAPER_JAM",
    "RIBBON_OUT",
    "HEAD_OPEN",
    "RECYCLER_FULL",
    "FILE_SYSTEM_FULL",
    "FILE_NOT_FOUND",
    "FILE_NAME_DUPLICATE",
    "SYNTAX_ERROR",
    "CUTTER_JAMMED",
    "NO_EXT_MEMORY",
    "WAITING_FOR_LABEL",
    "PAUSED",
    "SETUP_MODE",
    "KEYBOARD_MODE",
    "PRINTING",
    "PROCESSING_DATA",
    "HEAD_OVERHEAT",
    "UNKNOWN",
]


class PrinterSession:
    __dll: CDLL
    __lock: Lock
    __last_cache: float = 0
    __last_cache_result: tuple[PrinterState, int] = (PrinterState.UNKNOWN, 0)

    def __init__(self, dll: CDLL, lock: Lock) -> None:
        self.__dll = dll
        self.__lock = lock

    def __enter__(self) -> "PrinterSession":
        if system() == "Windows":
            if (self.__dll.openport(b"6") != 1):
                raise Exception("Failed to open printer")
        else:
            if (self.__dll.openUSB() != 1):
                raise Exception("Failed to open printer")
        return self

    def __exit__(self, exc_type: Optional[type], exc_value: Optional[BaseException], traceback: Optional[Any]) -> None:
        if system() == "Windows":
            self.__dll.closeport()
        else:
            self.__dll.closeUSB()

    def send_command(self, command: Union[str, bytes, Iterable[str], Iterable[bytes]]) -> None:
        if isinstance(command, str):
            rv = self.__dll.sendcommand(command.encode("utf-8"))
        elif isinstance(command, bytes):
            rv = self.__dll.sendcommand(command)
        else:
            for element in command:
                if isinstance(element, str):
                    element = element.encode("utf-8")
                elif not isinstance(element, bytes):
                    raise TypeError("Command elements must be str or bytes")
                if (self.__dll.sendcommand(command) != 1):
                    raise Exception(f"Failed to send command: {command}")
            return
        if (rv != 1):
            raise Exception(f"Failed to send command: {command}")

    def receive_buffer(self, retry_times: int = 3) -> bytes:
        buffer = create_string_buffer(1024)
        try:
            length = -1
            for _ in range(max(retry_times, 1)):
                length = self.__dll.RcvBuf(buffer, 1024)
                if length > 0:
                    break
            result = buffer.raw[:length] if length > 0 else b""

            if length < 0:
                raise Exception("Failed to receive data from printer")
            return result
        finally:
            buffer = None

    def get_state(self) -> tuple[PrinterState, int]:
        self.__lock.acquire()

        cls = self.__class__
        if time() - cls.__last_cache < 1:
            if cls.__last_cache_result is not None:
                self.__lock.release()
                return cls.__last_cache_result

        self.send_command("~S,STATUS")
        response = self.receive_buffer()
        state, count = response.decode("utf-8").split(",", 2)

        result = PrinterState.from_code(state), int(count.strip())
        cls.__last_cache_result = result
        cls.__last_cache = time()

        self.__lock.release()
        return result

    def pause(self) -> None:
        if self.get_state() == PrinterState.PRINTING:
            self.send_command("~S,PAUSE")

    def resume(self) -> None:
        if self.get_state() == PrinterState.PAUSED:
            self.send_command("~S,PAUSE")

    def cancel(self) -> None:
        self.send_command("~S,CANCEL")

    def backward(self, mm: int) -> None:
        if not isinstance(mm, int):
            raise TypeError("Backward distance must be an integer")
        if mm < 1 or mm > 1000:
            raise ValueError("Backward distance must be between 1 and 1000 mm")
        self.send_command(f"^B{mm}")

    def forward(self, mm: int) -> None:
        if not isinstance(mm, int):
            raise TypeError("Forward distance must be an integer")
        if mm < 1 or mm > 1000:
            raise ValueError("Forward distance must be between 1 and 1000 mm")
        self.send_command(f"^M{mm}")

    def set_buzzer(self, enabled: bool) -> None:
        self.send_command(f"^XSET,BUZZER,{1 if enabled else 0}")


class GoDexPrinter:
    __dll: Optional[CDLL] = None
    __lock: Lock = Lock()

    @classmethod
    def open(cls) -> PrinterSession:
        if cls.__dll is None:
            cls.__dll = cdll.LoadLibrary(abspath(
                DLL_PATH if DLL_PATH else
                "EZio64.dll" if system() == "Windows" else
                "libezio.so"
            ))
        return PrinterSession(cls.__dll, cls.__lock)
