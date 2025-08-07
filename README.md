
# Smart Irrigation System (Minimum Viable Product)

### MVP
Tento projekt představuje **minimalistický prototyp chytrého zavlažovacího systému**, který využívá **Raspberry Pi Zero** k řízení jednotlivých zavlažovacích okruhů (zón).

### Stabilní verze
Systém MVP je navržen jako rozšiřitelný základ pro distribuovaný systém automatizovaného zavlažování s integrací s **Home Assistantem**, **Webovým UI** a centrálním serverem na **Raspberry Pi 4**.

---

## Architektura systému

### MVP
- Jeden zavlažovací uzel **Raspberry Pi Zero** pracuje v **standalone režimu** a je zodpovědný za několik zavlažovacích zón.
- Data o konfiguraci a stavu jsou uložena v lokálních JSON souborech.
- **Globální podmínky** získané přes API lokální meteostanice (např. teplota, sluneční svit, vlhkost za relevantní období) se využívají k výpočtu potřebné závlahy.
- Ventily jsou řízeny pomocí **relé**.

### Stabilní verze
- Systém je rozdělen do tří vrstev:  
  - **1. Uživatelská vrstva (UI) - Webová aplikace, Home Assistant, CLI**
  - **2. Centrální řídicí server (Raspberry Pi 4)**  
  - **3. Zavlažovací uzly (Raspberry Pi Zero)**

#### 1. Centrální řídicí server (RPi 4):
- Zajišťuje **sběr dat ze serveru meteostanice** – intenzita slunečního svitu, teplota, srážky, vlhkost atd.
- Zajišťuje **sběr dat k předpovědi počasí** prostřednictvím API.
- Získaná data k řízení závlahy zasílá na vyžádání jednotlivým uzlům
- Uchovává **konfiguraci všech zón** v jednom centrálním úložišti (v souboru JSON / prostřednictvím databáze MySQL).
- Zajišťuje **centrální sběr logů** ze všech uzlů (UART/MQTT + HTTPS v případě většího množství dat z logů - např. v případě předcházejícího výpadku spojení)
- Rozesílá aktualizace konfigurace a data k řízení závlahy jednotlivým uzlům (UART/MQTT).
- Hostuje **uživatelské rozhraní (webová aplikace, Home Assistant Dashboard)** pro správu systému.
- Poskytuje **CLI rozhraní**
- Provádí **analýzu a agregaci dat** (např. historie zavlažování, úspora vody, predikce podle počasí).

#### 2. Zavlažovací uzly (RPi Zero):
- Obdrží a lokálně uloží aktuální konfiguraci a data k řízení závlahy ze serveru.
- Stále fungují **autonomně** (fail-safe fallback): v případě výpadku komunikace pokračují v režimu podle posledně známé konfigurace.
- Vyhodnocují stav každé zóny a **lokálně spouští závlahu** podle instrukcí a případně podle **lokálních senzorů vlhkosti půdy**.
- Odesílají zpět na server **stavové zprávy, chyby a logy**.
- Jednotlivé uzly mohou mít různý počet zón a různé typy výstupů.

#### Komunikační rozhraní:
- **UART** pro uzly, které je možné spojit síťovým kabelem
- **MQTT** pro uzly, které není možné spojit síťovým kabelem, také jako fallback v případě neúspěšného pokusu o spojení přes UART

### Redundance a bezpečnost:
- Lokální konfigurace na uzlech slouží jako záloha při výpadku komunikace.
- Uzel pravidelně zasílá informace o svém stavu na centrální server.
- Komunikace mezi uzly a centrálním serverem je šifrovaná: MQTT over TLS + HTTPS
- Systém je navržen jako ***fail-safe***: při neznámém stavu nebo výpadku napájení nedojde k nekontrolovanému spuštění závlahy.
- Každý zavlažovací okruh je řízen samostatným vláknem, které je bezpečně ukončeno při přerušení. V případě přerušení, nebo nečekané chyby v programu je ventil vždy bezpečně uzavřen.
- Použití ventilu ***Normally-closed*** zajišťuje jeho uzavření, pokud dojde k chybě mimo program.
- Runtime stavový automat (`IDLE`, `IRRIGATING`, `WAITING`, `ERROR`) zabraňuje souběhu konfliktních operací.
- Ukládání stavů do JSON se umožňuje systému bezpečně zotavit z `Unclean Shutdown` situací.
- Systém validuje a filtruje extrémní hodnoty ze senzorů a dat o počasí, aby se předešlo přijetí chybných dat.
- Je zavedeno podrobné ***logování všech operací*** v několika úrovních, logy jsou ukládány lokálně na uzlu a také pravidelně zasílány na server.

#### Plánované rozšíření:
- Přidání watchdog mechanismu, který kontroluje aktivitu jednotlivých vláken a restartuje je v případě nečinnosti nebo zamrznutí
- Heartbeat mechanismus: server real-time monitoruje běh a stav uzlů
- OTA aktualizace firmware pro možnost vzdálené hromadné aktualizace softwaru uzlů
- Automatické zálohy konfigurace a logů na centrálním serveru
- Běh systému na vyhrazené síti bez přímého přístupu k internetu
- Autentizace ve webové aplikaci přes tokeny (např. JWT)
- Role-based Access Control pro webovou aplikaci
---

## Hlavní funkce 

