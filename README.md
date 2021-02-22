# Split Schedule

[![Tests Status](https://github.com/sanders41/split_schedule/workflows/Testing/badge.svg?branch=main&event=push)](https://github.com/sanders41/split-schedule/actions?query=workflow%3ATesting+branch%3Amain+event%3Apush)
[![Lint Status](https://github.com/sanders41/split_schedule/workflows/Linting/badge.svg?branch=main&event=push)](https://github.com/sanders41/split-schedule/actions?query=workflow%3ALinting+branch%3Amain+event%3Apush)
[![Coverage](https://codecov.io/github/sanders41/split-schedule/coverage.svg?branch=main)](https://codecov.io/gh/sanders41/split-schedule)

This package takes a class list and reduces the number of students in each class by a specified amount. This is done by splitting the classes across days. Each individual student's day is kept the same for each of his/her classes.

The class list should be supplied as an Excel(xlsx) file with all students on a single sheet, a csv file, or a Pandas DataFrame containing the columns:

- block = The class period as a number (i.e. 1, 2, 3, etc.)
- class = The name of the class
- student = The name of the student

The generated schedule will contain the fillowing columns:

- block = The class period as a number (i.e. 1, 2, 3, etc.)
- class = The name of the class
- total_students = The total number of students for a block across all days
- max_students = The maximum number of students allowed in a block each day
- num_classes = The total number of days needed in order to allow for the maximum class size
- day_number = The day for the class. This can be used as desired. For example 1 = Monday, 2 = Tuesday, etc.
- student = The name of the student

## Installation

**Note:** Python 3.8 or greater is required

Using a virtual environmnet is recommended for installing this package. Once the virtual environment is created and activated install the package with:

```sh
pip install split-schedule
```

## Usage

### ScheduleBuilder Methods

- build_schedule_from_df: Builds the schedule from a Pandas DataFrame
  - df: The DataFrame that contains the schedule to split
  - reduce_by (optinal): The amount by which the class size should be reduced. Default = 0.2
  - smallest_allowed (optinal): The smallest a class should be. This can be used to override the reduce_by amount in cases where the class would be smaller than the desired amount. For example if classes are being reduced 50% (0.5) if the smallest allowd class is 10 and a class has 10 students at the start, then all 10 of these students would be kept in one class rather than reducing the size below 10. Default = 1
  - max_tries (optinal): The maximum number of times the program will restart itself tying to find a viable schedule. If the maximum number of tries is exceded with no viable schedule found a SchedulingError error will occur meaning no possible way was found to split the schedule with parameters supplied. Default = 10
  - verbose (optinal): Setting verbose to True will result in log output being written to the terminal as the schedule is being build. Default = False
- build_schedule_from_file: Builds the schedule from either an Excel(xlsx) file or a csv file.
  - schedule_file_path: The path to the schedule file, including the name of the file. The file path can be either a string or a Path object. Excel files in xlsx format or csv files are accepted.
  - reduce_by (optinal): The amount by which the class size should be reduced. Default = 0.2
  - smallest_allowed (optinal): The smallest a class should be. This can be used to override the reduce_by amount in cases where the class would be smaller than the desired amount. For example if classes are being reduced 50% (0.5) if the smallest allowd class is 10 and a class has 10 students at the start, then all 10 of these students would be kept in one class rather than reducing the size below 10. Default = 1
  - max_tries (optinal): The maximum number of times the program will restart itself tying to find a viable schedule. If the maximum number of tries is exceded with no viable schedule found a SchedulingError error will occur meaning no possible way was found to split the schedule with parameters supplied. Default = 10
  - verbose (optinal): Setting verbose to True will result in log output being written to the terminal as the schedule is being build. Default = False
- save_schedule: Saves the generated schedule to a file.
  - save_path: The path to which the generated schedule file should be saved, including the desired name of the file. The file path can be either a string or a Path object. Excel files in xlsx format or csv files are accepted.

### ScheduleBuilder Properties

- final_schedule_df: This is a Pandas DataFrame that contains the generated schedule. Before the schedule is created the property will be `None`

## Examples

**Note:** Examples uses Mac/Linux type file paths. For Windows use paths like `c:\path\to\original_file.xlsx` and `c:\path\to\generated_schedule.xlsx`.

Create a schedule from an Excel file, then save the generated schedule to another Excel file.

```python
from split_schedule import ScheduleBuilder

schedule_builder = ScheduleBuilder()
schedule_builder.build_schedule_from_file("/path/to/file.xlsx")
schedule_builder.save_schedule("/path/to/generated_schedule.xlsx")
```

Create a schedule from an Excel file, then print the resulting schedule DataFrame.

```python
from split_schedule import ScheduleBuilder

schedule_builder = ScheduleBuilder()
schedule_builder.build_schedule_from_file("/path/to/file.xlsx")
print(schedule_builder.final_schedule_df)
```
