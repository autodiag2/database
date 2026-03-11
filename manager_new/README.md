### Develop
#### Install
```bash
conda create -y -n autodiag python=3.11 ; \
    conda activate autodiag && \
    pip install poetry && \
    poetry install --no-root && \
    pip install -e .
```
#### Build
```bash
poetry build
```

### Run
```bash
ad_db_manager
```