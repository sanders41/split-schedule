# Split Schedule

# Instillation
Start by cloaning this repository.
```
git clone https://github.com/sanders41/sas7bdat_converter.git
```
* Note Python 3.8 or greater is required
  
Using a virtual environmnet is recommended for installing this package. Once the virtual environment is created activate it and run the setup script.
```
pip install .
```

# Useage
## Arguments
* -h, --help: show this help message and exit
* -f file_path: Required
  * The path to the file containing the original schedule
* -o, --output_file_path: Required
  * The path (including file name) where the generated schedule should be saved
* -r, --reduce_by, Required
  * The percentage (expressed as a decimal) by which the class size should be reduced
* -s, --smallest_allowed: Optional
  * The smallest number of students a class should be reduced. If this number is greater than the calculated reduce by value then reduce by will be overriden, and this will be used to reduce class sized. For example, if the maximum number of students after reduction is calculated to 5, but smallest allowe is set to 7 then 7 will be used instead of 5. It is possible to have 1 class that is smaller than the smallest allowed if the final day does not have enough students for the smallest allowed.