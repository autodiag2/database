The collaborative database of information relative to automotive.  
The goal is to provide an easily updatable database for scantools and  
fill the gap that makes open source solution weak.  
What you can find specifically in this db:
 - OBD DTCs; manufacturer specific, ecu specific, generic (eg P1000)
 - UDS DTCs (eg. 0x0F4231)
 - ECU information (manufacturer, model, version, mcu)
 - Vehicle brand, version, engines
 - and more !

You can browse the database [online](https://autodiag2.github.io/tools/dtc_query/index.html)

# Contributing
The easiest way to contribute is to edit yaml files.
for example [B1000.yml](/data/vehicle/acura/1/dtc/B1000.yml),
don't forget to add your sources in the evidence section.
Then with the manager the data will be compiled to sqlite.

# Data manager
[See](/manager/README.md) for installation

# Using the data
Compiled database are in [releases](https://github.com/autodiag2/database/releases)  

- **Optimized SQLite database** (normalized schema with relationships, smallest disk footprint):  
  [`ad_database.sqlite`](https://github.com/autodiag2/database/releases/latest/download/ad_database.sqlite)

See [this](/doc/using_data.md) for more information
