# Projektbrief för forskningsstudien

## Studiens teman

- AI-agenter
- Multi-Agent Systems
- Agentic Software Engineering
- Agentorkestrering
- AI-assisterad kvalitetssäkring
- Verifiering och validering
- Test-Driven Development

## Analysfrågor att besvara under studien

### AI-agenter

- Hur definieras en agent i aktuell litteratur?
- Vilka egenskaper återkommer: autonomi, planering, verktygsanvändning, minne och reflektion?
- Hur skiljer sig enkla agentloopar från orkestrerade multi-agentmiljöer?

### Multi-Agent Systems

- Vilka samarbetsmönster används: hierarki, marknadsbaserad delegation, blackboard, reviewer-loop?
- Hur hanteras konflikter, koordinering och delat tillstånd?
- Vilka risker finns kring felpropagering mellan agenter?

### Agentic Software Engineering

- Vilka delar av utvecklingslivscykeln stöds bäst av agenter?
- Hur mäts kvalitet, spårbarhet och produktivitet?
- Vilka arkitekturval underlättar styrbarhet och granskningsbarhet?

### AI-assisterad kvalitetssäkring

- Hur används AI för kravanalys, testdesign och testgenerering?
- Finns empiriskt stöd för förbättrad kravtäckning eller minskad ledtid?
- Hur hanteras testorakel, testdata och selektorer?

### Verifiering och validering

- Hur knyts V&V till agentiska arbetsflöden?
- Vilka granskningsmekanismer krävs för att begränsa hallucineringar och svag spårbarhet?

### TDD

- Hur relaterar testdriven utveckling till kravdriven testgenerering?
- Kan agentiska arbetssätt stödja en TDD-liknande återkopplingsloop?

## Jämförelseramverk för plattformar

Bedöm varje plattform utifrån följande kriterier:

| Kriterium | Fråga |
|---|---|
| Orkestrering | Hur uttrycks flöden, iterationer och routing? |
| Rollspecialisering | Hur enkelt är det att modellera flera agentroller? |
| Tillståndshantering | Hur lagras mellanresultat, minne och spårbarhet? |
| Verktygsintegration | Hur väl stöds externa verktyg, RAG och testkörning? |
| Observerbarhet | Finns loggning, tracing och debug-stöd? |
| Lokalt modellstöd | Hur lätt kopplas Ollama eller lokal inferens in? |
| Molnstöd | Hur väl stöds kommersiella modell-API:er? |
| QA-lämplighet | Hur väl passar plattformen kravanalys och testdesign? |

## Möjliga plattformar att jämföra

| Plattform | Kort beskrivning |
|---|---|
| OpenClaw | Experimentell plattform för agentautomation med fokus på snabb prototypframtagning och flexibla agentflöden. |
| Hermes Agent Framework | Ramverk för att strukturera agentroller, ansvar och samspel i mer kontrollerade agentbaserade system. |
| CrewAI | Rollbaserat multi-agentramverk där flera specialiserade agenter samarbetar i definierade arbetsflöden. |
| LangGraph | Grafbaserat orkestreringsramverk för att bygga agentflöden med tydliga tillstånd, övergångar och återkopplingsloopar. |
| AutoGen | Ramverk för konversationsdrivna multi-agentsystem med starkt stöd för samarbete mellan agenter och verktyg. |
| OpenAI Agents SDK | SDK för att bygga AI-agenter med nära integration till modeller, verktyg, guardrails och körbar orkestrering. |

## Lokal vs molnbaserad modellkörning

### Ollama / lokala modeller

Analysera:

- dataskydd och lokal kontroll
- latens och driftskostnad
- modellkapacitet för längre kedjor av resonemang
- begränsningar i verktygsanrop och funktionstillförlitlighet

### Molnbaserade modeller

Analysera:

- modellkvalitet och stabilitet
- kostnad per körning
- skalbarhet och integrationsstöd
- risker kring sekretess och leverantörsberoende

## AI-agent POC-rapport

Statusbedömningen mot projektmålet har brutits ut till en egen rapport:

- [AI-agent POC-rapport](../ai-agents-poc-report/)

Denna rapport fungerar som underlag för slutrapporten och samlar nulägesbild, uppnådda egenskaper, begränsningar och nästa steg för den aktuella QA-agent-POC:n.
