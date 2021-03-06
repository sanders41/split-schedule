import logging

import pandas as pd
import pytest

from split_schedule.errors import NoScheduleError
from split_schedule.schedule_builder import ScheduleBuilder, SchedulingError
from tests.helpers import init_classes_check, reduce_classes_check, total_classes_check


@pytest.mark.parametrize("max_tries", [1, 2])
@pytest.mark.parametrize("verbose", [True, False])
def test_build_schedule_validated_classs_size(monkeypatch, tmp_path, caplog, max_tries, verbose):
    test_file = str(tmp_path.joinpath("data1.xlsx"))
    data_1 = {
        "block": [1],
        "class": ["test class 1"],
        "student": ["test 1"],
    }

    df_1 = pd.DataFrame(data_1)
    df_1.to_excel(test_file, index=False, engine="openpyxl")

    def mock_return(*args, **kwargs):
        return pd.DataFrame(
            {
                "student": ["test 1"],
                "original": 3,
                "scheduled": 2,
            }
        ).set_index("student")

    schedule_builder = ScheduleBuilder()
    monkeypatch.setattr(ScheduleBuilder, "_validate_class_size", mock_return)

    with pytest.raises(SchedulingError):
        schedule_builder.build_schedule_from_file(
            test_file, 0.2, max_tries=max_tries, verbose=verbose
        )

    if verbose:
        assert "Classes contain too many students" in caplog.text
    else:
        assert "Classes contain too many students" not in caplog.text


@pytest.mark.parametrize("max_tries", [1, 2])
@pytest.mark.parametrize("verbose", [True, False])
def test_build_schedule_validated_classes_number(monkeypatch, tmp_path, caplog, max_tries, verbose):
    test_file = str(tmp_path.joinpath("data1.xlsx"))
    data_1 = {
        "block": [1],
        "class": ["test class 1"],
        "student": ["test 1"],
    }

    df_1 = pd.DataFrame(data_1)
    df_1.to_excel(test_file, index=False, engine="openpyxl")

    data_2 = {
        "block": [1, 2, 1, 2],
        "class": ["test class 1", "test class 2", "test class 1", "test class 2"],
        "student": ["test 1", "test 1", "test 2", "test 2"],
    }

    def mock_return_validated_classes(*args, **kwargs):
        return pd.DataFrame(data_2)

    schedule_builder = ScheduleBuilder()
    monkeypatch.setattr(ScheduleBuilder, "_validate_classes", mock_return_validated_classes)

    with pytest.raises(SchedulingError):
        schedule_builder.build_schedule_from_file(
            test_file, 0.2, max_tries=max_tries, verbose=verbose
        )

    if verbose:
        assert "Student missing" in caplog.text
    else:
        assert "Student missing" not in caplog.text


@pytest.mark.parametrize("max_tries", [1, 2])
@pytest.mark.parametrize("verbose", [True, False])
def test_build_schedule_validated_same_day(monkeypatch, tmp_path, caplog, max_tries, verbose):
    test_file = str(tmp_path.joinpath("data1.xlsx"))
    data_1 = {
        "block": [1],
        "class": ["test class 1"],
        "student": ["test 1"],
    }

    df_1 = pd.DataFrame(data_1)
    df_1.to_excel(test_file, index=False, engine="openpyxl")

    data_2 = {
        "block": [
            1,
            1,
            2,
        ],
        "class": [
            "test class 1",
            "test class 1",
            "test class 3",
        ],
        "total_students": [
            2,
            2,
            1,
        ],
        "max_students": [
            2,
            2,
            1,
        ],
        "num_classes": [
            1,
            1,
            1,
        ],
        "day_number": [
            1,
            1,
            2,
        ],
        "student": [
            "test 1",
            "test 2",
            "test 1",
        ],
    }

    def mock_return_validated_days(*args, **kwargs):
        return pd.DataFrame(data_2)

    schedule_builder = ScheduleBuilder()
    monkeypatch.setattr(ScheduleBuilder, "_validate_same_day", mock_return_validated_days)

    with pytest.raises(SchedulingError):
        schedule_builder.build_schedule_from_file(
            test_file, 0.2, max_tries=max_tries, verbose=verbose
        )

    if verbose:
        assert "Student not on the same day" in caplog.text
    else:
        assert "Student not on the same day" not in caplog.text


