import pandas as pd
import pytest

from math import ceil, floor
from pathlib import Path


ASSETS_PATH= Path().absolute().joinpath('tests/assets/')
TEST_FILE_PATH = ASSETS_PATH.joinpath('classes.xlsx')


def init_classes_check(class_size, reduce_by, smallest_allowed):
    reduce_classes = reduce_classes_check(reduce_by, smallest_allowed, class_size)
    total_classes = total_classes_check(reduce_classes)
    classes: List[ScheduleDays] = []
        
    for c in class_size:
        class_append: ScheduleDays = c # type: ignore
        class_list: List[Set] = []
        for i in range(total_classes):
            class_list.append(set())

        class_append['classes'] = class_list
        classes.append(class_append)

    return classes


def reduce_classes_check(reduce_by, smallest_allowed, class_size):
    check_reduced = class_size
    
    for c in check_reduced:
        reduced = floor(c['total_students']  * reduce_by)
        if reduced > smallest_allowed:
            size = reduced
        else:
            size = smallest_allowed

        num_classes = ceil(c['total_students'] / size)
        c['max_students'] = size
        c['num_classes'] = num_classes

    return check_reduced


def total_classes_check(reduced_classes):
    check_total_classes = 1
    for c in reduced_classes:
        if c['num_classes'] > check_total_classes:
            check_total_classes = c['num_classes']
    
    return check_total_classes