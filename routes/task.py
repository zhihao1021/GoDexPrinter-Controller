from fastapi import APIRouter, HTTPException, Query, status

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


def generate_command(
    count: int,
    record: Record,
    remark: Optional[str] = None
) -> list[str]:
    operation_type = "分化" if record.operation_type == "DIFF" \
        else "中間橋" if record.operation_type == "MID" \
        else "子瓶" if record.operation_type == "CHILD" \
        else "二次瓶"

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
        f"AD,144,12,1,1,0,0E,{record.name}",
        f"AB,144,46,1,1,0,0E,{record.year}-{str(record.month).zfill(2)}-{str(record.day).zfill(2)}",
        f"AZ1,144,72,1,1,0,0,{record.operator_name}{f' ({record.operator_code})' if record.operator_code else ''}",
        f"AZ1,144,96,1,1,0,0,{operation_type}"
    ]

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