@pytest.mark.parametrize("max_tries", [1, 2])
@pytest.mark.parametrize("verbose", [True, False])
def test_build_schedule_validated_students(monkeypatch, tmp_path, caplog, max_tries, verbose):
    test_file = str(tmp_path.joinpath("data1.xlsx"))
    data_1 = {
        "block": [1],
        "class": ["test class 1"],
        "student": ["test 1"],
    }

    df_1 = pd.DataFrame(data_1)
    df_1.to_excel(test_file, index=False, engine="openpyxl")

    def mock_return_validated_students(*args, **kwargs):
        return ["test 1"]

    schedule_builder = ScheduleBuilder()
    monkeypatch.setattr(ScheduleBuilder, "_validate_students", mock_return_validated_students)

    with pytest.raises(SchedulingError):
        schedule_builder.build_schedule_from_file(
            test_file, 0.2, max_tries=max_tries, verbose=verbose
        )

    if verbose:
        assert "Student original number" in caplog.text
    else:
        assert "Student original number" not in caplog.text


@pytest.mark.parametrize("verbose", [True, False])
def test_build_schedule_restart(monkeypatch, tmp_path, caplog, verbose):
    test_file = str(tmp_path.joinpath("data1.xlsx"))
    data_1 = {
        "block": [1],
        "class": ["test class 1"],
        "student": ["test 1"],
    }

    df_1 = pd.DataFrame(data_1)
    df_1.to_excel(test_file, index=False, engine="openpyxl")

    def mock_return(*args, **kwargs):
        return None

    schedule_builder = ScheduleBuilder()
    monkeypatch.setattr(ScheduleBuilder, "_fill_classes", mock_return)

    with pytest.raises(SchedulingError):
        schedule_builder.build_schedule_from_file(test_file, 0.2, max_tries=2, verbose=verbose)

    if verbose:
        assert "No schedule found. Retrying" in caplog.text
    else:
        assert "No schedule found. Retrying" not in caplog.text


def test_fill_classes_match_no_space(tmp_path):
    test_file = str(tmp_path.joinpath("data1.xlsx"))
    data = {
        "block": [1, 1, 2, 2],
        "class": [
            "test class 1",
            "test class 1",
            "test class 2",
            "test class 2",
        ],
        "student": ["test 1", "test 2", "test 1", "test 2"],
    }

    df = pd.DataFrame(data)
    df.to_excel(test_file, index=False, engine="openpyxl")

    fill_classes = [
        {
            "block": 1,
            "class_name": "test class 1",
            "total_students": 2,
            "max_students": 1,
            "num_classes": 1,
            "classes": [set()],
        },
        {
            "block": 2,
            "class_name": "test class 2",
            "total_students": 2,
            "max_students": 1,
            "num_classes": 1,
            "classes": [set()],
        },
    ]

    student_classes_grouped = {
        "test 1": {"blocks": {1: "test class 1", 2: "test class 2"}},
        "test 2": {"blocks": {1: "test class 1", 2: "test class 2"}},
    }

    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_file)

    fill_classes = schedule_builder._fill_classes(fill_classes, student_classes_grouped)

    assert not fill_classes


def test_fill_classes_no_match_no_space(tmp_path):
    test_file = str(tmp_path.joinpath("data1.xlsx"))

    data = {
        "block": [1],
        "class": [
            "test class 1",
        ],
        "student": ["test 1"],
    }

    df = pd.DataFrame(data)
    df.to_excel(test_file, index=False, engine="openpyxl")

    fill_classes = [
        {
            "block": 1,
            "class_name": "test class 1",
            "total_students": 1,
            "max_students": 0,
            "num_classes": 1,
            "classes": [set()],
        },
    ]

    student_classes_grouped = {
        "test 1": {"blocks": {1: "test class 1", 2: "test class 2"}},
    }

    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_file)
    fill_classes = schedule_builder._fill_classes(fill_classes, student_classes_grouped)

    assert not fill_classes


