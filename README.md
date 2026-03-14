The collaborative database of information relative to automotive.
The goal is to provide an easily updatable database for scantools for example and
fill the gap that make open source solution weak.
What you can find specifically in this db:
 - OBD DTCs (manufacturer specific, generic, eg. P1000)
 - UDS DTCs (eg. 0x0F4231)
 - ECU information (manufacturer model, version, firmware ?)

# Contributing
The easiest way to contribute is to edit yaml files.
for example [B1000.yml](/data/vehicle/acura/1/dtc/B1000.yml),
don't forget to add your sources in the evidence section.
Then with the manager the data will be compiled to sqlite.

# Data manager
[See](/manager/README.md) for installation  
Browse and manage the data:
![Browser](/doc/browser.png)
Query DTC:  
![Query](/doc/query.png)
