from fastapi import APIRouter
from pydantic import BaseModel

from depends import auth_depends, PrinterDepends
from printer import GoDexPrinter, PrinterState, PrinterStateLiteral

router = APIRouter(
    prefix="/printer",
    tags=["Printer"],
    dependencies=[auth_depends]
)


class StateResponse(BaseModel):
    state: PrinterStateLiteral
    queue: int


@router.get("/state")
def get_printer_state() -> StateResponse:
    try:
        with GoDexPrinter.open() as printer:
            state, queue = printer.get_state()
        return StateResponse(state=state.name, queue=queue)
    except:
        return StateResponse(state=PrinterState.UNKNOWN.name, queue=0)


@router.get("/raw-pause")
def raw_pause_printer(printer: PrinterDepends) -> None:
    printer.send_command("~S,PAUSE")

@router.get("/pause")
def pause_printer(printer: PrinterDepends) -> None:
    printer.pause()


@router.get("/resume")
def resume_printer(printer: PrinterDepends) -> None:
    printer.pause()


@router.get("/forward/{distance}")
def forward_printer(distance: int, printer: PrinterDepends) -> None:
    printer.forward(distance)


@router.get("/backward/{distance}")
def backward_printer(distance: int, printer: PrinterDepends) -> None:
    printer.backward(distance)
