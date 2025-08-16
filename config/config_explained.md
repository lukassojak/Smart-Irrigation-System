# Konfigurace zavlažovacího systému

Tento dokument popisuje strukturu a význam polí v konfiguračních souborech:

- [`config_global.json`](./config_global.json)
- [`zones_config.json`](./zones_config.json)
- [`config_secrets.json`](./config_secrets.json)

---

## 🔧 `config_global.json`

Tento soubor obsahuje globální konfiguraci, která ovlivňují všechny okruhy (celý zavlažovací uzel).

### standard_conditions:
Referenční hodnoty počasí, při kterých je zavlažování považováno za ideální (očekávané) a používá se 100% očekávaného výtoku - bazální stav.

- `solar_total`: Celková energie slunečního záření za 24 hodin v kWh/m².
- `ŗain_mm`: Celkový úhrn srážek za 24 hodin v mm.
- `temperature_celsius`: Průměrná teplota od posledního zavlažování.

Tyto hodnoty slouží jako výchozí bod pro výpočty – aktuální podmínky se porovnávají s těmito a výsledný rozdíl se násobí koeficienty.

### correction_factors:
Koeficienty, které určují, jak moc ovlivní odchylka od ideálních podmínek výsledné množství vody.
Pro **přímou úměru** (více, než referenční hodnota v `standard_conditions` = více zalévání) se koeficienty zapisují kladné.
Pro **nepřímou úměru** (více, než referenční hodnota = méně zalévání) se koeficienty zapisují záporné.

- `solar`: Kolik procent se přidá za každou kWh/m² slunečního záření navíc/méně.
- `rain`: Kolik procent se přidá za každý mm srážek navíc/méně.
- `temperature`: Kolik procent se přidá za každý stupeň Celsia navíc.

Např.:
`rain` je nastaveno na -0.2. Za každý mm srážek se ubere 20% výtoku okruhu.
Když je o 2 mm více srážek než standardní, výpočet výtoku bude upraven o 2 × (-0.2) = -0.2 (-20 %).

### irrigation_limits:
- `min_percent`: Dolní hranice výpočtu (např. 0 = žádné zavlažování).
- `max_percent`: Horní hranice (např. 500 = maximálně 5× běžné doby).
- `main_valve_max_flow`: Maximální odběr v l/h pro celý zavlažovací uzel.

Např.:
Když je min_percent = 20, i kdyby pršelo celý den, bude se zavlažovat 20% běžného objemu.

### automation:
- `enabled`: Povolí/zakáže automatické zavlažování v nastavený čas.
- `scheduled_hour`, `scheduled_minute`: Denní čas, kdy má systém spustit zavlažování (např. 20:00).
- `irrigation_mode`: **Nedostupné v MVP** může být:
    - `sequential`: zavlažování probíhá sekvenčně - v daný okamžik je aktivní pouze jeden zavlažovací okruh v rámci celého zavlažovacího uzlu.
    - `concurrent`: zavlažování probíhá souběžně – všechny okruhy v rámci zavlažovacího uzlu se spustí najednou. Pokud je `max_flow_monitoring` nastaveno na `false` a spotřeba vody překročí dostupný přítok, může dojít k nepřesnému zavlažení (např. některé okruhy dostanou méně vody, než bylo plánováno).
- `max_flow_monitoring`: Pokud je `true`, IrrigationController během spuštěného zavlažování kontroluje aktuální odběr všech zavlažovacích okruhů. Pokud by při **souběžném zavlažování** mělo spuštění zavlažování dalšího okruhu navýšit odběr nad `main_valve_max_flow`, počká tento okruh, než doběhne zavlažování jiných, a až poté se spustí. V případě omezeného `main_valve_max_flow` je tento režim bezpečnou variantou pro souběžné zavlažování, zároveň ale **negarantuje 100% souběžné zavlažování**. Při **sekvenčním zavlažování** nepovolí zavlažení okruhů, které mají vypočítaný větší odběr, než je `main_valve_max_flow`.
- `sequential`: Boolean příznak, který, pokud je `true`, deaktivuje souběžné zavlažování a aktivuje zavlažování sekvenční (vždy zalévá jen jeden okruh). Okruhy jsou zalévány v pořadí podle jejich ID vzestupně.
- `server_offline_fallback`: **Nedostupné v MVP** V případě, že nejsou dostupné záznamy o počasí, nebo je server (centrální Raspberry Pi 4) offline:
    - `disabled`: Zavlažování se pozastaví do té doby, než bude server dostupný
    - `history_based`: Zavlažování pokračuje v nastavený čas podle konfigurace, nedostupná data o počasí pro výpočet objemu zavlažení jsou nahrazena průměrem zavlažení z posledních 3 dnů pro každý okruh.
    - `base_volume`: Zavlažování pokračuje v nastavený čas podle konfigurace. Zavlaží se vždy 100% bazálního množství.
    - `half_base_volume`: Zavlažování pokračuje v nastavený čas podle konfigurace. Zavlaží se vždy 50% bazálního množství.
- `environment`: Tato položka určuje **běhové prostředí systému**. Na základě hodnoty mohou různé části aplikace měnit své chování – např. používat simulovaná data, odlišné API adresy, deaktivovat reálné GPIO výstupy apod.
    - `development`: Vývojové prostředí. Povolen je simulovaný režim, rozšířené logování, debug výstupy.

### logging:
Ovládá chování výstupu logování na klientském zařízení.

- `enabled`: Zapne/vypne logování
- `log_level`: Úroveň výstupu (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)

### weather_api:
Konfigurace URL adres pro přístup k datům meteostanice a předpovědi počasí.

