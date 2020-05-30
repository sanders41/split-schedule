import numpy as np
import pandas as pd

from itertools import combinations, groupby
from math import ceil, floor
from operator import itemgetter
from random import shuffle
from split_schedule.schedule_types import (
    GroupedBlock,
    ReducedClass,
    ScheduleDays,
    ScheduleTotalStudents,
    StudentClass
)
from typing import Dict, List, Optional, Set, Tuple


class ScheduleBuilder:
    def __init__(self, schedule_file_path: str) -> None:
        self.schedule_df = self._load_file(schedule_file_path)

    def build_schedule(self, reduce_by: float, save_path: str, smallest_allowed: int=1) -> None:
        student_classes_grouped = self._group_blocks()
        classes = self._init_classes(reduce_by, smallest_allowed)
        class_size = self._get_class_size()
        reduced_classes = self._reduce_class(
            class_size=class_size,
            reduce_by=reduce_by,
            smallest_allowed=smallest_allowed
        )
        total_classes = self._get_total_classes(reduced_classes)
        student_day = False
        while not student_day:
            fill_classes = classes
            group_blocks = self._fill_grouped_blocks(
                classes,
                total_classes,
                student_classes_grouped,
            )

            student_day, fill_classes_return = self._fill_classes(
                group_blocks,
                classes,
                student_classes_grouped,
                total_classes
            )

            if fill_classes_return:
                fill_classes = fill_classes_return

                fill_class_df = self._expand_fill_classes(fill_classes)

                self._save_schedule_to_file(fill_class_df, save_path)

    def _create_fill_classes_days(self, total_classes: int) -> List[List]:
        days: List[List] = []
        for day in range(total_classes):
            days.append([])
        return days

    def _expand_fill_classes(self, fill_classes: List[ScheduleDays]) -> pd.DataFrame:
        fill_classes_expanded = []
        for fill in fill_classes:
            for i, c in enumerate(fill['classes']):
                for student in c:
                    row = {
                        'block': fill['block'],
                        'class_name': fill['class_name'],
                        'total_students': fill['total_students'],
                        'max_students': fill['max_students'],
                        'num_classes': fill['num_classes'],
                        'day_number': i + 1,
                        'student': student,
                    }
                    fill_classes_expanded.append(row)
        
        fill_class_df = pd.DataFrame(fill_classes_expanded)
        fill_class_df = fill_class_df.rename(columns={'class_name': 'class'})

        return fill_class_df

    def _fill_classes(
        self,
        group_blocks: List[List[List[StudentClass]]],
        fill_classes: List[ScheduleDays],
        student_classes_grouped: List[GroupedBlock],
        total_classes: int
    ) -> Tuple[bool, Optional[List[ScheduleDays]]]:
        added = set()
        student_day = False
        student_day_tracker: Dict[str, int] = {}
        for x, block in enumerate(group_blocks):
            if x == len(group_blocks) - 1:
                student_day = True
                break
            for i, b in enumerate(block):
                fill_day = 0
                for sb in b:
                    for student_block in student_classes_grouped:
                        for student_class in student_block['classes']:
                            for student in student_class['students']:
                                if student['student'] == sb['student']:
                                    if (
                                        (
                                            student['student'],
                                            student['block'],
                                            student['class_name'],
                                        ) not in added
                                    ):
                                        for choice in fill_classes:
                                            if student_block['block'] == choice['block']:
                                                if (
                                                    student['block'] == choice['block']
                                                    and student['class_name'] == choice['class_name']
                                                ):
                                                    if student['student'] in student_day_tracker:
                                                        if len(choice['classes'][student_day_tracker[student['student']]]) < choice['max_students']:
                                                            choice['classes'][student_day_tracker[student['student']]].add(student['student'])
                                                            added.add(
                                                                (
                                                                    student['student'],
                                                                    student['block'],
                                                                    student['class_name'],
                                                                )
                                                            )
                                                            student_day = True
                                                            break
                                                        else:
                                                            if i + 1 > len(choice['classes']):
                                                                student_day = False
                                                                break
                                                    else:
                                                        for j in range(total_classes):
                                                            if len(choice['classes'][j]) < choice['max_students']:
                                                                choice['classes'][j].add(student['student'])
                                                                student_day_tracker[student['student']] = j
                                                                added.add(
                                                                (
                                                                    student['student'],
                                                                    student['block'],
                                                                    student['class_name'],
                                                                )
                                                            )
                                                                student_day = True
                                                                break
                                                            else:
                                                                if i + 1 > len(choice['classes']):
                                                                    student_day = False
                                                                    break
        if student_day:
            return student_day, fill_classes
        
        return student_day, None

    def _fill_grouped_blocks(
        self,
        fill_classes: List[ScheduleDays],
        total_classes: int,
        student_classes_grouped: List[GroupedBlock]
    ) -> List[List[List[StudentClass]]]:
        matches = self._find_matches()
        group_blocks = []
        students_added = set()

        for c in fill_classes:
            days = self._create_fill_classes_days(total_classes)
            for student_block in student_classes_grouped:
                if c['block'] == student_block['block']:
                    for student_class in student_block['classes']:
                        if c['class_name'] == student_class['class_name']:
                            for match in matches:
                                for m in match.values():
                                    for people in m:
                                        for person in people:
                                            if person not in students_added:
                                                for i, student in enumerate(
                                                    student_class['students']
                                                ):
                                                    if student['student'] == person:
                                                        added = False
                                                        for day in days:
                                                            if len(day) < c['max_students']:
                                                                day.append(student)
                                                                students_added.add(person)
                                                                added = True
                                                                break
                                                        if not added:
                                                            days.append([student])
                                                    if i == len(student) - 1:
                                                        group_blocks.append(days)

                            shuffle(student_class['students'])
                            for i, student in enumerate(student_class['students']):
                                if student['student'] not in students_added:
                                    for day in days:
                                        added = False
                                        if len(day) < c['max_students']:
                                            day.append(student)
                                            students_added.add(student['student'])
                                            added = True
                                            break
                                    if not added:
                                        days.append([student])

                                if i == c['total_students'] - 1:
                                     group_blocks.append(days)
        return group_blocks

    def _find_matches(self) -> List[Dict[int, List[List[str]]]]:
        blocks = self.schedule_df['block'].sort_values().unique()
        total_blocks = self.schedule_df['block'].max()
        match_df = self.schedule_df.pivot(
            index='student',
            columns='block',
            values='class'
        ).reset_index()

        matches: List[Dict[int, List[List[str]]]] = []
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

    def _get_class_size(self) -> List[ScheduleTotalStudents]:
        class_size = (
            self.schedule_df.groupby(['block', 'class',])
            .size()
            .to_frame()
            .reset_index()
        )
        return [
            {'block': x[0], 'class_name': x[1], 'total_students': x[2]}
            for x in class_size.to_numpy()
        ]

    def _get_student_classes(self) -> List[StudentClass]:
        student_classes: List[StudentClass] = [
            {'block': x[1], 'class_name': x[2], 'student': x[0],}
                for x in self.schedule_df[['student', 'block', 'class']]
                .sort_values(by=['block', 'class',])
            .to_numpy()
        ]

        return student_classes

    def _get_total_classes(self, reduced_classes: List[ReducedClass]) -> int:
        total_classes = 1
        for c in reduced_classes:
            if c['num_classes'] > total_classes:
                total_classes = c['num_classes']
    
        return total_classes

    def _group_blocks(self) -> List[GroupedBlock]:
        student_classes = self._get_student_classes()
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

    def _init_classes(self, reduce_by: float, smallest_allowed: int) -> List[ScheduleDays]:
        class_sizes = self._get_class_size()
        reduced_classes = self._reduce_class(
            class_size=class_sizes,
            reduce_by=reduce_by,
            smallest_allowed=smallest_allowed
        )
        total_classes = self._get_total_classes(reduced_classes)
        classes: List[ScheduleDays] = []
        
        for c in class_sizes:
            class_append: ScheduleDays = c # type: ignore
            class_list: List[Set] = []
            for i in range(total_classes):
                class_list.append(set())

            class_append['classes'] = class_list
            classes.append(class_append)

        return classes

    def _load_file(self, file_path: str) -> pd.DataFrame:
        df = pd.read_excel(file_path)

        return df.dropna()

    def _reduce_class(
        self,
        class_size: List[ScheduleTotalStudents],
        reduce_by: float,
        smallest_allowed: int
    ) -> List[ReducedClass]:
        reduced_class: List[ReducedClass] = class_size # type: ignore
        for c in reduced_class:
            reduced = floor(c['total_students']  * reduce_by)
            if reduced > smallest_allowed:
                size = reduced
            else:
                size = smallest_allowed

            num_classes = ceil(c['total_students'] / size)
            c['max_students'] = size
            c['num_classes'] = num_classes

        return reduced_class

    def _save_schedule_to_file(self, df: pd.DataFrame, save_path: str) -> None:
        df = df.sort_values(by=['day_number', 'block', 'class'])
        df.to_excel(save_path, index=False, engine='xlsxwriter')

    def _validate_classes(self, reduced_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        df_main_grouped = self.schedule_df.groupby('student').size().to_frame('original')
        df_reduced_grouped = reduced_df.groupby('student').size().to_frame('scheduled')
        df_merge = df_main_grouped.merge(df_reduced_grouped, on='student')
        
        if df_merge.empty:
            return None

        return df_merge

    def _validate_students(self, reduced_df: pd.DataFrame) -> Optional[List[str]]:
        missing = []
        for student in self.schedule_df['student'].unique().tolist():
            if student not in reduced_df['student'].unique().tolist():
                missing.append(student)

        if len(missing) == 0:
            return None

        return missing