def test_fill_classes_match_move_day(tmp_path):
    test_file = str(tmp_path.joinpath("data1.xlsx"))
    data = {
        "block": [1, 2, 1, 2, 1, 2],
        "class": [
            "test class 1",
            "test class 2",
            "test class 1",
            "test class 2",
            "test class 1",
            "test class 2",
        ],
        "student": ["test 1", "test 1", "test 2", "test 2", "test 3", "test 3"],
    }

    df = pd.DataFrame(data)
    df.to_excel(test_file, index=False, engine="openpyxl")

    fill_classes = [
        {
            "block": 1,
            "class_name": "test class 1",
            "total_students": 3,
            "max_students": 2,
            "num_classes": 2,
            "classes": [set(), set()],
        },
        {
            "block": 2,
            "class_name": "test class 2",
            "total_students": 3,
            "max_students": 2,
            "num_classes": 2,
            "classes": [set(), set()],
        },
    ]

    student_classes_grouped = {
        "test 1": {"blocks": {1: "test class 1", 2: "test class 2"}},
        "test 2": {"blocks": {1: "test class 1", 2: "test class 2"}},
        "test 3": {"blocks": {1: "test class 1", 2: "test class 2"}},
    }

    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_file)

    fill_classes = schedule_builder._fill_classes(fill_classes, student_classes_grouped)
    class_size = [sorted([len(y) for y in x["classes"]]) for x in fill_classes]

    expected = [[1, 2], [1, 2]]
    assert expected == class_size


def test_find_matches(student_matches_check, test_schedule):
    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_schedule)
    matches = schedule_builder._find_matches()

    assert matches == student_matches_check


def test_find_matches_unused_order_found(tmp_path, caplog):
    test_file = str(tmp_path.joinpath("data1.xlsx"))
    data = {
        "block": [1, 1, 2, 2],
        "class": [
            "test class 1",
            "test class 1",
            "test class 2",
            "test class 2",
        ],
        "student": ["test 1", "test 2", "test 1", "test 2"],
    }

    df = pd.DataFrame(data)
    df.to_excel(test_file, index=False, engine="openpyxl")

    class TestingScheduleBuilder(ScheduleBuilder):
        def __init__(self, schedule_file_path):
            self.final_schedule_df = None

            self._schedule_df = self._load_data(schedule_file_path)
            self._attempted_df = [df]
            self._attempt = 1
            self._verbose = True

            logging.basicConfig(format="%(asctime)s: %(levelname)s: %(message)s")
            logging.root.setLevel(level=logging.INFO)
            self._logger = logging.getLogger()

    schedule_builder = TestingScheduleBuilder(test_file)
    schedule_builder._find_matches()

    assert "Unused student order found" in caplog.text


def test_find_matches_unused_order_not_found(tmp_path, caplog):
    test_file = str(tmp_path.joinpath("data1.xlsx"))
    data_1 = {
        "block": [1, 1, 2, 2],
        "class": [
            "test class 1",
            "test class 1",
            "test class 2",
            "test class 2",
        ],
        "student": ["test 1", "test 2", "test 1", "test 2"],
    }

    df_1 = pd.DataFrame(data_1)
    df_1.to_excel(test_file, index=False, engine="openpyxl")

    data_2 = {
        "block": [1, 1, 2, 2],
        "class": [
            "test class 1",
            "test class 1",
            "test class 2",
            "test class 2",
        ],
        "student": ["test 2", "test 1", "test 2", "test 1"],
    }

    df_2 = pd.DataFrame(data_2)

    class TestingScheduleBuilder(ScheduleBuilder):
        def __init__(self, schedule_file_path):
            self.final_schedule_df = None

            self._schedule_df = self._load_data(schedule_file_path)
            self._attempted_df = [df_1, df_2]
            self._attempt = 1
            self._verbose = True

            logging.basicConfig(format="%(asctime)s: %(levelname)s: %(message)s")
            logging.root.setLevel(level=logging.INFO)
            self._logger = logging.getLogger()

    schedule_builder = TestingScheduleBuilder(test_file)
    schedule_builder._find_matches()

    assert "No unused matches found" in caplog.text


