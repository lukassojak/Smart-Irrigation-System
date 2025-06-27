
# Smart Irrigation System (Minimum Viable Product)

### MVP
Tento projekt představuje **minimalistický prototyp chytrého zavlažovacího systému**, který využívá **Raspberry Pi Pico** k řízení jednotlivých zavlažovacích okruhů (zón).

### Stabilní verze
Systém MVP je navržen jako rozšiřitelný základ pro distribuovaný systém automatizovaného zavlažování s integrací s **Home Assistantem**, **Webovým UI** a centrálním serverem na **Raspberry Pi 4**.

---

## 🧠 Architektura systému

### MVP
- Jeden zavlažovací uzel **Raspberry Pi Pico** pracuje v **standalone režimu** a je zodpovědný za několik zavlažovacích zón.
- Data o konfiguraci a stavu jsou uložena v lokálních JSON souborech.
- **Simulované globální podmínky** (např. teplota, sluneční svit, vlhkost) se využívají k výpočtu potřebné závlahy.
- Ventily jsou řízeny pomocí **relé**.

### Stabilní verze
- Systém bude rozdělen do tří vrstev:  
  **1. Uživatelská vrstva (UI) - Webová aplikace, Home Assistant, CLI, případně kombinace**
  **2. Centrální řídicí server (Raspberry Pi 4)**  
  **3. Zavlažovací uzly (n Raspberry Pi Pico)**
- Podrobnosti architektury zde: ![Architektura stabilní verze zavlažovacího systému](./other/architecture.png)

#### 1. Centrální řídicí server (RPi 4):
- Zajišťuje **sběr dat ze serveru meteostanice** – intenzita slunečního svitu, teplota, srážky, vlhkost atd.
- Uchovává **konfiguraci všech zón** v jednom centrálním úložišti (ve formátu JSON / prostřednictvím databáze MySQL).
- Rozesílá aktualizace konfigurace a globální podmínky jednotlivým uzlům (protokol UART / MQTT).
- Hostuje **uživatelské rozhraní (webová aplikace, Home Assistant Dashboard)** pro správu systému.
- Poskytuje CLI rozhraní
- Provádí **analýzu a agregaci dat** (např. historie zavlažování, úspora vody, predikce podle počasí).
- Poskytuje data k **předpovědi počasí** prostřednictvím API.

#### 2. Zavlažovací uzly (RPi Pico):
- Obdrží a lokálně uloží aktuální konfiguraci a podmínky ze serveru.
- Stále fungují **autonomně** (fail-safe fallback): v případě výpadku komunikace pokračují v režimu podle posledně známé konfigurace.
- Vyhodnocují stav každé zóny a **lokálně spouští závlahu** podle instrukcí a případně podle **lokálních senzorů vlhkosti půdy**.
- Odesílají zpět na server **stavové zprávy, chyby a logy**.
- Jednotlivé uzly mohou mít různý počet zón a různé typy výstupů.

#### Komunikační rozhraní (plánováno):
- **MQTT** (preferované): robustní, škálovatelné, podporováno v Home Assistantu.
- Alternativy: **UART** (přímé spojení), **I2C**, **SPI**, nebo jednoduché TCP/IP přes Wi-Fi (s doplňkovým modulem).

#### Redundance a bezpečnost:
- Lokální konfigurace na uzlech slouží jako záloha při výpadku komunikace.
- Systém bude navržen jako "fail-safe" – při neznámém stavu nebo výpadku napájení nedojde k nekontrolovanému spuštění závlahy.

---

## 🔧🚀 Hlavní funkce 

