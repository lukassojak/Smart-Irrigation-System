# Konfigurace zavlažovacího systému

Tento dokument popisuje strukturu a význam polí v konfiguračních souborech:

- [`config_global.json`](./config_global.json)
- [`zones_config.json`](./zones_config.json)

---

## 🔧 `config_global.json`

Tento soubor obsahuje globální konfiguraci, která ovlivňují všechny okruhy (celý zavlažovací uzel).

### standard_conditions:
Referenční hodnoty počasí, při kterých je zavlažování považováno za ideální (očekávané) a používá se 100% očekávaného výtoku - bazální stav.

- `sunlight_hours`: Celkový počet hodin slunečního svitu za posledních 24 hodin (od posledního zavlažování)
- `ŗain_mm`: Celkový úhrn srážek za posledních 24 hodin (od posledního zavlažování)
- `temperature_celsius`: Průměrná teplota za posledních 24 hodin (od posledního zavlažování)

Tyto hodnoty slouží jako výchozí bod pro výpočty – aktuální podmínky se porovnávají s těmito a výsledný rozdíl se násobí koeficienty.

### correction_factors:
Koeficienty, které určují, jak moc ovlivní odchylka od ideálních podmínek výsledné množství vody.

- `sunlight`: Kolik procent se přidá/ubere za každou hodinu slunečního svitu navíc/méně.
- `rain`: Kolik procent se ubere/přidá za každý mm srážek navíc/méně.
- `temperature`: Kolik procent se přidá/ubere za každý stupeň Celsia navíc/méně.

Např.:
Když je o 2 mm více srážek než standardní, výpočet výtoku bude snížen o 2 × (-0.1) = -20 %.

### irrigation_limits:
- `min_percent`: Dolní hranice výpočtu (např. 0 = žádné zavlažování).
- `max_percent`: Horní hranice (např. 500 = maximálně 5× běžné doby).
- `main_valve_max_flow`: Maximální odběr v l/h pro celý zavlažovací uzel.

Např.:
Když je min_percent = 20, i kdyby pršelo celý den, bude se zavlažovat 20% běžného objemu.

### automation:
- `enabled`: Povolí/zakáže automatické zavlažování v nastavený čas.
- `scheduled_hour`, `scheduled_minute`: Denní čas, kdy má systém spustit zavlažování (např. 20:00).
- `irrigation_mode`: může být:
    - `sequential`: zavlažování probíhá sekvenčně - v daný okamžik je aktivní pouze jeden zavlažovací okruh v rámci celého zavlažovacího uzlu.
    - `concurrent`: zavlažování probíhá souběžně – všechny okruhy v rámci zavlažovacího uzlu se spustí najednou. Pokud je `max_flow_monitoring` nastaveno na `false` a spotřeba vody překročí dostupný přítok, může dojít k nepřesnému zavlažení (např. některé okruhy dostanou méně vody, než bylo plánováno).
- `max_flow_monitoring`: Pokud je `true`, IrrigationController během spuštěného zavlažování kontroluje aktuální odběr všech zavlažovacích okruhů. Pokud by při **souběžném zavlažování** mělo spuštění zavlažování dalšího okruhu navýšit odběr nad `main_valve_max_flow`, počká tento okruh, než doběhne zavlažování jiných, a až poté se spustí. V případě omezeného `main_valve_max_flow` je tento režim bezpečnou variantou pro souběžné zavlažování, zároveň ale **negarantuje 100% souběžné zavlažování**. Pokud je `irrigation_mode` nastaveno na `sequential`, pak nemá žádný vliv.
- `server_offline`: **Nedostupné v MVP** V případě, že nejsou dostupné záznamy o počasí, nebo je server (centrální Raspberry Pi 4) offline:
    - `disabled`: Zavlažování se pozastaví do té doby, než bude server dostupný
    - `history_based`: Zavlažování pokračuje v nastavený čas podle konfigurace, nedostupná data o počasí pro výpočet objemu zavlažení jsou nahrazena průměrem zavlažení z posledních 3 dnů pro každý okruh.
    - `base_volume`: Zavlažování pokračuje v nastavený čas podle konfigurace. Zavlaží se vždy 100% bazálního množství.
    - `half_base_volume`: Zavlažování pokračuje v nastavený čas podle konfigurace. Zavlaží se vždy 50% bazálního množství.

### logging:
Ovládá chování výstupu logování na klientském zařízení.

- `enabled`: Zapne/vypne logování
- `log_level`: Úroveň výstupu (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

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
- `drippers_summary`: Slovník, kde klíče jsou průtoky kapkovačů v litrech za minutu (jako řetězce) a hodnoty jsou počty těchto kapkovačů v daném okruhu.


**DŮLEŽITÉ: Všechny hodnoty průtoků kapkovačů (drippers_summary - klíče) musí být celá čísla (integer). Desetinná čísla nebo jiné formáty nejsou podporovány a povedou k chybě při načítání konfigurace.**


### local_correction_factors:
Modifikace chování daného okruhu oproti globálním korekcím.

- `sunlight`: Např. pokud je v trvalém stínu, může být záporný – méně vody navzdory globálnímu slunci.
- `rain`: Některé části mohou být více vystavené srážkám (např. otevřený trávník) → vyšší negativní korekce.
- `temperature`: Např. terasa na betonu se silněji zahřívá, takže má smysl zvýšit vliv teploty.

Tyto hodnoty doplňují globální koeficienty – nejsou náhradou. Pokud např. globální hodnota pro `rain` je -0.5 a lokální je -0.8, pak celková citlivost na déšť bude -1.3.