def test_find_matches_retry(student_matches_check, test_schedule):
    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_schedule)
    schedule_builder._find_matches()
    matches = schedule_builder._find_matches()

    m_keys = [x.keys() for x in matches]
    s_keys = [x.keys() for x in student_matches_check]
    m_vals = [[[sorted(z) for z in y] for y in (list(x.values()))] for x in matches]
    s_vals = [[[sorted(z) for z in y] for y in (list(x.values()))] for x in student_matches_check]
    assert m_keys == s_keys
    assert m_vals == s_vals


def test_get_class_size(class_size_check, test_schedule):
    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_schedule)
    class_size = schedule_builder._get_class_size()
    assert class_size == class_size_check


def test_get_student_classes(student_classes_check, test_schedule):
    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_schedule)
    student_classes = schedule_builder._get_student_classes()

    assert student_classes == student_classes_check


@pytest.mark.parametrize("reduce_by", [0.1, 0.2, 0.5])
@pytest.mark.parametrize("smallest_allowed", [1, 5, 10])
def test_get_total_classes(class_size_check, reduce_by, smallest_allowed, test_schedule):
    reduced_classes = reduce_classes_check(reduce_by, smallest_allowed, class_size_check)
    check_total_classes = total_classes_check(reduced_classes)

    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_schedule)
    total_classes = schedule_builder._get_total_classes(reduced_classes)

    assert total_classes == check_total_classes


@pytest.mark.parametrize("reduce_by", [0.1, 0.2, 0.5])
@pytest.mark.parametrize("smallest_allowed", [1, 5, 10])
def test_init_classes(class_size_check, reduce_by, smallest_allowed, test_schedule):
    expected = init_classes_check(class_size_check, reduce_by, smallest_allowed)
    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_schedule)
    classes = schedule_builder._init_classes(reduce_by, smallest_allowed)

    assert classes == expected


def test_init_schedule_builder(test_schedule):
    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_schedule)
    test = pd.read_excel(str(test_schedule), engine="openpyxl")

    assert test.equals(schedule_builder._schedule_df)


@pytest.mark.parametrize("reduce_by", [0.1, 0.2, 0.5])
@pytest.mark.parametrize("smallest_allowed", [1, 5, 10])
def test_reduce_class(class_size_check, reduce_by, smallest_allowed, test_schedule):
    check_reduced = reduce_classes_check(reduce_by, smallest_allowed, class_size_check)

    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_schedule)
    reduced_class = schedule_builder._reduce_class(class_size_check, reduce_by, smallest_allowed)

    assert reduced_class == check_reduced


def test_save_schedule_to_file(tmp_path, test_schedule):
    export_path = tmp_path.joinpath("schedule.xlsx")

    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_schedule)
    schedule_builder.save_schedule(export_path)

    assert export_path.exists()


def test_save_schedule_check_columns(tmp_path, test_schedule):
    export_path = tmp_path.joinpath("schedule.xlsx")

    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_schedule)
    schedule_builder.save_schedule(export_path)
    df_saved = pd.read_excel(export_path, engine="openpyxl")
    columns = df_saved.columns.values.tolist()

    assert columns == [
        "block",
        "class",
        "total_students",
        "max_students",
        "num_classes",
        "day_number",
        "student",
    ]


