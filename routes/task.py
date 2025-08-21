from fastapi import APIRouter, HTTPException, Query, status

from typing import Annotated

from depends import auth_depends
from record import Record
from printer import GoDexPrinter, PrinterState

router = APIRouter(
    prefix="/task",
    tags=["Task"],
    dependencies=[auth_depends]
)


@router.put("/add/{record_id}")
def get_task(record_id: int, c: Annotated[int, Query(ge=1)]) -> None:
    try:
        record = Record.find_by_id(record_id)
        with GoDexPrinter.open() as printer:
            state, _ = printer.get_state()
            if state != PrinterState.IDLE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Printer is busy"
                )

            printer.send_command([
                "^XSETCUT,DOUBLECUT,0",
                "^Q20,3",
                "^W50",
                "^H9",
                "^P1",
                "^S4",
                "^AD",
                f"^C{c}",
                "^R0",
                "~Q+0",
                "^O0",
                "^D0",
                "^E18",
                "~R255",
                "^L",
                f"AD,144,12,1,1,0,0E,{record.name}",
                f"AC,144,52,1,1,0,0E,{record.year}-{str(record.month).zfill(2)}-{str(record.day).zfill(2)}",
                f"AZ1,144,86,1,1,0,0,{record.operator_name}{f' ({record.operator_code})' if record.operator_code else ''}",
                "W8,16,1,2,M0,8,6,17,0",
                f"{record.id}",
                "E",
            ])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record with ID {record_id} not found."
        )
