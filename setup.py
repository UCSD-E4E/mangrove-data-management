from setuptools import setup, find_packages

setup(
    name="MangroveDataManagement",
    version="0.0.0.1",
    author="Chris Crutchfield",
    author_email="ccrutchf@eng.ucsd.edu",
    entry_points={
        'console_scripts': [
            'MangroveDataManagement = MangroveDataManagement.manager:main',
        ],
    },
    packages=find_packages(),
    install_requires=[
        "tkcalendar>=1.6.1",
        "pytz>=2021.3",
        "pywin32>=303"
    ]
)