from __future__ import annotations

import logging
from itertools import combinations
from math import ceil, floor
from pathlib import Path
from random import randrange
from typing import Optional, Union

import numpy as np
import pandas as pd

from split_schedule.errors import NoScheduleError, SchedulingError
from split_schedule.schedule_types import ReducedClass, ScheduleDays, ScheduleTotalStudents


class ScheduleBuilder:
    def __init__(self) -> None:
        self.final_schedule_df: Optional[pd.DataFrame] = None

        self._schedule_df: pd.DataFrame = pd.DataFrame(columns=["block", "class", "student"])
        self._attempted_df: list[pd.DataFrame] = []
        self._attempt: int = 1
        self._verbose: bool = False

        logging.basicConfig(format="%(asctime)s: %(levelname)s: %(message)s")
        logging.root.setLevel(level=logging.INFO)
        self._logger = logging.getLogger()

    def build_schedule_from_df(
        self,
        df: pd.DataFrame,
        reduce_by: float = 0.2,
        smallest_allowed: int = 1,
        max_tries: int = 10,
        verbose: bool = False,
    ) -> None:
        self._schedule_df = df
        self._verbose = verbose
        self._build_schedule(reduce_by, smallest_allowed, max_tries)

    def build_schedule_from_file(
        self,
        schedule_file_path: Union[Path, str],
        reduce_by: float = 0.2,
        smallest_allowed: int = 1,
        max_tries: int = 10,
        verbose: bool = False,
    ) -> None:
        file_path = (
            Path(schedule_file_path) if isinstance(schedule_file_path, str) else schedule_file_path
        )

        if file_path.suffix == ".xlsx":
            self._schedule_df = pd.read_excel(file_path)
        elif file_path.suffix == ".csv":
            self._schedule_df = pd.read_csv(file_path)
        else:
            raise ValueError("File should either be an xlsx Excel or a csv file")

        self._verbose = verbose
        self._build_schedule(reduce_by, smallest_allowed, max_tries)

    def save_schedule(self, save_path: Union[Path, str]) -> None:
        if self.final_schedule_df is None:
            raise NoScheduleError("No schedule has been generated")

        file_path = Path(save_path) if isinstance(save_path, str) else save_path

        if self._verbose:
            self._logger.info(f"Saving schedule to {save_path}")

        if file_path.suffix == ".xlsx":
            self.final_schedule_df.to_excel(file_path, index=False, engine="openpyxl")
        elif file_path.suffix == ".csv":
            self.final_schedule_df.to_csv(file_path, index=False)
        else:
            raise ValueError("The output file should either be an xlsx Excel or a csv file")

        if self._verbose:
            self._logger.info("Saving schedule complete")

    def _build_schedule(
        self, reduce_by: float, smallest_allowed: int = 1, max_tries: int = 10
    ) -> None:
        if self._verbose:
            self._logger.info("Getting student classes")

        student_classes_grouped = self._get_student_classes()

        if self._verbose:
            self._logger.info("Getting student classes complete")

        if self._verbose:
            self._logger.info("Initalizing classes")

        classes = self._init_classes(reduce_by, smallest_allowed)

        if self._verbose:
            self._logger.info("Initalizing classes complete")

        if self._verbose:
            self._logger.info("Getting class sizes")

        if self._verbose:
            self._logger.info("Getting class sizes complete")

        if self._verbose:
            self._logger.info("Reducing class sizes")

        if self._verbose:
            self._logger.info("Reducing class sizes complete")

        if self._verbose:
            self._logger.info("Getting total classes needed")

        if self._verbose:
            self._logger.info("Getting total classes needed complete")

        if self._verbose:
            self._logger.info(f"Schedule build try number {self._attempt}")

        if self._verbose:
            self._logger.info("Filling blocks")

        fill_classes = self._fill_classes(
            classes,
            student_classes_grouped,
        )

        if self._verbose:
            self._logger.info("Filling blocks complete")

        if fill_classes:
            if self._verbose:
                self._logger.info("Formatting classes")

            fill_class_df = self._expand_fill_classes(fill_classes)

            if self._verbose:
                self._logger.info("Formatting classes complete")

            self._validate_generated_schedule(fill_class_df, reduce_by, smallest_allowed, max_tries)
        else:
            if self._attempt >= max_tries:
                raise SchedulingError("No possible schedule found")

            if self._verbose:
                self._logger.info("No schedule found. Retrying")

            self._attempt += 1
            self._build_schedule(reduce_by, smallest_allowed, max_tries)

    def _expand_fill_classes(self, fill_classes: list[ScheduleDays]) -> pd.DataFrame:
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
        fill_classes: list[ScheduleDays],
        student_classes_grouped: dict[str, dict[str, dict[int, str]]],
    ) -> Optional[list[ScheduleDays]]:
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
                            days: list[int] = []
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

                            if len(to_add) != len(student_classes_grouped[person]["blocks"]):
                                return None

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
        day = randrange(total_days)
        for student_name, value in student_classes_grouped.items():
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
                    if len(to_add) == len(value["blocks"]):
                        break

                    to_add = []
                    days.append(day_tried)
                    for i in range(total_days):
                        if i not in days:
                            day_tried = i
                            break
                if len(to_add) != len(student_classes_grouped[student_name]["blocks"]):
                    return None

                for a in to_add:
                    for c in fill_classes:
                        if (
                            c["block"] == a["block"]
                            and c["class_name"] == a["class_name"]
                            and len(c["classes"][day_tried]) < c["max_students"]
                        ):
                            c["classes"][a["class_day"]].add(a["student"])  # type: ignore
                students_added.add(student_name)
        return fill_classes

    def _find_matches(self) -> list[dict[int, list[list[str]]]]:
        blocks = self._schedule_df["block"].sort_values().unique()
        total_blocks = self._schedule_df["block"].max()
        match_df = self._schedule_df.pivot(
            index="student", columns="block", values="class"
        ).reset_index()

        if len(self._attempted_df) == 0:
            self._attempted_df.append(match_df)
        else:
            if self._verbose:
                self._logger.info("Finding unused student order")

            total_attempted_pre = len(self._attempted_df)
            total_attempted = len(self._attempted_df)
            attempt_number = 1
            while False in [match_df.equals(x) for x in self._attempted_df]:
                self._attempted_df.append(match_df)
                match_df = match_df.sample(frac=1)
                if attempt_number == total_attempted:
                    if self._verbose:
                        self._logger.info("No unused matches found")
                    break
                attempt_number += 1

            if self._verbose:
                if len(self._attempted_df) <= total_attempted_pre:
                    self._logger.info("No unused matches found")
                else:
                    self._logger.info("Unused student order found")

        matches: list[dict[int, list[list[str]]]] = []
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

    def _get_class_size(self) -> list[ScheduleTotalStudents]:
        class_size = (
            self._schedule_df.groupby(
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

    def _get_student_classes(self) -> dict[str, dict[str, dict[int, str]]]:
        student_classes: dict[str, dict[str, dict[int, str]]] = {}
        for student in (
            self._schedule_df[["student", "block", "class"]]
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

    def _get_total_classes(self, reduced_classes: list[ReducedClass]) -> int:
        total_classes = 1
        for c in reduced_classes:
            if c["num_classes"] > total_classes:
                total_classes = c["num_classes"]

        return total_classes

    def _init_classes(self, reduce_by: float, smallest_allowed: int) -> list[ScheduleDays]:
        class_sizes = self._get_class_size()
        reduced_classes = self._reduce_class(
            class_size=class_sizes, reduce_by=reduce_by, smallest_allowed=smallest_allowed
        )
        total_classes = self._get_total_classes(reduced_classes)
        classes: list[ScheduleDays] = []

        for c in class_sizes:
            class_append: ScheduleDays = c  # type: ignore
            class_list: list[set] = []
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
        self, class_size: list[ScheduleTotalStudents], reduce_by: float, smallest_allowed: int
    ) -> list[ReducedClass]:
        reduced_class: list[ReducedClass] = class_size  # type: ignore
        for c in reduced_class:
            reduced = floor(c["total_students"] * reduce_by)
            size = max(reduced, smallest_allowed)
            num_classes = ceil(c["total_students"] / size)
            c["max_students"] = size
            c["num_classes"] = num_classes

        return reduced_class

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
        df_main_grouped = self._schedule_df.groupby("student").size().to_frame("original")
        df_reduced_grouped = reduced_df.groupby("student").size().to_frame("scheduled")
        df_merge = df_main_grouped.merge(df_reduced_grouped, on="student")

        df_merge = df_merge[df_merge["original"] != df_merge["scheduled"]]

        if df_merge.empty:
            return None

        return df_merge

    def _validate_generated_schedule(
        self,
        fill_class_df: pd.DataFrame,
        reduce_by: float,
        smallest_allowed: int = 1,
        max_tries: int = 10,
    ) -> None:
        if self._verbose:
            self._logger.info("Validating generated schedule")

        validated_class_size = self._validate_class_size(fill_class_df)
        validated_classes_numbers = self._validate_classes(fill_class_df)
        validated_same_days = self._validate_same_day(fill_class_df)
        validated_students = self._validate_students(fill_class_df)

        if self._verbose:
            if validated_class_size is not None:
                self._logger.error("Classes contain too many students")

            if validated_classes_numbers is not None:
                self._logger.error("Student missing from the generated schedule")

            if validated_same_days is not None:
                self._logger.error("Student not on the same day")

            if validated_students:
                self._logger.error(
                    "Student original number of classes and generated number of classes do not match"
                )

        if (
            validated_class_size is not None
            or validated_classes_numbers is not None
            or validated_same_days is not None
            or validated_students
        ):
            if self._attempt >= max_tries:
                raise SchedulingError("No possible schedule found")

            self._attempt += 1
            self._build_schedule(reduce_by, smallest_allowed, max_tries)

        if self._verbose:
            self._logger.info("Validation complete")

        self.final_schedule_df = fill_class_df.sort_values(by=["day_number", "block", "class"])

        if self._verbose:
            self._logger.info("Saving schedule complete")

    def _validate_same_day(self, reduced_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        reduced_df = reduced_df[["student", "day_number"]].drop_duplicates()
        reduced_df = reduced_df.groupby("student").size().to_frame("count").reset_index()
        reduced_df = reduced_df[reduced_df["count"] > 1]

        if reduced_df.empty:
            return None

        return reduced_df

    def _validate_students(self, reduced_df: pd.DataFrame) -> Optional[list[str]]:
        missing = [
            student
            for student in self._schedule_df["student"].unique().tolist()
            if student not in reduced_df["student"].unique().tolist()
        ]

        if not missing:
            return None

        return missing
