---
layout: literature
title: Bilaga: Tokenjämförelse mellan Hermes och vår egen QA agent service
permalink: /token-jamforelse-hermes-vs-qa-agent-service-sv/
---

# Bilaga: Tokenjämförelse mellan Hermes och vår egen QA agent service

## Syfte

Denna bilaga sammanfattar de sex jämförelsekörningar där:

- Hermes kördes med en starkare modellmiljö, i den insamlade datan `gpt-5.5`
- vår egen lösning kördes via `ai_agents` med `qa-agent-service` som agentbackend
- tokenförbrukningen för vår egen lösning hämtades från exporterade JSON-filer per scenario

Bilagan ska läsas tillsammans med [Hermes-rapport scenario 1-6](../hermes-report-scenarios-1-6/), som lämnas oförändrad och fungerar som källfil för Hermes-delen av jämförelsen.

## Datagrund och avgränsning

För Hermes används de mätbara siffror som redan sammanställts i [Hermes-rapport scenario 1-6](../hermes-report-scenarios-1-6/):

- `Input tokens`
- `Output tokens`
- `Reasoning tokens`
- `Cache read`
- `API calls`
- `Tool calls`

För vår egen lösning används de tokenfält som nu finns i JSON-exporterna från `ai_agents`:

- `prompt_tokens`
- `completion_tokens`
- `total_tokens`

Detta innebär att jämförelsen inte är helt symmetrisk. Hermes-tabellen beskriver session- och orkestreringsnära användning i Hermes-spåret, medan vår egen tabell beskriver modelltoken som förbrukades i `qa-agent-service`-anropen. Hermes cache-läsningar, reasoning-token och övrig intern overhead har därför ingen direkt motsvarighet i vår egen export. Trots detta är jämförelsen värdefull eftersom den visar storleksordning, iterationsmönster och vilka delar av vårt eget flöde som driver tokenkostnaden.

## Scenarioöversikt

Alla sex körningar med vår egen lösning följde samma praktiska mönster:

- `max_rounds = 10`
- `max_feedback_messages = 12`
- `max_feedback_per_agent_pair = 4`
- faktisk `iterations = 5`
- faktisk `total_feedback_messages = 4`
- faktisk feedbackriktning: `Review Agent -> Test Design Agent`

Det innebär att samtliga körningar stoppade efter fyra backtracking-omgångar mellan Review Agent och Test Design Agent, trots att den globala round-gränsen låg högre.

## Tabell 1: Hermes och vår egen lösning per scenario

| Scenario | Hermes model | Hermes input + output | Vår total tokens | Kvot vår/Hermes I/O | Skillnad vår - Hermes I/O |
|---|---|---:|---:|---:|---:|
| 1. Login and registration | gpt-5.5 | 123322 | 71362 | 0.579 | -51960 |
| 2. E-commerce checkout | gpt-5.5 | 125096 | 71430 | 0.571 | -53666 |
| 3. Password reset | gpt-5.5 | 65438 | 53451 | 0.817 | -11987 |
| 4. Support tickets | gpt-5.5 | 75112 | 66534 | 0.886 | -8578 |
| 5. Inventory management | gpt-5.5 | 139965 | 64305 | 0.459 | -75660 |
| 6. Course enrollment | gpt-5.5 | 122342 | 61162 | 0.500 | -61180 |
| **Total** | mixed | **651275** | **388244** | **0.596** | **-263031** |

### Tolkning

- Vår egen lösning låg i dessa körningar under Hermes mätbara input+output-token för samtliga sex scenarier.
- Skillnaden ska inte tolkas som att vår lösning därför är "billigare i alla avseenden", eftersom Hermes också redovisade reasoning-token och mycket stora cache-läsningar som saknar direkt motsvarighet i vår egen export.
- Däremot går det att säga att våra `qa-agent-service`-anrop i denna konfiguration låg på ungefär 46 till 89 procent av Hermes uppmätta input+output-token beroende på scenario.

## Tabell 2: Vår egen lösning per scenario

| Scenario | Run ID | Prompt tokens | Completion tokens | Total tokens | Tokenförande anrop | Iterationer | Feedbackomgångar |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1. Login and registration | 1 | 59211 | 12151 | 71362 | 11 | 5 | 4 |
| 2. E-commerce checkout | 2 | 59170 | 12260 | 71430 | 11 | 5 | 4 |
| 3. Password reset | 3 | 47185 | 6266 | 53451 | 11 | 5 | 4 |
| 4. Support tickets | 4 | 55585 | 10949 | 66534 | 11 | 5 | 4 |
| 5. Inventory management | 5 | 54502 | 9803 | 64305 | 11 | 5 | 4 |
| 6. Course enrollment | 6 | 51759 | 9403 | 61162 | 11 | 5 | 4 |

### Tolkning

- Körmönstret var praktiskt identiskt i alla sex scenarier.
- Alla körningar nådde samma antal iterationer och samma antal feedbackomgångar.
- Tokenkostnaden varierade alltså främst med scenariots innehåll och artefakternas storlek, inte med olika kontrollinställningar.

## Tabell 3: Grundrunda och extra cykler i vår egen lösning

`Grundrunda` avser den första kompletta omgången:

- Requirements Analyst
- första passet i Test Design Agent
- första passet i Review Agent

`Extra cykler` avser de fyra efterföljande looparna mellan Test Design Agent och Review Agent.

| Scenario | Grundrunda tokens | Extra cykler totalt | Genomsnitt per extra cykel |
|---|---:|---:|---:|
| 1. Login and registration | 13127 | 58235 | 14558.75 |
| 2. E-commerce checkout | 13539 | 57891 | 14472.75 |
| 3. Password reset | 10505 | 42946 | 10736.50 |
| 4. Support tickets | 12648 | 53886 | 13471.50 |
| 5. Inventory management | 12199 | 52106 | 13026.50 |
| 6. Course enrollment | 11773 | 49389 | 12347.25 |

