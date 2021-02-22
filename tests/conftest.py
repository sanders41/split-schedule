from itertools import combinations

import pandas as pd
import pytest

mock_data = {
    "block": [
        1,
        1,
        2,
        3,
        2,
        2,
        2,
        2,
        1,
        1,
        1,
        1,
        1,
        2,
        3,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
    ],
    "class": [
        "test class 1",
        "test class 1",
        "test class 2",
        "test class 2",
        "test class 3",
        "test class 3",
        "test class 3",
        "test class 3",
        "test class 4",
        "test class 4",
        "test class 5",
        "test class 5",
        "test class 5",
        "test class 6",
        "test class 7",
        "test class 8",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 7",
        "test class 9",
        "test class 9",
    ],
    "student": [
        "Al Pacino",
        "Anne Hathaway",
        "Arnold Schwarzenegger",
        "Diane Keaton",
        "Al Pacino",
        "Anne Hathaway",
        "Annette Bening",
        "Claudia Cardinale",
        "Antonio Banderas",
        "Diane Keaton",
        "Test 1",
        "Arnold Schwarzenegger",
        "Claudette Colbert",
        "Diane Keaton",
        "Claudia Cardinale",
        "Antonio Banderas",
        "Test 1",
        "Test 2",
        "Test 3",
        "Test 4",
        "Test 5",
        "Test 6",
        "Test 7",
        "Test 8",
        "Test 9",
        "Test 10",
        "Test 11",
        "Test 12",
        "Test 13",
        "Test 14",
        "Test 15",
        "Test 16",
        "Test 17",
        "Test 18",
        "Test 19",
        "Test 20",
        "Test 21",
        "Test 22",
        "Test 23",
        "Test 24",
        "Test 25",
        "Test 26",
        "Al Pacino",
        "Anne Hathaway",
    ],
}


@pytest.fixture(scope="session")
def class_size_check(test_schedule):
    df = pd.read_excel(str(test_schedule), engine="openpyxl")
    class_size = (
        df.groupby(
            [
                "block",
                "class",
            ]
        )
        .size()
        .to_frame()
        .reset_index()
    )
    class_size = [
        {"block": x[0], "class_name": x[1], "total_students": x[2]} for x in class_size.to_numpy()
    ]

    return class_size


@pytest.fixture(scope="session")
def student_matches_check(test_schedule):
    df = pd.read_excel(str(test_schedule), engine="openpyxl")
    blocks = df["block"].sort_values().unique()
    total_blocks = df["block"].max()
    match_df = df.pivot(index="student", columns="block", values="class").reset_index()

    matches = [{i: []} for i in range(total_blocks, 1, -1)]
    all_combinations = []
    for r in range(len(blocks) + 1):
        found_combinations = combinations(blocks, r)
        combinations_list = list(found_combinations)
        for comb in combinations_list:
            if len(comb) > 1:
                all_combinations += combinations_list

    all_combinations.sort(reverse=True, key=len)

    for comb in all_combinations:
        exclude = []
        for match in matches:
            for m in match:
                for student_matches in match[m]:
                    for student_match in student_matches:
                        exclude.append(student_match)

        match_df = match_df[~match_df["student"].isin(exclude)]
        matches_key = len(comb)
        matches_loc = total_blocks - len(comb)
        match_some_df = match_df.groupby(list(comb))
        for match in match_some_df:
            match_list = match[1][["student"]].values.tolist()  # type: ignore
            check = [x.pop() for x in match_list if len(match_list) > 1]
            if check:
                matches[matches_loc][matches_key].append(check)

    return matches


@pytest.fixture(scope="session")
def student_classes_check(test_schedule):
    df = pd.read_excel(str(test_schedule), engine="openpyxl")
    student_classes = {}
    for student in (
        df[["student", "block", "class"]]
        .sort_values(
            by=[
                "block",
                "class",
            ]
        )
        .to_numpy()
    ):
        if student[0] in student_classes:
            student_classes[student[0]]["blocks"][student[1]] = student[2]
        else:
            student_classes[student[0]] = {"blocks": {student[1]: student[2]}}

    return student_classes


@pytest.fixture
def test_schedule_df():
    return pd.DataFrame(mock_data)


@pytest.fixture(scope="session")
def test_schedule(tmp_path_factory):
    save_dir = tmp_path_factory.mktemp("schedule").joinpath("original_schedule.xlsx")
    df = pd.DataFrame(mock_data)
    df.to_excel(save_dir, index=False, engine="xlsxwriter")
    return save_dir


@pytest.fixture(scope="session")
def test_schedule_csv(tmp_path_factory):
    save_dir = tmp_path_factory.mktemp("schedule").joinpath("original_schedule.csv")
    df = pd.DataFrame(mock_data)
    df.to_csv(save_dir, index=False)
    return save_dir
