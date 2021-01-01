# Split Schedule

[![Tests Status](https://github.com/sanders41/split_schedule/workflows/Testing/badge.svg?branch=master&event=push)](https://github.com/sanders41/split_schedule/actions?query=workflow%3ATesting+branch%3Amaster+event%3Apush)
[![Lint Status](https://github.com/sanders41/split_schedule/workflows/Linting/badge.svg?branch=master&event=push)](https://github.com/sanders41/split_schedule/actions?query=workflow%3ALinting+branch%3Amaster+event%3Apush)
[![Coverage](https://codecov.io/github/sanders41/split_schedule/coverage.svg?branch=master)](https://codecov.io/gh/sanders41/split_schedule)

This progam takes a schools class list and reduces the number of students in each class by a specified amount. This is done by splitting the classes across day. Each individual student's day is kept the same for each of his/her classes.

The class list should be supplied as an Excel file with all students on a single sheet containing the columns:

* block = The class period as a number (i.e. 1, 2, 3, etc.)
* class = The name of the class
* student = The name of the student

The generated schedule will be an Excel file with the fillowing columns:

* block = The class period as a number (i.e. 1, 2, 3, etc.)
* class = The name of the class
* total_students = The total number of students for a block across all days
* max_students = The maximum number of students allowed in a block each day
* num_classes = The total number of days needed in order to allow for the maximum class size
* day_number = The day for the class. This can be used as desired. For example 1 = Monday, 2 = Tuesday, etc.
* student = The name of the student

# Instillation

Start by cloning this repository.

```
git clone https://github.com/sanders41/split_schedule.git

If you do not already have Poetry installed
you will need to install it with the instuctions here https://python-poetry.org/docs/#installation
```

**Note:** Python 3.8 or greater is required

Using a virtual environmnet is recommended for installing this package.
Once the virtual environment is created activate it and install the dependencies.

```
poetry install
```

# Usage

## Arguments

* -h, --help: show this help message and exit
* -f, --file_path: Required
  * The path to the file containing the original schedule
* -o, --output_file_path: Required
  * The path (including file name) where the generated schedule should be saved
* -r, --reduce_by, Required
  * The percentage (expressed as a decimal) by which the class size should be reduced
* -s, --smallest_allowed: Optional - Default = 1
  * The smallest number of students a class should be reduced. If this number is greater than the calculated reduce by value then reduce by will be overriden, and this will be used to reduce class sized. For example, if the maximum number of students after reduction is calculated to 5, but smallest allowe is set to 7 then 7 will be used instead of 5. It is possible to have 1 class that is smaller than the smallest allowed if the final day does not have enough students for the smallest allowed.

## Running the program

### Example using the default minimum class size of 1 and reducing the classes by 20%

```
python set_schedule.py -f /path/to/original_file.xlsx -o /path/to/generated_schedule.xlsx -r 0.2
```

**Note:** Example uses Mac/Linux type file paths. For Windows use paths like `c:\path\to\original_file.xlsx` and `c:\path\to\generated_schedule.xlsx`.

### Example reducing the class size by 30% or a minimum of 8 students, which ever is greater

```
python set_schedule.py -f /path/to/original_file.xlsx -o /path/to/generated_schedule.xlsx -r 0.3 -s 8
```

**Note:** Example uses Mac/Linux type file paths. For Windows use paths like `c:\path\to\original_file.xlsx` and `c:\path\to\generated_schedule.xlsx`.