def test_validate_class_size_pass(tmp_path):
    test_file = str(tmp_path.joinpath("test.xlsx"))

    data = {
        "block": [
            1,
            1,
        ],
        "class": [
            "test class 1",
            "test class 1",
        ],
        "total_students": [
            2,
            2,
        ],
        "max_students": [
            2,
            2,
        ],
        "num_classes": [
            1,
            1,
        ],
        "day_number": [
            1,
            1,
        ],
        "student": [
            "test 1",
            "test 2",
        ],
    }
    df = pd.DataFrame(data)
    df.to_excel(test_file, index=False, engine="openpyxl")

    schedule_builder = ScheduleBuilder()
    validate_df = schedule_builder._validate_class_size(df)

    assert not validate_df


def test_validate_class_size_fail(tmp_path):
    test_file = str(tmp_path.joinpath("test.xlsx"))

    data = {
        "block": [
            1,
            1,
        ],
        "class": [
            "test class 1",
            "test class 1",
        ],
        "total_students": [
            2,
            2,
        ],
        "max_students": [
            1,
            1,
        ],
        "num_classes": [
            1,
            1,
        ],
        "day_number": [
            1,
            1,
        ],
        "student": [
            "test 1",
            "test 2",
        ],
    }
    df = pd.DataFrame(data)
    df.to_excel(test_file, index=False, engine="openpyxl")

    schedule_builder = ScheduleBuilder()
    validate_df = schedule_builder._validate_class_size(df)

    expected_df = pd.DataFrame(
        {
            "block": [1],
            "class": ["test class 1"],
            "max_students": [1],
            "day_number": [1],
            "class_size": [2],
        }
    )

    assert expected_df.equals(validate_df)


def test_validate_classes_pass(tmp_path):
    test_file = str(tmp_path.joinpath("test.xlsx"))
    data_1 = {
        "block": [1, 2, 3, 1, 2],
        "class": ["test class 1", "test class 2", "test class 3", "test class 1", "test class 2"],
        "student": ["test 1", "test 1", "test 1", "test 2", "test 2"],
    }

    df_1 = pd.DataFrame(data_1)
    df_1.to_excel(test_file, index=False, engine="openpyxl")

    data_2 = data_1 = {
        "block": [1, 3, 2, 1, 2],
        "class": [
            "test class 1",
            "test class 3",
            "test class 2",
            "test class 1",
            "test class 2",
        ],
        "student": ["test 1", "test 1", "test 1", "test 2", "test 2"],
    }

    df_2 = pd.DataFrame(data_2)

    schedule_builder = ScheduleBuilder()
    invalid_df = schedule_builder._validate_classes(df_2)

    assert not invalid_df


def test_validate_classes_fail(tmp_path):
    test_file = str(tmp_path.joinpath("test.xlsx"))
    data_1 = {
        "block": [1, 2, 3, 1, 2],
        "class": ["test class 1", "test class 2", "test class 3", "test class 1", "test class 2"],
        "student": ["test 1", "test 1", "test 1", "test 2", "test 2"],
    }

    df_1 = pd.DataFrame(data_1)
    df_1.to_excel(test_file, index=False, engine="openpyxl")

    data_2 = {
        "block": [1, 2, 1, 2],
        "class": ["test class 1", "test class 2", "test class 1", "test class 2"],
        "student": ["test 1", "test 1", "test 2", "test 2"],
    }

    df_2 = pd.DataFrame(data_2)

    expected_df = pd.DataFrame(
        {
            "student": ["test 1"],
            "original": 3,
            "scheduled": 2,
        }
    ).set_index("student")

    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_file)
    invalid_df = schedule_builder._validate_classes(df_2)

    assert expected_df.equals(invalid_df)


def test_same_day_pass(tmp_path):
    test_file = str(tmp_path.joinpath("test.xlsx"))

    data = {
        "block": [
            1,
            1,
            2,
        ],
        "class": [
            "test class 1",
            "test class 1",
            "test class 3",
        ],
        "total_students": [
            2,
            2,
            1,
        ],
        "max_students": [
            2,
            2,
            1,
        ],
        "num_classes": [
            1,
            1,
            1,
        ],
        "day_number": [
            1,
            1,
            1,
        ],
        "student": [
            "test 1",
            "test 2",
            "test 1",
        ],
    }
    df = pd.DataFrame(data)
    df.to_excel(test_file, index=False, engine="openpyxl")

    schedule_builder = ScheduleBuilder()
    validate = schedule_builder._validate_same_day(df)

    assert not validate


