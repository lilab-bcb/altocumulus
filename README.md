# altocumulus

Command line utilities for running workflows on [Terra](https://app.terra.bio/) including:

- Add/update methods in Terra.
- Generate a Terra WDL input.json stub.
- Run a Terra method. Replace local file paths with workspace Google Cloud bucket URLs. Automatically 
    upload referenced files to workspace Google bucket.
- Bulk add/delete methods in Terra. 
- Parse monitoring log files to determine optimal instance type and disk space.


## Installation

    git clone https://github.com/klarman-cell-observatory/altocumulus.git
    cd altocumulus
    pip install -e .

## Usage
- Type `alto` for a list of all commands.


## Release note

Version 1.1.1, make sure that float values would look the same as in json input. For example, if 0.00005 is given, altocumulus will pass '0.00005' instead of '5e-05' to Terra.

