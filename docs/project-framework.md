# Projektbrief för forskningsstudien

## Studiens teman

- AI Agents
- Multi-Agent Systems
- Agentic Software Engineering
- Agent Orchestration
- AI-assisted Quality Assurance
- Verification and Validation
- Test-Driven Development

## Analysfrågor per tema

### AI Agents

- Hur definieras en agent i aktuell litteratur?
- Vilka egenskaper återkommer: autonomi, planering, verktygsanvändning, minne, reflexion?
- Hur skiljer sig enkla agentloopar från orkestrerade multi-agentmiljöer?

### Multi-Agent Systems

- Vilka samarbetsmönster används: hierarki, marknadsbaserad delegation, blackboard, reviewer-loop?
- Hur hanteras konflikter, koordinering och delat tillstånd?
- Vilka risker finns kring felpropagering mellan agenter?

### Agentic Software Engineering

- Vilka delar av utvecklingslivscykeln stöds bäst av agenter?
- Hur mäts kvalitet, spårbarhet och produktivitet?
- Vilka arkitekturval underlättar styrbarhet och auditability?

### AI-assisted Quality Assurance

- Hur används AI för kravanalys, testdesign och testgenerering?
- Finns empiriskt stöd för förbättrad kravtäckning eller minskad ledtid?
- Hur hanteras testorakel, testdata och selektorer?

### Verification and Validation

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
| State management | Hur lagras mellanresultat, minne och spårbarhet? |
| Verktygsintegration | Hur väl stöds externa verktyg, RAG och testkörning? |
| Observability | Finns loggning, tracing och debug-stöd? |
| Lokal modellstöd | Hur lätt kopplas Ollama eller lokal inferens in? |
| Molnstöd | Hur väl stöds kommersiella modell-API:er? |
| QA-lämplighet | Hur väl passar plattformen kravanalys och testdesign? |

## Plattformar att jämföra

| Plattform | Förväntade styrkor | Frågor att undersöka |
|---|---|---|
| OpenClaw | Kandidat för experimentell agentautomation | Mognad, dokumentation, observability |
| Hermes Agent Framework | Fokus på agentstruktur | Hur väl lämpar den sig för QA-pipelines? |
| CrewAI | Tydlig rollbaserad multi-agentmodell | Hur styrbar är iteration och state? |
| LangGraph | Explicit grafbaserad orkestrering | Hur mycket boilerplate krävs? |
| AutoGen | Stark agent-till-agent-dialog | Hur robust blir deterministisk processkontroll? |
| OpenAI Agents SDK | Bra verktygs- och modellintegration | Hur väl stödjer den komplex flerstegsorkestrering? |

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

## Föreslagen rapportstruktur för litteraturdelen

- Introduktion och motiv
- Teoretisk bakgrund
- Jämförelse av agentramverk
- QA-relevanta designmönster
- Lokal kontra molnbaserad inferens
- Slutsatser som motiverar prototypens arkitektur
