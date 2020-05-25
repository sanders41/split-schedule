import pandas as pd
import pytest

from itertools import combinations, groupby
from math import ceil, floor
from operator import itemgetter
from pathlib import Path


ASSETS_PATH= Path().absolute().joinpath('tests/assets/')
TEST_FILE_PATH = ASSETS_PATH.joinpath('classes.xlsx')


@pytest.fixture(scope='session')
def class_size_check():
    df = pd.read_excel(str(TEST_FILE_PATH))
    class_size = df.groupby(['block', 'class',]).size().to_frame().reset_index()
    class_size = [
        {'block': x[0], 'class_name': x[1], 'total_students': x[2]} for x in class_size.to_numpy()
    ]

    return class_size


@pytest.fixture(scope='session')
def group_blocks_check():
    df = pd.read_excel(str(TEST_FILE_PATH))
    student_classes = [
        {'block': x[1], 'class_name': x[2], 'student': x[0],}
            for x in df[['student', 'block', 'class']]
            .sort_values(by=['block', 'class',])
        .to_numpy()
    ]

    student_classes_sorted = sorted(student_classes, key=itemgetter('block', 'class_name',))
    grouped_classes = [
        {'block': x[0][0], 'class_name': x[0][1], 'students': list(x[1])} for x in
        groupby(student_classes_sorted, key=itemgetter('block', 'class_name',))
    ]

    grouped_blocks: List[GroupedBlock] = [
            {'block': x[0], 'classes': list(x[1])} # type: ignore
            for x in groupby(grouped_classes, key=itemgetter('block'))
    ]

    return grouped_blocks


@pytest.fixture(scope='session')
def student_matches_check():
    df = pd.read_excel(str(TEST_FILE_PATH))
    blocks = df['block'].sort_values().unique()
    total_blocks = df['block'].max()
    match_df = df.pivot(
        index='student',
        columns='block',
        values='class'
    ).reset_index()

    matches = []
    for i in range(total_blocks, 1, -1):
        matches.append({i: []})

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

        match_df = match_df[~match_df['student'].isin(exclude)]
        matches_key = len(comb)
        matches_loc = total_blocks - len(comb)
        match_some_df = match_df.groupby(list(comb))
        for match in match_some_df:
            match_list = match[1][['student']].values.tolist() # type: ignore
            check = [x.pop() for x in match_list if len(match_list) > 1]
            if len(check) > 0:
                matches[matches_loc][matches_key].append(check)

    return matches 


@pytest.fixture(scope='session')
def student_classes_check():
    df = pd.read_excel(str(TEST_FILE_PATH))
    student_classes = [
        {'block': x[1], 'class_name': x[2], 'student': x[0],}
            for x in df[['student', 'block', 'class']]
            .sort_values(by=['block', 'class',])
        .to_numpy()
    ]

    return student_classes