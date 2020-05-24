import pandas as pd
import pytest

from math import ceil, floor
from pathlib import Path
from split_schedule.schedule_builder import ScheduleBuilder
from tests.helpers import init_classes_check, reduce_classes_check, total_classes_check


ASSETS_PATH= Path().absolute().joinpath('tests/assets/')
TEST_FILE_PATH = ASSETS_PATH.joinpath('classes.xlsx')


def test_create_fill_classes_days():
    total_classes = 1
    schedule_builder = ScheduleBuilder(str(TEST_FILE_PATH))
    fill_classes_days = schedule_builder._create_fill_classes_days(total_classes)


@pytest.mark.parametrize('reduce_by', [0.1, 0.2, 0.5])
@pytest.mark.parametrize('smallest_allowed', [1, 5, 10])
def test_fill_grouped_blocks(reduce_by, smallest_allowed):
    pass


def test_find_matches(student_matches_check):
    schedule_builder = ScheduleBuilder(str(TEST_FILE_PATH))
    matches = schedule_builder._find_matches()

    assert matches == student_matches_check


def test_get_class_size(class_size_check):
    schedule_builder = ScheduleBuilder(str(TEST_FILE_PATH))
    class_size = schedule_builder._get_class_size()
    assert class_size == class_size_check


def test_get_student_classes(student_classes_check):
    schedule_builder = ScheduleBuilder(str(TEST_FILE_PATH))
    student_classes = schedule_builder._get_student_classes()

    assert student_classes == student_classes_check


@pytest.mark.parametrize('reduce_by', [0.1, 0.2, 0.5])
@pytest.mark.parametrize('smallest_allowed', [1, 5, 10])
def test_get_total_classes(class_size_check, reduce_by, smallest_allowed):
    reduced_classes = reduce_classes_check(reduce_by, smallest_allowed, class_size_check)
    check_total_classes = total_classes_check(reduced_classes)

    schedule_builder = ScheduleBuilder(str(TEST_FILE_PATH))
    total_classes = schedule_builder._get_total_classes(reduced_classes)

    assert total_classes == check_total_classes


def test_group_blocks(group_blocks_check):
    schedule_builder = ScheduleBuilder(str(TEST_FILE_PATH))
    group_blocks = schedule_builder._group_blocks()

    assert group_blocks == group_blocks_check


@pytest.mark.parametrize('reduce_by', [0.1, 0.2, 0.5])
@pytest.mark.parametrize('smallest_allowed', [1, 5, 10])
def test_init_classes(class_size_check, reduce_by, smallest_allowed):
    expected = init_classes_check(class_size_check, reduce_by, smallest_allowed)
    schedule_builder = ScheduleBuilder(str(TEST_FILE_PATH))
    classes = schedule_builder._init_classes(reduce_by, smallest_allowed)

    assert classes == expected


def test_init_schedule_builder():
    schedule_builder = ScheduleBuilder(str(TEST_FILE_PATH))
    test = pd.read_excel(str(TEST_FILE_PATH))

    assert test.equals(schedule_builder.schedule_df)


@pytest.mark.parametrize('reduce_by', [0.1, 0.2, 0.5])
@pytest.mark.parametrize('smallest_allowed', [1, 5, 10])
def test_reduce_class(class_size_check, reduce_by, smallest_allowed):
    check_reduced = reduce_classes_check(reduce_by, smallest_allowed, class_size_check)

    schedule_builder = ScheduleBuilder(str(TEST_FILE_PATH))
    reduced_class = schedule_builder._reduce_class(class_size_check, reduce_by, smallest_allowed)

    assert reduced_class == check_reduced


def test_save_schedule_to_file(tmp_path):
    EXPORT_PATH = tmp_path.joinpath('schedule.xlsx')
    test = {
        'day_number': [0, 0, 1, 2],
        'block': [1, 1, 2, 2],
        'class': ['test 1', 'test 2', 'test 3', 'test 4']
    }

    df = pd.DataFrame(test)

    schedule_builder = ScheduleBuilder(str(TEST_FILE_PATH))
    schedule_builder._save_schedule_to_file(df, str(EXPORT_PATH))

    assert EXPORT_PATH.exists()


def test_save_schedule_check_columns(tmp_path):
    EXPORT_PATH = tmp_path.joinpath('schedule.xlsx')
    test = {
        'day_number': [0, 0, 1, 2],
        'block': [1, 1, 2, 2],
        'class': ['test 1', 'test 2', 'test 3', 'test 4']
    }

    df = pd.DataFrame(test)

    EXPORT_PATH = tmp_path.joinpath('schedule.xlsx')

    schedule_builder = ScheduleBuilder(str(TEST_FILE_PATH))
    schedule_builder._save_schedule_to_file(df, str(EXPORT_PATH))
    df_saved = pd.read_excel(EXPORT_PATH)
    columns = df_saved.columns.values.tolist()

    assert columns == ['day_number', 'block', 'class']