from typing import List, TypedDict, Set


class BaseSchedule(TypedDict):
    block: int
    class_name: str


class ScheduleTotalStudents(BaseSchedule):
    total_students: int


class StudentClass(BaseSchedule):
    student: str


class Classes(BaseSchedule):
    students: List[StudentClass]


class GroupedBlock(TypedDict):
    block: int
    classes: List[Classes]


class ReducedClass(ScheduleTotalStudents):
    max_students: int
    num_classes: int


class ScheduleDays(ReducedClass):
    classes: List[Set]