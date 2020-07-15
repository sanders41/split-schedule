from pathlib import Path
from setuptools import find_packages, setup

HERE = Path(__file__).parent
README = (HERE.joinpath('README.md').read_text())

setup(
    name='split_schedule',
    version='0.1.0',
    author='Paul Sanders',
    author_email='psanders1@gmail.com',
    description='Split schedule into smaller class sizes',
    long_description=README,
    long_description_content_type='text/markdown',
    packages=['split_schedule'],
    install_requires=[
        'pandas>=1.0.4',
        'openpyxl>=3.0.4',
        'XlsxWriter==1.2.9',
    ],
    classifiers=[
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent'
    ],
)
