from fastapi import APIRouter, HTTPException, Query, status
from PIL import ImageFont

from time import sleep
from typing import Annotated, Optional

from depends import auth_depends
from record import Record
from printer import GoDexPrinter, PrinterState

router = APIRouter(
    prefix="/task",
    tags=["Task"],
    dependencies=[auth_depends]
)

FONT_12 = ImageFont.truetype("./arial.ttf", 12)
FONT_14 = ImageFont.truetype("./arial.ttf", 14)
FONT_16 = ImageFont.truetype("./arial.ttf", 16)
FONT_18 = ImageFont.truetype("./arial.ttf", 18)

def get_font_width_param(text: str) -> str:
    width_18 = int(FONT_18.getbbox(text)[2])
    if width_18 < 64:
        return "AF,140,0,1,1"
    width_16 = int(FONT_16.getbbox(text)[2])
    if width_16 < 64:
        return "AB,140,4,2,2"
    width_14 = int(FONT_14.getbbox(text)[2])
    if width_14 < 64:
        return "AE,140,8,1,1"
    width_12 = int(FONT_12.getbbox(text)[2])
    if width_12 < 64:
        return "AD,140,12,1,1"
    return "AC,140,12,1,1"

def generate_command(
    count: int,
    record: Record,
    remark: Optional[str] = None
) -> list[str]:
    operation_type = "分化" if record.operation_type == "DIFF" \
        else "中間橋" if record.operation_type == "MID" \
        else "子瓶" if record.operation_type == "CHILD" \
        else "二次瓶"
    
    record_param = get_font_width_param(record.name)

    result = [
        "^XSETCUT,DOUBLECUT,0",
        "^Q20,3",
        "^W50",
        "^H9",
        "^P1",
        "^S4",
        "^AD",
        f"^C{count}",
        "^R0",
        "~Q+0",
        "^O0",
        "^D0",
        "^E18",
        "~R255",
        "^L",
        f"{record_param},0,0E,{record.name}",
        # f"AB,144,46,1,1,0,0E,{record.year}-{str(record.month).zfill(2)}-{str(record.day).zfill(2)}",
        f"AD,140,46,1,1,0,0E,{record.year}-{str(record.month).zfill(2)}-{str(record.day).zfill(2)}", # Bigger version
        # f"AZ1,144,72,1,1,0,0,{record.operator_name}{f' ({record.operator_code})' if record.operator_code else ''}",
        # f"AZ1,144,72,1,1,0,0,{record.operator_name}",
        f"AZ1,140,82,1,1,0,0,{record.operator_name}", # Bigger version
        # f"AZ1,144,96,1,1,0,0,{operation_type}",
        f"AZ1,140,114,1,1,0,0,{operation_type}", # Bigger version
    ]

    if record.operator_code:
        # result.append(f"AD,232,68,1,1,0,0E,{record.operator_code}")
        result.append(f"AG,245,76,1,1,0,0E,{record.operator_code}") # Bigger version

    if remark:
        result.append(f"AZ1,144,120,1,1,0,0,{remark}")

    result += [
        "W8,16,1,2,M0,8,6,17,0",
        f"{record.id}",
        "E",
    ]

    return result


@router.get("/dryrun/{record_id}")
def dry_run(record_id: int) -> Record:
    try:
        record = Record.find_by_id(record_id)
        return record
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record with ID {record_id} not found."
        )


@router.put("/add/{record_id}")
def get_task(
    record_id: int,
    c: Annotated[int, Query(ge=1)],
    remark: Optional[str] = None,
    final_only: bool = False
) -> None:
    try:
        record = Record.find_by_id(record_id)
        with GoDexPrinter.open() as printer:
            state, _ = printer.get_state()
            if state != PrinterState.IDLE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Printer is busy"
                )

            if final_only and remark:
                printer.send_command(generate_command(
                    count=1,
                    record=record,
                    remark=remark
                ))
                sleep(1.5)
                if c > 1:
                    printer.send_command(generate_command(
                        count=c - 1,
                        record=record,
                    ))
            else:
                printer.send_command(generate_command(
                    count=c,
                    record=record,
                    remark=remark
                ))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record with ID {record_id} not found."
        )
