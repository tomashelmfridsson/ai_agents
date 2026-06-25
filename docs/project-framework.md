# Projektframework

## Forskningsfråga

Hur kan ett agentiskt QA-system med orkestrator och specialiserade agenter stödja kravbaserad testdesign och testgenerering, samt vilka agentramverk och arkitekturer är mest lämpade för detta ändamål?

## Delmål

1. Kartlägga relevanta agentramverk och jämföra deras lämplighet för QA-arbetsflöden.
2. Implementera en demonstrator som transformerar krav till testartefakter.
3. Utvärdera demonstratorn med tydliga kvalitets- och effektivitetsmått.

## Avgränsning

- Fokus ligger på QA-automation och agentorkestrering, inte på generell kodgenerering.
- Demonstratorn prioriterar spårbarhet från krav till testartefakt framför djup exekveringsintegration.
- Initial implementation är modellagnostisk och kan senare kopplas till Ollama eller molntjänster.

## Målarkitektur

### Arbetsflöde

```text
Krav
  -> Orkestrator
  -> Kravanalys
  -> Testdesign
  -> Testgenerering
  -> Granskning
  -> Godkända testartefakter
```

### Agentansvar

`OrchestratorAgent`

- styr sekvensen mellan agentsteg
- hanterar iterationer
- samlar slutresultatet

`RequirementsAnalystAgent`

- bryter ner kravtext
- identifierar aktörer, handlingar, villkor och acceptanskriterier
- producerar strukturerad JSON

`TestDesignAgent`

- väljer testtyp per krav
- definierar teststeg och orakel
- markerar risker och antaganden

`TestGenerationAgent`

- genererar konkreta testfall
- producerar testdatautkast
- skapar kandidater för GUI- och logiktest

`ReviewAgent`

- granskar täckning, tydlighet och spårbarhet
- avgör om ny iteration krävs
- producerar förbättringsförslag

## Föreslagna utvärderingsmått

| Mått | Definition | Hur det kan mätas |
|---|---|---|
| Kravtäckning | Andel krav med minst ett testfall | Matchning mellan krav-ID och genererade tester |
| Test Pass Rate | Andel passerande tester | Körning i CI eller lokal testrunner |
| Exekveringstid | Tid för pipeline eller agentsteg | Tidsmätning per steg och total pipeline |
| Iterationscykler | Antal review-loopar före godkännande | Loggas av orkestratorn |
| Kodtäckning | Täckning om kod/tester körs mot app | Coverage-verktyg |
| Kodkvalitet | Kvalitetsmått på genererade tester | Exempelvis SonarQube eller lint-regler |

## Hot mot validitet

- Små demonstrationsfall riskerar att överskatta systemets generaliserbarhet.
- Regelbaserad eller enkel heuristik i prototypen representerar inte full LLM-kapacitet.
- Jämförelser mellan ramverk kan bli missvisande om kriterierna inte definieras konsekvent.
