### Run
```bash
vindecoder_cli 4S4BSAJC9K3287952
vindecoder_cli 2010 4S4BSAJC9K3287952
```
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
#### Tests
```bash
python ./vindecoder/tests/test_decoder.py
```
#### Build
```bash
poetry build
```

### Decode manually
 - https://fr.wikipedia.org/wiki/Code_constructeur-WMI  
 - http://renaultconcepts.online.fr/ressources/codes/codes-vin-auto.htm  
 - https://carinfo.kiev.ua/cars/vin/audi  
 - https://en.wikibooks.org/wiki/Vehicle_Identification_Numbers_(VIN_codes)/Toyota/VIN_Codes  
 - https://en.wikibooks.org/wiki/Vehicle_Identification_Numbers_(VIN_codes)/Peugeot/VIN_Codes  
 - https://citroen.c5x7.fr/vin  
 - https://en.wikibooks.org/wiki/Vehicle_Identification_Numbers_(VIN_codes)  
 - https://www.1aauto.com/content/articles/vin-number-decoding  
 - https://fr.wikipedia.org/wiki/Vehicle_Identification_Number  
 - https://cptdb.ca/wiki/index.php/Vehicle_Identification_Number_Explanation/VDS  
 - https://web.archive.org/web/20060211083930/http://www.aiam.org/vin/2000VINBOOK.pdf  