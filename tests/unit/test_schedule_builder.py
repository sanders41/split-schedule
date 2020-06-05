import pandas as pd
import pytest

from collections import Counter
from math import ceil, floor
from pathlib import Path
from split_schedule.schedule_builder import ScheduleBuilder
from tests.helpers import init_classes_check, reduce_classes_check, total_classes_check


def test_create_fill_classes_days(test_schedule):
    total_classes = 1
    schedule_builder = ScheduleBuilder(str(test_schedule))
    fill_classes_days = schedule_builder._create_fill_classes_days(total_classes)


@pytest.mark.parametrize('reduce_by', [0.1, 0.2, 0.5])
@pytest.mark.parametrize('smallest_allowed', [1, 5, 10])
def test_fill_grouped_blocks(reduce_by, smallest_allowed):
    pass


def test_find_matches(student_matches_check, test_schedule):
    schedule_builder = ScheduleBuilder(str(test_schedule))
    matches = schedule_builder._find_matches()

    assert matches == student_matches_check


def test_find_matches_retry(student_matches_check, test_schedule):
    schedule_builder = ScheduleBuilder(str(test_schedule))
    schedule_builder._find_matches()
    matches = schedule_builder._find_matches()

    m_keys = [x.keys() for x in matches]
    s_keys = [x.keys() for x in student_matches_check]
    m_vals = [[[sorted(z) for z in y] for y in (list(x.values()))] for x in matches]
    s_vals = [[[sorted(z) for z in y] for y in (list(x.values()))] for x in student_matches_check]
    assert m_keys == s_keys
    assert m_vals == s_vals


def test_get_class_size(class_size_check, test_schedule):
    schedule_builder = ScheduleBuilder(str(test_schedule))
    class_size = schedule_builder._get_class_size()
    assert class_size == class_size_check


def test_get_student_classes(student_classes_check, test_schedule):
    schedule_builder = ScheduleBuilder(str(test_schedule))
    student_classes = schedule_builder._get_student_classes()

    assert student_classes == student_classes_check


@pytest.mark.parametrize('reduce_by', [0.1, 0.2, 0.5])
@pytest.mark.parametrize('smallest_allowed', [1, 5, 10])
def test_get_total_classes(class_size_check, reduce_by, smallest_allowed, test_schedule):
    reduced_classes = reduce_classes_check(reduce_by, smallest_allowed, class_size_check)
    check_total_classes = total_classes_check(reduced_classes)

    schedule_builder = ScheduleBuilder(str(test_schedule))
    total_classes = schedule_builder._get_total_classes(reduced_classes)

    assert total_classes == check_total_classes


@pytest.mark.parametrize('reduce_by', [0.1, 0.2, 0.5])
@pytest.mark.parametrize('smallest_allowed', [1, 5, 10])
def test_init_classes(class_size_check, reduce_by, smallest_allowed, test_schedule):
    expected = init_classes_check(class_size_check, reduce_by, smallest_allowed)
    schedule_builder = ScheduleBuilder(str(test_schedule))
    classes = schedule_builder._init_classes(reduce_by, smallest_allowed)

    assert classes == expected


def test_init_schedule_builder(test_schedule):
    schedule_builder = ScheduleBuilder(str(test_schedule))
    test = pd.read_excel(str(test_schedule))

    assert test.equals(schedule_builder.schedule_df)


@pytest.mark.parametrize('reduce_by', [0.1, 0.2, 0.5])
@pytest.mark.parametrize('smallest_allowed', [1, 5, 10])
def test_reduce_class(class_size_check, reduce_by, smallest_allowed, test_schedule):
    check_reduced = reduce_classes_check(reduce_by, smallest_allowed, class_size_check)

    schedule_builder = ScheduleBuilder(str(test_schedule))
    reduced_class = schedule_builder._reduce_class(class_size_check, reduce_by, smallest_allowed)

    assert reduced_class == check_reduced


def test_save_schedule_to_file(tmp_path, test_schedule):
    EXPORT_PATH = tmp_path.joinpath('schedule.xlsx')
    test = {
        'day_number': [0, 0, 1, 2],
        'block': [1, 1, 2, 2],
        'class': ['test 1', 'test 2', 'test 3', 'test 4']
    }

    df = pd.DataFrame(test)

    schedule_builder = ScheduleBuilder(str(test_schedule))
    schedule_builder._save_schedule_to_file(df, str(EXPORT_PATH))

    assert EXPORT_PATH.exists()


def test_save_schedule_check_columns(tmp_path, test_schedule):
    EXPORT_PATH = tmp_path.joinpath('schedule.xlsx')
    test = {
        'day_number': [0, 0, 1, 2],
        'block': [1, 1, 2, 2],
        'class': ['test 1', 'test 2', 'test 3', 'test 4']
    }

    df = pd.DataFrame(test)

    EXPORT_PATH = tmp_path.joinpath('schedule.xlsx')

    schedule_builder = ScheduleBuilder(str(test_schedule))
    schedule_builder._save_schedule_to_file(df, str(EXPORT_PATH))
    df_saved = pd.read_excel(EXPORT_PATH)
    columns = df_saved.columns.values.tolist()

    assert columns == ['day_number', 'block', 'class']


