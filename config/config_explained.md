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

Např.:
Když je min_percent = 20, i kdyby pršelo celý den, bude se zavlažovat 20% běžné doby.

### automation:
- `enabled`: Povolí/zakáže automatické zavlažování v nastavený čas.
- `scheduled_hour`, `scheduled_minute`: Denní čas, kdy má systém spustit zavlažování (např. 20:00).

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
- `enabled`: Příznak, zda je okruh aktivní. Pokud je `false`, okruh se přeskakuje, ale zůstává v konfiguraci.
- `standard_flow_seconds`: Počet sekund, jak dlouho má být ventil otevřen při **100% výpočtu výtoku** (bazálním stavu, např. 60 sekund). Např. pokud výsledný výpočet ukáže 150%, takový ventil se pak otevře na 90 sekund (1.5 * 60)¨
- `interval_days`: Počet dní mezi jednotlivými cykly zavlažování daného okruhu. Např. 1 = každý den, 2 = každý druhý den. Při každém denním spuštění v daný čas systém zkontroluje, zda od posledního zavlažení dané zóny uplynulo dost dní. Stav posledního zalití každé zóny bude potřeba uchovávat – např. v paměti nebo ve zvláštním datovém souboru.
- `drippers`: Seznam kapkovačů s jejich spotřebou (v l/h).

### local_correction_factors:
Modifikace chování daného okruhu oproti globálním korekcím.

- `sunlight`: Např. pokud je v trvalém stínu, může být záporný – méně vody navzdory globálnímu slunci.
- `rain`: Některé části mohou být více vystavené srážkám (např. otevřený trávník) → vyšší negativní korekce.
- `temperature`: Např. terasa na betonu se silněji zahřívá, takže má smysl zvýšit vliv teploty.

Tyto hodnoty doplňují globální koeficienty – nejsou náhradou. Pokud např. globální hodnota pro `rain` je -0.5 a lokální je -0.8, pak celková citlivost na déšť bude -1.3.
