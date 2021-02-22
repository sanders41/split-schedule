import pandas as pd
import pytest

from split_schedule.schedule_builder import ScheduleBuilder


@pytest.mark.parametrize("reduce_by", [0.1, 0.2, 0.5])
@pytest.mark.parametrize("smallest_allowed", [1, 5, 10])
def test_build_schedule_from_df(reduce_by, smallest_allowed, test_schedule_df):
    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_df(
        test_schedule_df, reduce_by, smallest_allowed, verbose=True
    )

    expected_student_classes = test_schedule_df.groupby("student").size().to_dict()

    expected_columns = [
        "block",
        "class",
        "total_students",
        "max_students",
        "num_classes",
        "day_number",
        "student",
    ]

    student_classes = schedule_builder.final_schedule_df.groupby("student").size().to_dict()
    columns = schedule_builder.final_schedule_df.columns.values.tolist()

    assert student_classes == expected_student_classes
    assert columns == expected_columns


@pytest.mark.parametrize("reduce_by", [0.1, 0.2, 0.5])
@pytest.mark.parametrize("smallest_allowed", [1, 5, 10])
def test_build_schedule_from_file_csv(tmp_path, reduce_by, smallest_allowed, test_schedule_csv):
    export_path = tmp_path.joinpath("schedule.csv")
    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(
        test_schedule_csv, reduce_by, smallest_allowed, verbose=True
    )
    schedule_builder.save_schedule(export_path)

    expected_df = pd.read_csv(test_schedule_csv)
    expected_student_classes = expected_df.groupby("student").size().to_dict()

    expected_columns = [
        "block",
        "class",
        "total_students",
        "max_students",
        "num_classes",
        "day_number",
        "student",
    ]

    df = pd.read_csv(export_path)
    student_classes = df.groupby("student").size().to_dict()
    columns = df.columns.values.tolist()

    assert student_classes == expected_student_classes
    assert columns == expected_columns


@pytest.mark.parametrize("reduce_by", [0.1, 0.2, 0.5])
@pytest.mark.parametrize("smallest_allowed", [1, 5, 10])
def test_build_schedule_from_file_excel(tmp_path, reduce_by, smallest_allowed, test_schedule):
    export_path = tmp_path.joinpath("schedule.xlsx")
    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(
        test_schedule, reduce_by, smallest_allowed, verbose=True
    )
    schedule_builder.save_schedule(export_path)

    expected_df = pd.read_excel(test_schedule, engine="openpyxl")
    expected_student_classes = expected_df.groupby("student").size().to_dict()

    expected_columns = [
        "block",
        "class",
        "total_students",
        "max_students",
        "num_classes",
        "day_number",
        "student",
    ]

    df = pd.read_excel(export_path, engine="openpyxl")
    student_classes = df.groupby("student").size().to_dict()
    columns = df.columns.values.tolist()

    assert student_classes == expected_student_classes
    assert columns == expected_columns
