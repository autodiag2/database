### Develop
#### Install
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
Compile dtcs as a single file
```bash
compile_dtcs
```