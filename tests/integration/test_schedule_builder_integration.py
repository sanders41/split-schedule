import pandas as pd
import pytest

from pathlib import Path
from split_schedule.schedule_builder import ScheduleBuilder


@pytest.mark.parametrize('reduce_by', [0.1, 0.2, 0.5])
@pytest.mark.parametrize('smallest_allowed', [1, 5, 10])
def test_build_schedule(tmp_path, reduce_by, smallest_allowed, test_schedule):
    EXPORT_PATH = tmp_path.joinpath('schedule.xlsx')
    schedule_builder = ScheduleBuilder(str(test_schedule))
    schedule_builder.build_schedule(reduce_by, str(EXPORT_PATH), smallest_allowed)

    expected_df = pd.read_excel(str(test_schedule))
    expected_student_classes = expected_df.groupby('student').size().to_dict()

    expected_columns = [
        'block',
        'class',
        'total_students',
        'max_students',
        'num_classes',
        'day_number',
        'student'
    ]

    df = pd.read_excel(str(EXPORT_PATH))
    student_classes = df.groupby('student').size().to_dict()
    columns = df.columns.values.tolist()

    assert student_classes == expected_student_classes
    assert columns == expected_columns