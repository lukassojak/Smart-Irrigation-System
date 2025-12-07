# Stav zón zavlažovacího systému

Tento dokument popisuje strukturu a význam polí v konfiguračním souboru:

- [`zones_state.json`](./zones_state.json)

---

## 🔧 `zones_state.json`

Tento soubor slouží k uchovávání aktuálního stavu zavlažovacích okruhů v systému. Nejedná se o konfigurační soubor, ale o stavový soubor, který je aktualizován během nebo po zavlažování.

Používá se především pro:
- Výpočet, zda má být daný okruh dnes zavlažován (na základě intervalu dnů).
- Záznam výsledku posledního zavlažování (např. úspěšné, přeskakováno, chyba).
- Možnou budoucí analýzu zavlažovacího chování.

### last_updated:
Datum a čas poslední aktualizace tohoto souboru. Slouží pro ladění nebo audit.
Typ: `string`

### circuits:
Seznam jednotlivých zavlažovacích okruhů a jejich posledního známého stavu.
Typ: `array`



**Každý prvek v poli `circuits` obsahuje následující pole:

- `id`: Unikátní identifikátor okruhu. Musí odpovídat id z [`zones_config.json`](./../config/zones_config.json)
- `circuit_state`: Aktuální stav okruhu. Může být: `idle`, `irrigating`, `shutdown`.
- `last_decision`: Datum a čas (začátku) posledního rozhodnutí o zavlažování v ISO 8601 formátu (např. 2025-06-21T20:00:00). `null`, pokud zatím nikdy nebylo učiněno. *Nastaví se při každém rozhodnutí o zavlažování (včetně přeskakování).*
- `last_outcome`: Výsledek posledního pokusu o zavlažování. Může být: `success`, `failed`, `stopped`, `interrupted`, `skipped`, nebo `null` (pokud zatím nikdy neproběhlo). *Nastaví se až po dokončení zavlažování.*
- `last_irrigation`: Datum a čas (začátku) posledního zavlažování v ISO 8601 formátu (např. 2025-06-21T20:00:00). *Nastaví se až po dokončení zavlažování (v případě unclean shutdownu je nastaveno na čas restartu systému).*
- `last_duration`: Délka posledního zavlažování v sekundách. `null`, pokud zatím nikdy neproběhlo. `0` v případě, že `last_outcome` je `SKIPPED`. *Nastaví se až po dokončení zavlažování.*
- `last_volume`: Objem vody použitý při posledním zavlažování v litrech. `null`, pokud zatím nikdy neproběhlo. `0` v případě, že `last_outcome` je `SKIPPED`. *Nastaví se až po dokončení zavlažování.*

Datový model:
```python
"id": int
"circuit_state": SnapshotCircuitState enum
"last_decision": datetime | None
"last_irrigation": datetime | None
"last_outcome": IrrigationOutcome enum | None
"last_duration": int | None
"last_volume": float | None
```



Pozn.:
- V případě, kdy je `last_outcome` `SKIPPED`, jsou `last_irrigation`, `last_duration` a `last_volume` ponechány beze změny podle posledního skutečného zavlažování.
- Hodnoty `null` jsou použity pro nové okruhy nebo takové, které zatím nebyly zavlažovány.
- Všechny časové údaje jsou v UTC nebo je třeba si je sjednotit s ostatními částmi systému.
- Tento soubor bude obvykle spravovat třída `CircuitStateManager`, která zajišťuje načtení, aktualizaci a zápis.