### Tolkning

- Den första kompletta omgången kostade ungefär 10.5k till 13.5k tokens beroende på scenario.
- De fyra extra cyklerna kostade tillsammans ungefär 43k till 58k tokens.
- En extra cykel kostade i genomsnitt ungefär 10.7k till 14.6k tokens.
- I praktiken är det alltså backtracking-loopen mellan Test Design Agent och Review Agent som står för merparten av kostnadsökningen.

## Tabell 4: Vilka steg som kostar mest i vår egen lösning

Summerat över scenario 1 till 6:

| Del av flödet | Tokens | Andel av totalen |
|---|---:|---:|
| Requirements Analyst | 11461 | 3.0% |
| Test Design Agent | 178868 | 46.1% |
| Review Agent | 197915 | 51.0% |
| **Totalt** | **388244** | **100%** |

### Tolkning

- Requirements Analyst är relativt billig och stabil mellan scenarierna.
- Nästan hela tokenkostnaden ligger i Test Design Agent och Review Agent.
- Review Agent är genomgående den enskilt dyraste delen av flödet.

## Tabell 5: Växande kostnad inom samma scenario

| Scenario | Test Design första -> sista | Review första -> sista |
|---|---|---|
| 1 | 4531 -> 7423 | 6714 -> 7879 |
| 2 | 4940 -> 7390 | 6693 -> 7827 |
| 3 | 3817 -> 5616 | 4715 -> 5891 |
| 4 | 4562 -> 6889 | 6192 -> 7369 |
| 5 | 4412 -> 6717 | 5878 -> 6955 |
| 6 | 4228 -> 6332 | 5648 -> 6742 |

### Tolkning

- Både Test Design Agent och Review Agent blir dyrare för varje ytterligare cykel.
- Detta talar för att mer kontext, fler artefakter och fler tidigare feedbackpunkter skickas in i senare promptar.
- Mönstret passar bättre med hypotesen "växande kontextmassa" än med hypotesen "lös agentchatt" som dominerande kostnadsorsak.

## Vad som sannolikt kostar token i vår lösning

Utifrån de sex körningarna går det att dra följande slutsatser:

1. Orchestratorn verkar inte vara den stora tokenkostnaden.
   Orchestrator-stegen i exporterade `stage_traces` saknar tokenvärden i dessa körningar och fungerar här främst som routing- och stopplogik.

2. Den stora kostnaden ligger i upprepade modelkall i Test Design Agent och Review Agent.
   Varje extra cykel innebär att dessa agenter anropas igen, ofta med ett större underlag än i föregående omgång.

3. Den första requirementsanalysen är inte huvudproblemet.
   Requirements Analyst står bara för cirka 3 procent av total tokenförbrukning i det insamlade materialet.

4. Växande kontext verkar vara en starkare förklaring än "brusig agentdialog".
   Det är sannolikt inte fri chatt i sig som kostar mest, utan att krav, testdesign, reviewfynd och tidigare iterationer återförs in i nya promptar. Varje ny omgång blir därför lite tyngre än den föregående.

5. Feedbackformatet är sannolikt en nyckelpunkt för optimering.
   Eftersom all faktisk feedback i dessa körningar gick från Review Agent till Test Design Agent är det just denna länk som bör undersökas först om tokenkostnaden ska minska.

## Vad mer det insamlade datat gör möjligt att analysera

Det nuvarande datat gör det redan möjligt att gå vidare med flera typer av analys:

- jämföra tokenkostnad per scenario mot scenario-komplexitet
- mäta hur mycket varje extra cykel kostar i absoluta tal
- analysera vilka agentroller som driver kostnaden mest
- bedöma om stoppgränserna används som skydd mot loopar eller om de oftare nås som "normalläge"
- jämföra totalkostnad mot slutkvalitet, till exempel Hermes total score kontra vår egen tokensumma
- jämföra hur mycket observerbarhet man får i vår egen lösning i relation till dess tokenkostnad

Det som däremot ännu inte går att avgöra exakt från nuvarande export är:

- exakt hur stor del av prompten som består av kravtext, tidigare testdesign, feedback respektive övrig bakgrundsdata
- exakt hur stor del som är "brus" jämfört med nödvändig arbetskontext

För att komma längre i just den frågan skulle nästa steg vara att logga promptstorlek per delkomponent, exempelvis:

- scenario-text
- shared memory
- agent private memory
- tidigare testdesign
- review feedback
- system-/agentdirektiv

## Samlad slutsats

Det mest intressanta resultatet från dessa sex körningar är att tokenförbrukningen i vår egen lösning inte främst verkar drivas av orkestratorn eller av någon allmän agentchatt. Den drivs i stället av iterativ återläsning och ombearbetning i loopen mellan Test Design Agent och Review Agent. Detta är också förenligt med litteraturens varning för att fleragenta system snabbt blir dyra när samma eller växande kontext skickas vidare mellan agenter flera gånger.

Det innebär att den viktigaste optimeringsfrågan framåt inte bara är modellval, utan kontextdisciplin:

- hur mycket data skickas vidare mellan stegen
- hur ofta skickas den vidare
- och hur mycket av det materialet är faktiskt nödvändigt i nästa omgång

I praktiken pekar detta mot att nästa förbättringssteg bör ligga i bättre komprimering, selektiv vidarebefordran av feedback och tydligare avgränsning av vad Test Design Agent respektive Review Agent verkligen behöver se i varje ny iteration.
