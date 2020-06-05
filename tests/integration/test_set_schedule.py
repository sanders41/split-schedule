import pandas as pd
import pytest
import sys

from pathlib import Path
from split_schedule.set_schedule import main

@pytest.mark.parametrize('file_path', ['-f', '--file_path'])
@pytest.mark.parametrize('output_file_path', ['-o', '--output_file_path'])
@pytest.mark.parametrize('reduce_by', ['-r', '--reduce_by'])
@pytest.mark.parametrize('smallest_allowed', ['-s', '--smallest_allowed', None])
@pytest.mark.parametrize('reduce_by_amount', ['0.1', '0.2', '0.5'])
@pytest.mark.parametrize('smallest_allowed_amount', ['1', '5', '10'])
def test_set_schedule(
    monkeypatch,
    tmp_path,
    file_path,
    output_file_path,
    reduce_by,
    smallest_allowed,
    reduce_by_amount,
    smallest_allowed_amount,
    test_schedule
):
    EXPORT_PATH = tmp_path.joinpath('schedule.xlsx')
    args=[
        'pytest',
        file_path,
        str(test_schedule),
        output_file_path,
        str(EXPORT_PATH),
        reduce_by,
        reduce_by_amount,
    ]

    if smallest_allowed:
        args.append(smallest_allowed)
        args.append(smallest_allowed_amount)

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

    with monkeypatch.context() as m:
        m.setattr(sys, 'argv', args)
        main()

    df = pd.read_excel(str(EXPORT_PATH))
    student_classes = df.groupby('student').size().to_dict()
    columns = df.columns.values.tolist()

    assert student_classes == expected_student_classes
    assert columns == expected_columns


def test_set_schedule_unfound_file(monkeypatch, tmp_path):
    EXPORT_PATH = tmp_path.joinpath('schedule.xlsx')
    args=[
        'pytest',
        '-f',
        'some/bad/file/path/bad.xlsx',
        '-o',
        str(EXPORT_PATH),
        '-r',
        '0.2',
    ]

    with monkeypatch.context() as m:
        m.setattr(sys, 'argv', args)
        with pytest.raises(ValueError) as execinfo:
            main()

            assert 'Unable to find file' in str(execinfo.value)