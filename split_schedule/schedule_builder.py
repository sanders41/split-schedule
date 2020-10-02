import logging
from itertools import combinations
from math import ceil, floor
from random import randrange
from typing import Dict, List, Optional, Set

import numpy as np
import pandas as pd

from split_schedule.schedule_types import ReducedClass, ScheduleDays, ScheduleTotalStudents

logging.basicConfig(format="%(asctime)s: %(levelname)s: %(message)s")
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
        self, reduce_by: float, save_path: str, smallest_allowed: int = 1, max_tries: int = 10
    ) -> None:
        logger.info("Getting student classes")
        student_classes_grouped = self._get_student_classes()
        logger.info("Getting student classes complete")

        logger.info("Initalizing classes")
        classes = self._init_classes(reduce_by, smallest_allowed)
        logger.info("Initalizing classes complete")

        logger.info("Getting class sizes")
        class_size = self._get_class_size()
        logger.info("Getting class sizes complete")

        logger.info("Reducing class sizes")
        reduced_classes = self._reduce_class(
            class_size=class_size, reduce_by=reduce_by, smallest_allowed=smallest_allowed
        )
        logger.info("Reducing class sizes complete")

        logger.info("Getting total classes needed")
        total_classes = self._get_total_classes(reduced_classes)
        logger.info("Getting total classes needed complete")

        logger.info(f"Schedule build try number {self._attempt}")

        logging.info("Filling blocks")
        fill_classes = self._fill_classes(
            classes,
            total_classes,
            student_classes_grouped,
        )
        logging.info("Filling blocks complete")

        if fill_classes:
            logger.info("Formatting classes")
            fill_class_df = self._expand_fill_classes(fill_classes)
            logger.info("Formatting classes complete")

            logger.info("Validating generated schedule")
            validated_class_size = self._validate_class_size(fill_class_df)
            validated_classes_numbers = self._validate_classes(fill_class_df)
            validated_same_days = self._validate_same_day(fill_class_df)
            validated_students = self._validate_students(fill_class_df)

            if validated_class_size is not None:
                logger.error("Classes contain too many students")

            if validated_classes_numbers is not None:
                logger.error("Student missing from the generated schedule")

            if validated_same_days is not None:
                logger.error("Student not on the same day")

            if validated_students:
                logger.error(
                    "Student original number of classes and generated number of classes do not match"  # noqa: E501
                )

            if (
                validated_class_size is not None
                or validated_classes_numbers is not None
                or validated_same_days is not None
                or validated_students
            ):
                if self._attempt < max_tries:
                    self._attempt += 1
                    self.build_schedule(reduce_by, save_path, smallest_allowed, max_tries)
                else:
                    raise SchedulingError("No possible schedule found")

            logger.info("Validation complete")

            logger.info(f"Saving schedule to {save_path}")
            self._save_schedule_to_file(fill_class_df, save_path)
            logger.info("Saving schedule complete")
        else:
            if self._attempt < max_tries:
                logger.info("No schedule found. Retrying")
                self._attempt += 1
                self.build_schedule(reduce_by, save_path, smallest_allowed, max_tries)
            else:
                raise SchedulingError("No possible schedule found")

    def _expand_fill_classes(self, fill_classes: List[ScheduleDays]) -> pd.DataFrame:
        fill_classes_expanded = []
        for fill in fill_classes:
            for i, c in enumerate(fill["classes"]):
                for student in c:
                    row = {
                        "block": fill["block"],
                        "class_name": fill["class_name"],
                        "total_students": fill["total_students"],
                        "max_students": fill["max_students"],
                        "num_classes": fill["num_classes"],
                        "day_number": i + 1,
                        "student": student,
                    }
                    fill_classes_expanded.append(row)

        fill_class_df = pd.DataFrame(fill_classes_expanded)
        fill_class_df = fill_class_df.rename(columns={"class_name": "class"})

        return fill_class_df

    def _fill_classes(
        self,
        fill_classes: List[ScheduleDays],
        total_classes: int,
        student_classes_grouped: Dict[str, Dict[str, Dict[int, str]]],
    ) -> Optional[List[ScheduleDays]]:
        matches = self._find_matches()
        students_added = set()

        total_days = len(fill_classes[0]["classes"])

        for match in matches:
            for m in match.values():
                for people in m:
                    day = randrange(total_days)
                    for person in people:
                        if person not in students_added:
                            day_tried = day
                            days: List[int] = []
                            to_add = []
                            while len(days) < total_days:
                                for c in fill_classes:
                                    if (
                                        c["class_name"]
                                        == student_classes_grouped[person]["blocks"].get(c["block"])
                                        and len(c["classes"][day_tried]) < c["max_students"]
                                    ):
                                        add = {
                                            "student": person,
                                            "block": c["block"],
                                            "class_name": c["class_name"],
                                            "class_day": day_tried,
                                        }
                                        if add not in to_add:
                                            to_add.append(add)
                                if len(to_add) == len(student_classes_grouped[person]["blocks"]):
                                    break

                                to_add = []
                                days.append(day_tried)
                                for i in range(total_days):
                                    if i not in days:
                                        day_tried = i
                                        break

                            if len(to_add) == len(student_classes_grouped[person]["blocks"]):
                                for a in to_add:
                                    for c in fill_classes:
                                        if (
                                            c["block"] == a["block"]
                                            and c["class_name"] == a["class_name"]
                                            and len(c["classes"][day_tried]) < c["max_students"]
                                        ):
                                            c["classes"][a["class_day"]].add(  # type: ignore
                                                a["student"]
                                            )
                                students_added.add(person)
                            else:
                                return None

        day = randrange(total_days)
        for student_name in student_classes_grouped:
            if student_name not in students_added:
                day_tried = day
                days = []
                to_add = []
                while len(days) < total_days:
                    for c in fill_classes:
                        if (
                            c["class_name"]
                            == student_classes_grouped[student_name]["blocks"].get(c["block"])
                            and len(c["classes"][day_tried]) < c["max_students"]
                        ):
                            add = {
                                "student": student_name,
                                "block": c["block"],
                                "class_name": c["class_name"],
                                "class_day": day_tried,
                            }
                            if add not in to_add:
                                to_add.append(add)
                    if len(to_add) == len(student_classes_grouped[student_name]["blocks"]):
                        break

                    to_add = []
                    days.append(day_tried)
                    for i in range(total_days):
                        if i not in days:
                            day_tried = i
                            break
                if len(to_add) == len(student_classes_grouped[student_name]["blocks"]):
                    for a in to_add:
                        for c in fill_classes:
                            if (
                                c["block"] == a["block"]
                                and c["class_name"] == a["class_name"]
                                and len(c["classes"][day_tried]) < c["max_students"]
                            ):
                                c["classes"][a["class_day"]].add(a["student"])  # type: ignore
                    students_added.add(student_name)
                else:
                    return None

        return fill_classes

    def _find_matches(self) -> List[Dict[int, List[List[str]]]]:
        blocks = self.schedule_df["block"].sort_values().unique()
        total_blocks = self.schedule_df["block"].max()
        match_df = self.schedule_df.pivot(
            index="student", columns="block", values="class"
        ).reset_index()

        if len(self._attempted_df) == 0:
            self._attempted_df.append(match_df)
        else:
            logger.info("Finding unused student order")
            total_attempted_pre = len(self._attempted_df)
            total_attempted = len(self._attempted_df)
            attempt_number = 1
            while False in [match_df.equals(x) for x in self._attempted_df]:
                self._attempted_df.append(match_df)
                match_df = match_df.sample(frac=1)
                if attempt_number == total_attempted:
                    logger.info("No unused matches found")
                    break
                attempt_number += 1

            if len(self._attempted_df) <= total_attempted_pre:
                logger.info("No unused matches found")
            else:
                logger.info("Unused student order found")

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

    def _get_class_size(self) -> List[ScheduleTotalStudents]:
        class_size = (
            self.schedule_df.groupby(
                [
                    "block",
                    "class",
                ]
            )
            .size()
            .to_frame()
            .reset_index()
        )
        return [
            {"block": x[0], "class_name": x[1], "total_students": x[2]}
            for x in class_size.to_numpy()
        ]

    def _get_student_classes(self) -> Dict[str, Dict[str, Dict[int, str]]]:
        student_classes: Dict[str, Dict[str, Dict[int, str]]] = {}
        for student in (
            self.schedule_df[["student", "block", "class"]]
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

    def _get_total_classes(self, reduced_classes: List[ReducedClass]) -> int:
        total_classes = 1
        for c in reduced_classes:
            if c["num_classes"] > total_classes:
                total_classes = c["num_classes"]

        return total_classes

    def _init_classes(self, reduce_by: float, smallest_allowed: int) -> List[ScheduleDays]:
        class_sizes = self._get_class_size()
        reduced_classes = self._reduce_class(
            class_size=class_sizes, reduce_by=reduce_by, smallest_allowed=smallest_allowed
        )
        total_classes = self._get_total_classes(reduced_classes)
        classes: List[ScheduleDays] = []

        for c in class_sizes:
            class_append: ScheduleDays = c  # type: ignore
            class_list: List[Set] = []
            for _ in range(total_classes):
                class_list.append(set())

            class_append["classes"] = class_list
            classes.append(class_append)

        return classes

    def _load_data(self, file_path: str) -> pd.DataFrame:
        df = pd.read_excel(file_path, engine="openpyxl")
        df = df.dropna()
        return df

    def _reduce_class(
        self, class_size: List[ScheduleTotalStudents], reduce_by: float, smallest_allowed: int
    ) -> List[ReducedClass]:
        reduced_class: List[ReducedClass] = class_size  # type: ignore
        for c in reduced_class:
            reduced = floor(c["total_students"] * reduce_by)
            size = max(reduced, smallest_allowed)
            num_classes = ceil(c["total_students"] / size)
            c["max_students"] = size
            c["num_classes"] = num_classes

        return reduced_class

    def _save_schedule_to_file(self, df: pd.DataFrame, save_path: str) -> None:
        df = df.sort_values(by=["day_number", "block", "class"])
        df.to_excel(save_path, index=False, engine="xlsxwriter")

    def _validate_class_size(self, reduced_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        df = (
            reduced_df.groupby(["block", "class", "day_number"])
            .size()
            .to_frame("class_size")
            .reset_index()
        )
        reduced_df = (
            reduced_df[["block", "class", "max_students"]]
            .drop_duplicates()
            .merge(df, on=["block", "class"])
        )

        reduced_df["match"] = np.where(reduced_df["max_students"] >= reduced_df["class_size"], 1, 0)
        reduced_df = reduced_df[reduced_df["match"] == 0]

        if reduced_df.empty:
            return None

        return reduced_df.drop(columns=["match"])

    def _validate_classes(self, reduced_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        df_main_grouped = self.schedule_df.groupby("student").size().to_frame("original")
        df_reduced_grouped = reduced_df.groupby("student").size().to_frame("scheduled")
        df_merge = df_main_grouped.merge(df_reduced_grouped, on="student")

        df_merge = df_merge[df_merge["original"] != df_merge["scheduled"]]

        if df_merge.empty:
            return None

        return df_merge

    def _validate_same_day(self, reduced_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        reduced_df = reduced_df[["student", "day_number"]].drop_duplicates()
        reduced_df = reduced_df.groupby("student").size().to_frame("count").reset_index()
        reduced_df = reduced_df[reduced_df["count"] > 1]

        if reduced_df.empty:
            return None

        return reduced_df

    def _validate_students(self, reduced_df: pd.DataFrame) -> Optional[List[str]]:
        missing = [
            student
            for student in self.schedule_df["student"].unique().tolist()
            if student not in reduced_df["student"].unique().tolist()
        ]

        if not missing:
            return None

        return missing
