import logging
import numpy as np
import pandas as pd

from itertools import combinations, groupby
from math import ceil, floor
from operator import itemgetter
from random import randrange, shuffle
from split_schedule.schedule_types import (
    GroupedBlock,
    ReducedClass,
    ScheduleDays,
    ScheduleTotalStudents,
    StudentClass
)
from typing import Dict, List, Optional, Set, Tuple


logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchedulingError(Exception):
    pass


class ScheduleBuilder:
    def __init__(self, schedule_file_path: str) -> None:
        self.schedule_df = self._load_data(schedule_file_path)
        self._attempted_df: List[pd.DataFrame] = []
        self._attempt: int = 1

    def build_schedule(
        self,
        reduce_by: float,
        save_path: str,
        smallest_allowed: int=1,
        max_tries: int=100
    ) -> None:
        logger.info('Getting student classes')
        student_classes_grouped = self._get_student_classes()
        logger.info('Getting student classes complete')

        logger.info('Initalizing classes')
        classes = self._init_classes(reduce_by, smallest_allowed)
        logger.info('Initalizing classes complete')

        logger.info('Getting class sizes')
        class_size = self._get_class_size()
        logger.info('Getting class sizes complete')

        logger.info('Reducing class sizes')
        reduced_classes = self._reduce_class(
            class_size=class_size,
            reduce_by=reduce_by,
            smallest_allowed=smallest_allowed
        )
        logger.info('Reducing class sizes complete')

        logger.info('Getting total classes needed')
        total_classes = self._get_total_classes(reduced_classes)
        logger.info('Getting total classes needed complete')

        logger.info(f'Schedule build try number {self._attempt}')

        logging.info('Filling blocks')
        fill_classes = self._fill_classes(
            classes,
            total_classes,
            student_classes_grouped,
        )
        logging.info('Filling blocks complete')

        if fill_classes:
            logger.info('Formatting classes')
            fill_class_df = self._expand_fill_classes(fill_classes)
            logger.info('Formatting classes complete')

            logger.info('Validating generated schedule')
            validated_classes_numbers = self._validate_classes(fill_class_df)
            validated_same_days = self._validate_same_day(fill_class_df)
            validated_students = self._validate_students(fill_class_df)

            if validated_classes_numbers is not None:
                logger.error('Student missing from the generated schedule')
                print(validated_classes_numbers)

            if validated_same_days is not None:
                logger.error('Student not on the same day')
                print(validated_same_days)
            
            if validated_students:
                logger.error('Student original number of classes and generated number of classes do not match')
                print(validated_students)

            if (
                validated_classes_numbers is not None
                or validated_same_days is not None
                or validated_students
            ):
                if self._attempt < max_tries:
                    logger.info('No schedule found. Retrying')
                    self._attempt += 1
                    self.build_schedule(reduce_by, save_path, smallest_allowed, max_tries)
                else:
                    raise SchedulingError('Error generating schedule')

            logger.info('Validation complete')

            logger.info(f'Saving schedule to {save_path}')
            self._save_schedule_to_file(fill_class_df, save_path)
            logger.info('Saving schedule complete')
        else:
            if self._attempt < max_tries:
                logger.info('No schedule found. Retrying')
                self._attempt += 1
                self.build_schedule(reduce_by, save_path, smallest_allowed, max_tries)
            else:
                raise SchedulingError('Error generating schedule')
            

    def _create_fill_classes_days(self, total_classes: int) -> List[List]:
        days: List[List] = []
        for _ in range(total_classes):
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
        fill_classes: List[ScheduleDays],
        total_classes: int,
        student_classes_grouped: List[GroupedBlock]
    ) -> List[List[List[StudentClass]]]:
        matches = self._find_matches()
        group_blocks = []
        students_added = set()

        total_days = len(fill_classes[0]['classes'])

        for match in matches:
            for m in match.values():
                for people in m:
                    day = randrange(total_days)
                    for person in people:
                        if person not in students_added:
                            day_tried = day
                            days = []
                            to_add = []
                            while (len(days) < total_days):
                                for c in fill_classes:
                                    if c['class_name'] == student_classes_grouped[person]['blocks'].get(c['block']):
                                        add = {'student': person, 'block': c['block'], 'class_name': c['class_name'], 'class_day': day_tried}
                                        if add not in to_add:
                                            to_add.append(add)
                                if len(to_add) == len(student_classes_grouped[person]['blocks']):
                                    break

                                to_add = []
                                days.append(day_tried)
                                for i in range (total_days):
                                    if i not in days:
                                        day_tried = i
                                        break
                            if len(to_add) == len(student_classes_grouped[person]['blocks']):
                                for a in to_add:
                                    for c in fill_classes:
                                        if c['block'] == a['block'] and c['class_name'] == a['class_name']:
                                            c['classes'][a['class_day']].add(a['student'])
                                students_added.add(person)
                            else:
                                return None

        day = randrange(total_days)
        for student_name in student_classes_grouped:
            if student_name not in students_added:
                day_tried = day
                days = []
                to_add = []
                while (len(days) < total_days):
                    for c in fill_classes:
                        if c['class_name'] == student_classes_grouped[student_name]['blocks'].get(c['block']):
                            add = {'student': student_name, 'block': c['block'], 'class_name': c['class_name'], 'class_day': day_tried}
                            if add not in to_add:
                                to_add.append(add)
                    if len(to_add) == len(student_classes_grouped[student_name]['blocks']):
                        break

                    to_add = []
                    days.append(day_tried)
                    for i in range (total_days):
                        if i not in days:
                            day_tried = i
                            break
                if len(to_add) == len(student_classes_grouped[student_name]['blocks']):
                    for a in to_add:
                        for c in fill_classes:
                            if c['block'] == a['block'] and c['class_name'] == a['class_name']:
                                c['classes'][a['class_day']].add(a['student'])
                    students_added.add(student_name)
                else:
                    return None

        return fill_classes

    def _find_matches(self) -> List[Dict[int, List[List[str]]]]:
        blocks = self.schedule_df['block'].sort_values().unique()
        total_blocks = self.schedule_df['block'].max()
        match_df = self.schedule_df.pivot(
            index='student',
            columns='block',
            values='class'
        ).reset_index()

        if len(self._attempted_df) == 0:
            self._attempted_df.append(match_df)
        else:
            logger.info('Finding unused student order')
            while False not in [match_df.equals(x) for x in self._attempted_df]:
                self._attempted_df.append(match_df)
                match_df = match_df.sample(frac=1)
            logger.info('Unused student order found')

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
                if check:
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
        student_classes = {}
        for student in self.schedule_df[['student', 'block', 'class']].sort_values(by=['block', 'class',]).to_numpy():
            if student[0] in student_classes:
                student_classes[student[0]]['blocks'][student[1]] = student[2]
            else:
                student_classes[student[0]] = {'blocks': {student[1]: student[2]}}

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
            for _ in range(total_classes):
                class_list.append(set())

            class_append['classes'] = class_list
            classes.append(class_append)

        return classes

    def _load_data(self, file_path: str) -> pd.DataFrame:
        df = pd.read_excel(file_path)
        df = df.dropna()
        return df

    def _reduce_class(
        self,
        class_size: List[ScheduleTotalStudents],
        reduce_by: float,
        smallest_allowed: int
    ) -> List[ReducedClass]:
        reduced_class: List[ReducedClass] = class_size # type: ignore
        for c in reduced_class:
            reduced = floor(c['total_students']  * reduce_by)
            size = max(reduced, smallest_allowed)
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

        df_merge = df_merge[df_merge['original'] != df_merge['scheduled']]
        
        if df_merge.empty:
            return None

        return df_merge

    def _validate_same_day(self, reduced_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        reduced_df = reduced_df[['student', 'day_number']].drop_duplicates()
        reduced_df = reduced_df.groupby('student').size().to_frame('count').reset_index()
        reduced_df = reduced_df[reduced_df['count'] > 1]

        if reduced_df.empty:
            return None

        return reduced_df

    def _validate_students(self, reduced_df: pd.DataFrame) -> Optional[List[str]]:
        missing = [
            student
            for student in self.schedule_df['student'].unique().tolist()
            if student not in reduced_df['student'].unique().tolist()
        ]

        if not missing:
            return None

        return missing