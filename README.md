# FemPy
A Python package for finite element models using Firedrake

## Setup

[Install Firedrake](https://www.firedrakeproject.org/download.html).

Download FemPy with 

    git clone git@github.com:geo-fluid-dynamics/fempy.git

Verify that tests pass as expected with

    python3 -m pytest -v -s -k "not fails" fempy/

Install with

    python3 fempy/setup.py install
    
## Development
### Project structure
This project mostly follows the structure suggested by [The Hitchhiker's Guide to Python](http://docs.python-guide.org/en/latest/).

### Guidelines
Mostly we try to follow PEP proposed guidelines, e.g. [The Zen of Python (PEP 20)](https://www.python.org/dev/peps/pep-0020/), and do not ever `from firedrake import *` ([PEP 8](https://www.python.org/dev/peps/pep-0008/)).
