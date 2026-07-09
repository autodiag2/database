# Optimized SQLite database
![UML of the database](/doc/ad_database_sqlite_uml.png)  
Sources, severity, and any information that a scantool needs.

### Standard OBD DTCs (saej2012.2002)
```sql
SELECT
    d.code,
    d.definition,
    d.description
FROM ad_dtc AS d
JOIN ad_ecu AS e
    ON e.id = d.ecu_id
WHERE e.model = 'saej2012.2002'
ORDER BY d.code;
```
### Retrieve DTC definition of P1110
```sql
SELECT
    d.code,
    d.definition,
    d.description,
    m.name AS manufacturer,
    e.model AS ecu_model
FROM ad_dtc AS d
JOIN ad_ecu AS e
    ON e.id = d.ecu_id
LEFT JOIN ad_manufacturer AS m
    ON m.id = e.manufacturer_id
WHERE d.code = 'P1110'
ORDER BY m.name, e.model;
```