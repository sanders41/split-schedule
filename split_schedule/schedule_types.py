from typing import List, Set, TypedDict


class BaseSchedule(TypedDict):
    block: int
    class_name: str


class ScheduleTotalStudents(BaseSchedule):
    total_students: int


class ReducedClass(ScheduleTotalStudents):
    max_students: int
    num_classes: int


class ScheduleDays(ReducedClass):
    classes: List[Set]
