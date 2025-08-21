from pydantic import BaseModel

from typing import Literal, Optional

from db import get_cursor


class Record(BaseModel):
    id: int
    name: str
    year: int
    month: int
    day: int
    operation_type: Literal["DIFF", "MID", "CHILD", "SEC"]
    operator_name: str
    operator_code: Optional[str] = None

    @staticmethod
    def find_by_id(id: int) -> "Record":
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT r.id, r.name, r.year, r.month, r.day, r.operation_type, o.name, o.code
                FROM public.hash_records r
                INNER JOIN public.operators o
                ON r.operator_id = o.id
                WHERE r.id = %s;
            """, (id,))

            result = cursor.fetchone()
            if result is None:
                raise ValueError(f"Record with id {id} not found.")
            (
                q_id,
                q_name,
                q_year,
                q_month,
                q_day,
                q_operation_type,
                q_operator_name,
                q_operator_code
            ) = result
            return Record(
                id=q_id,
                name=q_name,
                year=q_year,
                month=q_month,
                day=q_day,
                operation_type=q_operation_type,
                operator_name=q_operator_name,
                operator_code=q_operator_code
            )