def test_validate_classes_pass(tmp_path):
    test_file = str(tmp_path.joinpath('test.xlsx'))
    data_1 = {
        'block': [1, 2, 3, 1, 2],
        'class': ['test class 1', 'test class 2', 'test class 3', 'test class 1', 'test class 2'],
        'student': ['test 1', 'test 1', 'test 1', 'test 2', 'test 2'],
    }

    df_1 = pd.DataFrame(data_1)
    df_1.to_excel(test_file, index=False, engine='xlsxwriter')

    data_2 = data_1 = {
        'block': [1, 3, 2, 1, 2],
        'class': [
            'test class 1',
            'test class 3',
            'test class 2',
            'test class 1',
            'test class 2',
        ],
        'student': ['test 1', 'test 1', 'test 1', 'test 2', 'test 2'],
    }

    df_2 = pd.DataFrame(data_2)

    schedule_builder = ScheduleBuilder(test_file)
    invalid_df = schedule_builder._validate_classes(df_2)

    assert not invalid_df


def test_validate_classes_fail(tmp_path):
    test_file = str(tmp_path.joinpath('test.xlsx'))
    data_1 = {
        'block': [1, 2, 3, 1, 2],
        'class': ['test class 1', 'test class 2', 'test class 3', 'test class 1', 'test class 2'],
        'student': ['test 1', 'test 1', 'test 1', 'test 2', 'test 2'],
    }

    df_1 = pd.DataFrame(data_1)
    df_1.to_excel(test_file, index=False, engine='xlsxwriter')

    data_2 = {
        'block': [1, 2, 1, 2],
        'class': ['test class 1', 'test class 2', 'test class 1', 'test class 2'],
        'student': ['test 1', 'test 1', 'test 2', 'test 2'],
    }

    df_2 = pd.DataFrame(data_2)

    expected_df = pd.DataFrame(
        {
            'student': ['test 1'],
            'original': 3,
            'scheduled': 2,
        }
    ).set_index('student')

    schedule_builder = ScheduleBuilder(test_file)
    invalid_df = schedule_builder._validate_classes(df_2)

    assert expected_df.equals(invalid_df)


def test_same_day_pass(tmp_path):
    test_file = str(tmp_path.joinpath('test.xlsx'))

    data = {
        'block': [1, 1, 2,],
        'class': ['test class 1', 'test class 1', 'test class 3',],
        'total_students': [2, 2, 1,],
        'max_students': [2, 2, 1,],
        'num_classes': [1, 1, 1,],
        'day_number': [1, 1, 1,],
        'student': ['test 1', 'test 2', 'test 1',],
    }
    df = pd.DataFrame(data)
    df.to_excel(test_file, index=False, engine='xlsxwriter')
    
    schedule_builder = ScheduleBuilder(test_file)
    validate = schedule_builder._validate_same_day(df)

    assert not validate


def test_same_day_fail(tmp_path):
    test_file = str(tmp_path.joinpath('test.xlsx'))

    data = {
        'block': [1, 1, 2,],
        'class': ['test class 1', 'test class 1', 'test class 3',],
        'total_students': [2, 2, 1,],
        'max_students': [2, 2, 1,],
        'num_classes': [1, 1, 1,],
        'day_number': [1, 1, 2,],
        'student': ['test 1', 'test 2', 'test 1',],
    }
    df = pd.DataFrame(data)
    df.to_excel(test_file, index=False, engine='xlsxwriter')
    
    schedule_builder = ScheduleBuilder(test_file)
    validate = schedule_builder._validate_same_day(df)

    expected_df = pd.DataFrame({'student': ['test 1'], 'count': ['2']})

    assert not expected_df.equals(validate)


def test_validate_students_pass(tmp_path):
    test_file = str(tmp_path.joinpath('test.xlsx'))
    data_1 = {
        'block': [1, 2, 3, 1, 2],
        'class': ['test class 1', 'test class 2', 'test class 3', 'test class 1', 'test class 2'],
        'student': ['test 1', 'test 1', 'test 1', 'test 2', 'test 2'],
    }

    df_1 = pd.DataFrame(data_1)
    df_1.to_excel(test_file, index=False, engine='xlsxwriter')

    data_2 = data_1 = {
        'block': [1, 3, 2, 1, 4],
        'class': [
            'test class 1',
            'test class 3',
            'test class 2',
            'test class 1',
            'test class 4',
        ],
        'student': ['test 1', 'test 1', 'test 1', 'test 2', 'test 1'],
    }

    df_2 = pd.DataFrame(data_2)

    schedule_builder = ScheduleBuilder(test_file)
    invalid = schedule_builder._validate_students(df_2)

    assert not invalid


def test_validate_students_fail(tmp_path):
    test_file = str(tmp_path.joinpath('test.xlsx'))
    data_1 = {
        'block': [1, 2, 3, 1, 2],
        'class': ['test class 1', 'test class 2', 'test class 3', 'test class 1', 'test class 2'],
        'student': ['test 1', 'test 1', 'test 1', 'test 2', 'test 2'],
    }

    df_1 = pd.DataFrame(data_1)
    df_1.to_excel(test_file, index=False, engine='xlsxwriter')

    data_2 = data_1 = {
        'block': [1, 3, 2],
        'class': [
            'test class 1',
            'test class 3',
            'test class 2',
        ],
        'student': ['test 1', 'test 1', 'test 1'],
    }

    df_2 = pd.DataFrame(data_2)

    schedule_builder = ScheduleBuilder(test_file)
    invalid = schedule_builder._validate_students(df_2)

    assert len(invalid) == 1
    assert 'test 2' in invalid