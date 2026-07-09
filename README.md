The collaborative database of information relative to automotive.
The goal is to provide an easily updatable database for scantools for example and
fill the gap that make open source solution weak.
What you can find specifically in this db:
 - OBD DTCs (manufacturer specific, generic, eg. P1000)
 - UDS DTCs (eg. 0x0F4231)
 - ECU information (manufacturer, model, version)

# Contributing
The easiest way to contribute is to edit yaml files.
for example [B1000.yml](/data/vehicle/acura/1/dtc/B1000.yml),
don't forget to add your sources in the evidence section.
Then with the manager the data will be compiled to sqlite.

# Data manager
[See](/manager/README.md) for installation

# Using the data
Compiled databases are in [releases](https://github.com/autodiag2/database/releases)  
Two formats are available:

- **Optimized SQLite database** (normalized schema with relationships, smallest disk footprint):  
  [`ad_database.sqlite`](https://github.com/autodiag2/database/releases/latest/download/ad_database.sqlite)

- **Simplified database** (denormalized, easier to consume):
  - [`ad_database_simple.json`](https://github.com/autodiag2/database/releases/latest/download/ad_database_simple.json)
  - [`ad_database_simple.sqlite`](https://github.com/autodiag2/database/releases/latest/download/ad_database_simple.sqlite)

See [this](/using_data.md) for more information