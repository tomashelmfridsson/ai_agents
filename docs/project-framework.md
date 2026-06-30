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

## Aktuell statusbedömning mot projektmålet

Den nuvarande QA Agent POC:n har nu nått en nivå där den ger en praktisk förståelse för flera centrala agentbegrepp som tidigare endast fanns som teori i projektbriefen. POC:n visar i körbar form hur ett fleragentsystem kan organiseras kring specialiserade roller, styras av en orkestrator och kombineras med både strukturerad baslinjekörning och LLM-backed körning.

Det som nu tydligt är uppnått är:

- specialiserade agentroller med tydligt ansvar,
- orchestrator-first routing,
- selektiv backtracking i stället för endast full rerun,
- shared working memory och agent private memory,
- per-agent modell-, provider-, timeout- och direktivkonfiguration,
- runtime visibility genom GUI, runtime activity och live log,
- partial-result preservation on failure,
- stöd för både lokal Ollama-körning och externa modellstrategier.

Detta innebär att projektet i hög grad har uppnått målet att förstå vad agentiska system är på en praktisk nivå, särskilt inom ett QA-orienterat arbetsflöde. Systemet visar inte bara att flera agenter kan existera samtidigt, utan också hur routing, återkoppling, minne, observability och styrbar exekvering påverkar resultatet.

Samtidigt återstår viktiga steg innan lösningen kan beskrivas som ett mer generellt agentramverk:

- agentexpansion är fortfarande kodnära och inte fullt dynamisk,
- tool-runtime och MCP-baserad integration är ännu inte en central del av arkitekturen,
- persistence och checkpointing är inte generiska på ramverksnivå,
- jämförelsen mot externa agentramverk är ännu inte genomförd empiriskt i samma detalj som den interna POC:n.

Den mest korrekta tolkningen i detta läge är därför att projektet har nått målet att förstå och demonstrera centrala agentegenskaper, men att nästa steg är att jämföra denna POC mer systematiskt mot etablerade agentplattformar och att avgöra vilka delar som bör behållas, generaliseras eller ersättas.

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
