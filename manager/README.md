### Develop
#### Install
##### From Release
```bash
wget https://github.com/autodiag2/database/releases/latest/download/manager-0.2.0-py3-none-any.whl
pip install manager-*-py3-none-any.whl
```
##### From sources
```bash
conda create -y -n manager python=3.11 ; \
    conda activate manager && \
    pip install poetry && \
    poetry install --no-root && \
    pip install -e .
```
#### Build
```bash
poetry build
```

### Run
Manage the data from a gui
```bash
manager
```