### MVP
- **Řízení více zavlažovacích okruhů** – každý Pi Zero může řídit více výstupů (ventilů) s vlastní nezávislou logikou.
- **Sekvenční i souběžné (paralelní) zavlažování** – dle nastavení v konfiguraci. Při paralelním zavlažování je k dispozici funkce `max_flow_monitoring`, která sleduje aktuální potřebu průtoku vody a maximální dostupný průtok vody. Pokud by souběžné spuštění více okruhů překročilo limit, systém přepne do **hybridního režimu** a spouští některé zóny postupně, tak aby byl využit limit na maximum, ale nedošlo k přetížení.
- **Ruční spuštění** – možnost manuálně spustit všechny nebo vybrané okruhy.
- **Automatické denní zavlažování** – dle času a konfigurace.
- **Výpočet množství vody** – automatický výpočet aktuální potřeby vody pro okruh na základě globální konfigurace, lokální konfigurace, dat o počasí.
- **Konfigurace jednotlivých okruhů** - každý okruh může být zavlažován v jiné frekvenci, mít různou citlivost na jednotlivé projevy počasí, eviduje všechny zavlažovací emitory.
- **2 režimy výpočtu zavlažování**:
    - Rovnoměrný režim výpočtu: pokud je zavlažovaná plocha osazena zavlažovacími emitory rovnoměrně, je možné zadat požadovánou *bazální* (výchozí) hodnotu zavlažení jako výšku vodního sloupce v mm.
    - Nerovnoměrný režim výpočtu: pokud je zavlažovaná plocha osazena zavlažovacími emitory nerovnoměrně (např. velká rostlina emitor s celkovým průtokem 5L/h, malá rostlina 1L/h), požadovaná *bazální* hodnota zavlažení je zadána jako požadovaný objem vody vypuštěný *jedním zavlažovacím emitorem s nejmenším průtokem v konfiguraci* okruhu.
- **Možnost zapnout/vypnout automatický režim**.
- **Logování** – několik režimů logování činnosti a stavových hlášek do souboru.
- **Konfigurace pomocí JSON souborů** – připraveno na příjem z centrálního serveru a uživatelskou úpravu z webové aplikace / Home Assistantu.
- **Oddělený stav okruhů** – udržování aktuálního stavu (např. poslední zavlažování, aktivní stav) pro každý okruh.

---

## Struktura souborů a konfigurace

- `config_global.json`  
  Obsahuje globální nastavení systému, včetně:
  - Čas denního automatického spuštění
  - Povolení/zakázání automatického režimu
  - Globální parametry výpočtu (bazální počasí)
  - Obecné konstanty
  - Další informace v [`config_explained.md`](./config/config_explained.md)

- `zones_config.json`  
  Konfigurace všech zavlažovacích zón. Pro každou zónu:
  - Název a ID
  - Výstupní pin (GPIO)
  - Typ chování (sekvenční/paralelní)
  - Režim výpočtu zavlažování a jeho parametry
  - Koeficienty pro citlivost na změnu počasí
  - Další informace v [`config_explained.md`](./config/config_explained.md)

- `zones_state.json`  
  Udržuje runtime stav jednotlivých zón:
  - Poslední zavlažování (čas, délka)
  - Aktuální aktivita

- `config_secrets.json`
  Používá se pouze ve vývojovém prostředí. Obsahuje přístupové údaje pro komunikaci se službami třetích stran. Standardně v .gitignore. V případě, že soubor neexistuje, systém soubor vytvoří, vyzve uživatele k vyplnění přístupových údajů a v daném běhu pokračuje s náhodně generovanými daty pro testování.
  - API klíč pro přístup k datům meteostanice
  - Aplikační klíč pro ověření v rámci služby meteostanice
  - MAC adresa konkrétní meteostanice, ze které jsou data získávána.

  > ⚠️ Tento soubor **není určen pro produkční použití**. V ostrém nasazení se citlivé údaje ukládají do systémových proměnných prostředí, které nejsou součástí souborového systému ani verzovacího systému.


- `irrigation_log.txt`  
  Běžný víceúrovňový log aktivit, chyb a hlášení pro ladění i dohled.

---

## Požadavky

- **Hardware**
  - Raspberry Pi Zero W (1 ks pro každý zavlažovací uzel)
  - Relé modul (pro spínání ventilů, 1 ks pro každý okruh v uzlu)
  - Napájení
  - Dosah WiFi sítě / Ethernetové připojení
  - Hardwarové I/O pro uzel (volitelně)
  - Raspberry Pi 4+ (centrální server)

- **Software**
  - Python 3.10+ (CPython) s podporou standardních knihoven
  - RPi.GPIO (volitelně, používá se na Raspberry Pi; fallback implementace je dostupná pro testování)
  - luma.core, luma.oled, pillow, requests, smbus2, cbor2

---

## Spuštění projektu

Projekt je v MVP fázi a probíhá jeho ladění pro provoz na cílovém hardware (Raspberry Pi).
Pro účely testování je možné ho spustit i mimo prostředí Raspberry Pi, kdy je knihovna pro GPIO nahrazena dummy implementací.
Před spuštěním je nutné mít dostupné všechny závislosti. Chystá se automatický Environment setup.

Spuštění systému je možné tímto příkazem v kořenovém adresáři projektu:

```bash
python3 -m smart_irrigation_system.main
```

---

## Poznámky

- Termíny **"okruh"** a **"zóna"** jsou v rámci tohoto projektu synonymní.

---


![Architektura stabilní verze zavlažovacího systému](./other/architecture.png)
