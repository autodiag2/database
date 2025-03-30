### Develop
#### Install
```bash
conda create -n VINdecoder python=3.11 && \
    conda activate VINdecoder && \
    pip install poetry && \
    cd scripts/VIN/ && \
    poetry install --no-root && \
    pip install -e .
```