
# Smart Irrigation System (MVP)

Tento projekt je minimalistický prototyp inteligentního zavlažovacího systému řízeného mikrokontrolérem Raspberry Pi Pico.

## 🔧 Funkcionality (MVP)

- Zavlažování více okruhů sekvenčně / paralelně dle konfigurace
- Možnost ručního spuštění zavlažování všech nebo jednotlivých okruhů
- Výpočet množství vody podle globálních podmínek z meteostanice
- Možnost pozastavení/zapnutí automatického režimu
- Logování zavlažování a stavových hlášek
- Načítání konfigurace ze souboru (JSON)
- Příprava na synchronizaci konfigurace s centrálním Raspberry Pi 4

## 📁 Struktura konfigurace

- `config_global.json`: Globální konfigurace systému
- `zones_config.json`: Definice všech zavlažovacích okruhů a jejich konfigurace
- `zones_state.json`: Aktuální stav každého z okruhů

## 📜 Logování

Každé Raspberry Pi Pico zapisuje log do vlastního souboru `irrigation_log.txt`.

## 📅 Automatické zavlažování

Automatika může být zapnutá či vypnutá. V automatickém režimu systém zalévá každý den v nastavený čas.

## 🔌 Požadavky

- Raspberry Pi Pico (standalone režim)
- Python + knihovny `json`, `time`, `threading`

## 💡 Budoucí rozšíření

- Lokální senzory vlhkosti pro okruh
- Webové rozhraní pro řízení
- Integrace s Home Assistantem

## 🗒️ Poznámky

- Pojem `zóna` je v kontextu projektu synonymum pojmu `okruh`