- `realtime_url`: URL pro aktuální data meteostanice
- `history_url`: URL pro historická data meteostanice

> Pro funkčnost systému přizpůsobení zálivky vzhledem k počasí od posledního zalévání je nutné vyplnit v konfiguraci současně obě hodnoty: `realtime_url` i `history_url`. Pokud jedna z hodnot chybí nebo není dostupná, dojde k fallbacku na bazální režim zavlažování (bez ohledu na počasí). V připadě aktivního testovacího režimu dojde k fallbacku na náhodný generátor počasí pro simulaci podmínek.

---

## 🗺️ `zones_config.json`

Tento soubor obsahuje seznam všech zavlažovacích okruhů a jejich specifických vlastností. Každý okruh je odlišně ovlivňován počasím a jeho jednotlivými projevy (slunce, srážky).

- `id`: Jedinečné identifikační číslo každého okruhu. Může být využito pro řazení (sekvenční zavlažování od nejnižšího id), identifikaci v datech, komunikaci s klientskými zařízeními.
- `name`: Lidsky čitelný název okruhu, např. pro zobrazení v Home Assistantu.
- `relay_pin`: Číslo GPIO pinu, který ovládá relé pro ventil.
- `enabled`: Boolean příznak, zda je okruh aktivní. Pokud je `false`, okruh se přeskakuje, ale zůstává v konfiguraci.
- `even_area_mode`: Boolean příznak, který určuje režim výpočtu zavlažování:
    - `true`: Okruh je na ploše rovnoměrně osazen zavlažovacími emitory. Plocha se zavlažuje podle hodnot `target_mm` a `zone_area_m2`. Je možné regulovat zálivku podle mm vodního sloupce na zadanou plochu. V tomto režimu je hodnota `liters_per_minimum_dripper` nastavena na `null`.
    - `false`: Obecnější režim pro plochy, které nejsou rovnoměrně osazeny zavlažovacími emitory a není tak možné pracovat s výškou vodního sloupce na ploše. V tomto režimu se používá uživatelská hodnota atributu `liters_per_minimum_dripper`. Vhodné pro nerovnoměrné okruhy zavlažování, např. několik rostlin různých rozměrů. V takové situaci mají zavlažovací emitory takový průtok l/h v poměru požadavků rostlin v okruhu. Tento režim je spolehlivý a intuitivní při použití pouze zavlažovacích emitorů typu kapkovač (dripper).
- `target_mm`: Cílové množství vody (vodní sloupec) v milimetrech pro zavlažování. Pokud je `even_area_mode` `false`, hodnota je `null`.
- `zone_area_m2`: Velikost zavlažované plochy v m². Pokud je `even_area_mode` `false`, hodnota je `null`.
- `liters_per_minimum_dripper`: Množství vody, které je při bazálním stavu (při výpočtu 100% výtoku pro daný okruh podle nastavených globálních standardních podmínek) **vypuštěno z jednoho minimálního kapkovače (kapkovač s nejmenším průtokem v konfiguraci)**. Pokud je `even_area_mode` `true`, hodnota je `null`.
- `interval_days`: Počet dní mezi jednotlivými cykly zavlažování daného okruhu. Např. 1 = každý den, 2 = každý druhý den. Při každém denním spuštění v daný čas systém zkontroluje, zda od posledního zavlažení dané zóny uplynulo dost dní. Stav posledního zalití a jiné stavové hodnoty jsou uchovávány při běhu v paměti a ve stavovém souboru [`zones_state.json`](./../data/zones_state.json).
- `drippers_summary`: Slovník, kde klíče jsou průtoky kapkovačů v **litrech za hodinu** (jako řetězce, např. "2", "8", "12", "15", ..) a hodnoty jsou počty těchto kapkovačů v daném okruhu.


> ⚠️ Všechny hodnoty průtoků kapkovačů (drippers_summary - klíče) musí být celá čísla (integer). Desetinná čísla nebo jiné formáty nejsou podporovány a povedou k chybě při načítání a validaci konfigurace.**


### local_correction_factors:
Modifikace chování daného okruhu vůči globálním korekcím. Jedná se o lineární model, který umožňuje přizpůsobit vliv počasí na konkrétní okruh. Tyto hodnoty se sčítají s globálními koeficienty z [`config_global.json`](./config_global.json).

- `solar`: Lokální koeficient pro sluneční záření. Např. terasa na betonu se silněji zahřívá, takže má smysl zvýšit vliv slunečního záření.
- `rain`: Některé části mohou být více vystavené srážkám (např. otevřený trávník) → vyšší negativní korekce.
- `temperature`: Např. terasa na betonu se silněji zahřívá, takže má smysl zvýšit vliv teploty.


---

## 🔑 `config_secrets.json`

Soubor [config_secrets.json](./config_secrets.json) obsahuje citlivé přístupové údaje (např. API klíče) potřebné pro komunikaci se službami třetích stran, jako je například Ecowitt weather server.

- `api_key`: API klíč pro přístup k datům serveru meteostanice
- `application_key`: Aplikační klíč pro ověření v rámci služby meteostanice
- `device_mac`: MAC adresa konkrétní meteostanice, ze které jsou data získávána

```json
{
    "api_key": "your_api_key_here",
    "application_key": "your_application_key_here",
    "device_mac": "your_weather_station_mac_address_here"
}
```

> ⚠️ Tento soubor **není určen pro produkční použití**. V ostrém nasazení se citlivé údaje ukládají do systémových proměnných prostředí, které nejsou součástí souborového systému ani verzovacího systému.