### MVP
- **Řízení více zavlažovacích okruhů** – každý Pi Pico může řídit více výstupů (ventilů) s vlastní nezávislou logikou.
- **Sekvenční i souběžné (paralelní) zavlažování** – dle nastavení v konfiguraci. Při paralelním zavlažování je k dispozici funkce `max_flow_monitoring`, která sleduje aktuální potřebu průtoku vody a maximální dostupný průtok vody. Pokud by souběžné spuštění více okruhů překročilo limit, systém přepne do **hybridního režimu** a spouští některé zóny postupně, tak aby byl využit limit na maximum, ale nedošlo k přetížení.
- **Ruční spuštění** – možnost manuálně spustit všechny nebo vybrané okruhy.
- **Automatické denní zavlažování** – dle času a konfigurace.
- **Výpočet množství vody** – na základě záznamů ze serveru meteostanice (simulováno).
- **Konfigurace jednotlivých okruhů** - každý okruh může být zavlažován v jiné frekvenci, mít různou citlivost na jednotlivé projevy počasí, eviduje všechny zavlažovací emitory.
- **2 režimy výpočtu zavlažování**:
    - Rovnoměrný režim výpočtu: pokud je zavlažovaná plocha osazena zavlažovacími emitory rovnoměrně, je možné zadat požadovánou *bazální* (výchozí) hodnotu zavlažení jako výšku vodního sloupce v mm.
    - Nerovnoměrný režim výpočtu: pokud je zavlažovaná plocha osazena zavlažovacími emitory nerovnoměrně (např. velká rostlina emitor s celkovým průtokem 5L/h, malá rostlina 1L/h), požadovaná *bazální* hodnota zavlažení je zadána jako požadovaný objem vody vypuštěný *jedním zavlažovacím emitorem s nejmenším průtokem v konfiguraci* okruhu.
- **Možnost zapnout/vypnout automatický režim**.
- **Logování** – několik režimů logování činnosti a stavových hlášek do souboru.
- **Konfigurace pomocí JSON souborů** – připraveno na příjem z centrálního serveru a uživatelskou úpravu z webové aplikace / Home Assistantu.
- **Oddělený stav okruhů** – udržování aktuálního stavu (např. poslední zavlažování, aktivní stav) pro každý okruh.

---

## 📁 Struktura souborů a konfigurace

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
  - Požadované množství zalití pro bazální stav
  - Koeficienty pro citlivost na změnu počasí
  - Další informace v [`config_explained.md`](./config/config_explained.md)

- `zones_state.json`  
  Udržuje runtime stav jednotlivých zón:
  - Poslední zavlažování (čas, délka)
  - Aktuální aktivita
  - Stav senzoru (v budoucnu)

- `irrigation_log.txt`  
  Běžný log aktivit, chyb a hlášení pro ladění i dohled.

## 📜 Logování

Každé Raspberry Pi Pico zapisuje log do vlastního souboru `irrigation_log.txt`.

## 📅 Automatické zavlažování

Automatika může být zapnutá či vypnutá. V automatickém režimu systém zalévá každý den v nastavený čas.

## 🔌 Požadavky

- **Hardware**
  - Raspberry Pi Pico (1 ks pro každý zavlažovací uzel)
  - Relé modul (pro spínání ventilů)
  - Napájení
  - Dosah WiFi sítě (v budoucnu)

- **Software**
  - Python 3 (Micropython)
  - Používané knihovny: `json`, `time`, `threading`, `os`

---

## 🛠️ Možnosti řízení

### Ruční režim:
- Spuštění všech okruhů ručně
- Spuštění konkrétní zóny dle ID/názvu ručně
- Vypnutí všech zón

### Automatický režim:
- Spouští zavlažování ve zvolený čas pro ty zóny, které daný den mají zavlažovat
- Konfigurace automatického režimu podle [`config_explained.md`](./config/config_explained.md)
- Pozastavení všech zón pro následující cyklus
- Pozastavení konkrétní zóny pro následující cyklus

---

## 📈 Plánované rozšíření

- [ ] Lokální senzory vlhkosti půdy v zóně
- [ ] Webové rozhraní pro správu a monitoring
- [ ] Přímá synchronizace konfigurace se serverem (Raspberry Pi 4)
- [ ] Integrace s **Home Assistantem**
- [ ] MQTT komunikace mezi uzly

---

## 🗒️ Poznámky

- Termíny **"okruh"** a **"zóna"** jsou v rámci tohoto projektu synonymní.
---