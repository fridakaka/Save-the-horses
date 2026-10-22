# Save the Horses – prototyp 0.2

Grå-boxad webbprototyp för att testa **hoppkänslan** och **sparning i hagar**. Ingen riktig konst, inga beroenden – en enda fil.

## Kör
- Öppna `docs/index.html` i en webbläsare, eller kör `python3 -m http.server` i mappen och öppna `localhost:8000`.
- På mobil: liggande läge. Lägg gärna sidan på hemskärmen/öppna via lokalt nätverk.
- Styrning: tryck/klicka var som helst eller mellanslag/pil upp = hoppa.

## Vad som finns
- Autogalopp genom en fast bana i 3 sektioner (≈ 100 s) med hage efter varje sektion.
- Hinder: **stup** (avgrund) och **stock**. Vilda hästar plockas upp när flocken passerar.
- Fem hästtyper: Ledare (brun), Löpare (sand, kort hopp), Hoppare (ljus, långt hopp), **Tålig** (mörk, klarar ett felsteg) och **Lugn** (blågrå, förlåter sena hopp).
- **Tålig:** faller inte första gången utan kämpar sig upp (röd binda syns). Läker i nästa hage. Nästa felsteg efter det är förlust.
- **Lugn:** utökar tidsmarginalen för sena hopp med 12 px per Lugn (högst två räknas) för hela flocken.
- **Stallscen:** i hagen zoomar kameran in på varje ny häst med namn, personlighetstext och förmåga. Hästar som tappats sedan förra hagen listas som "Vi minns: …".
- **Kaskadhopp:** ett tryck sätter en hoppunkt; varje häst hoppar när den når punkten. Sen tajming = hästarna längst fram faller först, de bakre hinner hoppa. För tidigt hopp = hästar med kort hopp (Löpare) faller.
- Flocken sparas automatiskt (localStorage) varje gång den når en hage. Förlorar du alla hästar börjar du om från senaste hagen med den flock du hade där. "Ny start" nollställer.

## Att testa (frågor till speltestarna)
1. Känns stuphoppet rättvist? Ser man *varför* hästar föll?
2. Vill man köra igen efter total förlust? Känns hage-omstarten schysst eller för snäll?
3. Gör hästtyperna att man bryr sig om flockens sammansättning?
4. Kantmarkeringen (guldlinjen) – hjälp eller fusk? Stäng av med `?cue=0`.

## Justera
Konstanter överst i skriptet (`CFG`, `TYPES`) och `buildLevel()`: fart, hopplängder, avgrundsbredd, förlåtande marginal (`coyote`), flocklängd.
