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

- `id`: Unikátní identifikátor okruhu. Musí odpovídat id z [`zones_config.json`](./../config/zones_config.json)
- `irrigation_state`: Aktuální stav okruhu (ventilu). Může být: `idle`, `irrigating`. ZMĚNIT NA CIRCUIT_STATE A UDRŽOVAT STAV Z OBJEKTU (VOLAT MANAGER V SETTRU OKRUHU)
- `last_irrigation`: Datum a čas posledního zavlažování v ISO 8601 formátu (např. 2025-06-21T20:00:00).
- `last_result`: Výsledek posledního pokusu o zavlažování. Může být: `success`, `skipped`, `interrupted`, `error`, nebo `null` (pokud zatím nikdy neproběhlo).
- `last_duration`: Délka posledního zavlažování v sekundách. `null`, pokud zatím nikdy neproběhlo.


Pozn.:
- Hodnoty `null` jsou použity pro nové okruhy nebo takové, které zatím nebyly zavlažovány.
- Všechny časové údaje jsou v UTC nebo je třeba si je sjednotit s ostatními částmi systému.
- Tento soubor bude obvykle spravovat třída `CircuitStateManager`, která zajišťuje načtení, aktualizaci a zápis.
- Je potřeba zajistit atomicitu operací zavlažení a aktualizace souboru `zones_state.json`.