def test_same_day_fail(tmp_path):
    test_file = str(tmp_path.joinpath("test.xlsx"))

    data = {
        "block": [
            1,
            1,
            2,
        ],
        "class": [
            "test class 1",
            "test class 1",
            "test class 3",
        ],
        "total_students": [
            2,
            2,
            1,
        ],
        "max_students": [
            2,
            2,
            1,
        ],
        "num_classes": [
            1,
            1,
            1,
        ],
        "day_number": [
            1,
            1,
            2,
        ],
        "student": [
            "test 1",
            "test 2",
            "test 1",
        ],
    }
    df = pd.DataFrame(data)
    df.to_excel(test_file, index=False, engine="openpyxl")

    schedule_builder = ScheduleBuilder()
    validate = schedule_builder._validate_same_day(df)

    expected_df = pd.DataFrame({"student": ["test 1"], "count": ["2"]})

    assert not expected_df.equals(validate)


def test_validate_students_pass(tmp_path):
    test_file = str(tmp_path.joinpath("test.xlsx"))
    data_1 = {
        "block": [1, 2, 3, 1, 2],
        "class": ["test class 1", "test class 2", "test class 3", "test class 1", "test class 2"],
        "student": ["test 1", "test 1", "test 1", "test 2", "test 2"],
    }

    df_1 = pd.DataFrame(data_1)
    df_1.to_excel(test_file, index=False, engine="openpyxl")

    data_2 = data_1 = {
        "block": [1, 3, 2, 1, 4],
        "class": [
            "test class 1",
            "test class 3",
            "test class 2",
            "test class 1",
            "test class 4",
        ],
        "student": ["test 1", "test 1", "test 1", "test 2", "test 1"],
    }

    df_2 = pd.DataFrame(data_2)

    schedule_builder = ScheduleBuilder()
    invalid = schedule_builder._validate_students(df_2)

    assert not invalid


def test_validate_students_fail(tmp_path):
    test_file = str(tmp_path.joinpath("test.xlsx"))
    data_1 = {
        "block": [1, 2, 3, 1, 2],
        "class": ["test class 1", "test class 2", "test class 3", "test class 1", "test class 2"],
        "student": ["test 1", "test 1", "test 1", "test 2", "test 2"],
    }

    df_1 = pd.DataFrame(data_1)
    df_1.to_excel(test_file, index=False, engine="openpyxl")

    data_2 = {
        "block": [1, 3, 2],
        "class": [
            "test class 1",
            "test class 3",
            "test class 2",
        ],
        "student": ["test 1", "test 1", "test 1"],
    }

    df_2 = pd.DataFrame(data_2)

    schedule_builder = ScheduleBuilder()
    schedule_builder.build_schedule_from_file(test_file)
    invalid = schedule_builder._validate_students(df_2)

    assert len(invalid) == 1
    assert "test 2" in invalid


def test_build_schedule_from_file_bad_extension():
    with pytest.raises(ValueError):
        schedule_bulder = ScheduleBuilder()
        schedule_bulder.build_schedule_from_file("bad.zyz")


def test_save_schedule_no_schedule_error(tmp_path):
    with pytest.raises(NoScheduleError):
        schedule_builder = ScheduleBuilder()
        schedule_builder.save_schedule(tmp_path / "test.xlsx")


def test_save_schedule_file_error(tmp_path, test_schedule):
    with pytest.raises(ValueError):
        schedule_bulder = ScheduleBuilder()
        schedule_bulder.build_schedule_from_file(test_schedule)
        schedule_bulder.save_schedule(tmp_path / "bad.xyz")
