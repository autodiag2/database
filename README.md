
Database of cars and engines used by autodiag.  
It also includes a VIN decoder.

# One file download
[dtc.sqlite](https://github.com/autodiag2/database/releases): one table: dtc(id, desc, manufacturer, engine_model, ecu_model)

# Add a new car to the database
```bash
./scripts/newCarDescription.sh
```

# Decode VIN
See scripts/VIN/README.md

# Compile DTCs database
```bash
python scripts/compile_dtcs_database.py
```
