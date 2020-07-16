import argparse
import sys
from pathlib import Path
from typing import List

from split_schedule.schedule_builder import ScheduleBuilder


class FileCheckAction(argparse.Action):
    def __call__( # type: ignore
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        value: Path,
        option_stirng: str,
    ) -> None:
        """
        Checks to make sure the file specified in the arguments exists. If the file is not
        found a ValueError exception in raised.
        """
        if not value.exists():
            raise ValueError(f"Unable to find file: {value}")

        setattr(namespace, self.dest, value)  # all is well so keep the file that was sent


def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--file_path",
        required=True,
        type=Path,
        action=FileCheckAction,
        dest="file_path",
        help="The path to the file containing the original schedule",
    )
    parser.add_argument(
        "-o",
        "--output_file_path",
        required=True,
        type=Path,
        dest="output_file_path",
        help="The path (including file name) where the generated schedule should be saved",
    )
    parser.add_argument(
        "-r",
        "--reduce_by",
        required=True,
        type=float,
        dest="reduce_by",
        help="The percentage (expressed as a decimal) by which the class size should be reduced",
    )
    parser.add_argument(
        "-s",
        "--smallest_allowed",
        required=False,
        type=int,
        default=1,
        dest="smallest_allowed",
        help="If this number is greater than the calculated reduce by value then reduce by will be overriden, and this will be used to reduce class sized. The default value is 1",
    )
    parser.add_argument(
        "-m",
        "--max_retries",
        required=False,
        type=int,
        default=10,
        dest="max_tries",
        help="The maximum number of times the program will try to find a possible schedule if an attempted schedule was not found. The default value is 10",
    )

    return parser.parse_args(args)


def main() -> None:
    args = parse_args(sys.argv[1:])
    schedule_builder = ScheduleBuilder(str(args.file_path))
    schedule_builder.build_schedule(
        reduce_by=args.reduce_by,
        save_path=str(args.output_file_path),
        smallest_allowed=args.smallest_allowed,
        max_tries=args.max_tries,
    )


if __name__ == "__main__":
    main()
