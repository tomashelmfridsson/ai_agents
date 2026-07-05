# Teoretisk bakgrund och centrala begrepp

## Innehåll

- [Artificiell intelligens](#artificiell-intelligens)
- [Maskininlärning](#maskininlarning)
- [Djupinlärning](#djupinlarning)
- [Foundation Models](#foundation-models)
- [Generativ AI](#generativ-ai)
- [Large Language Models](#large-language-models)
- [Prompt Engineering](#prompt-engineering)
- [Embeddings](#embeddings)
- [Vector Databases](#vector-databases)
- [Retrieval-Augmented Generation](#retrieval-augmented-generation)
- [AI Agent](#ai-agent)
- [Agentic AI](#agentic-ai)
- [Multi-Agent System](#multi-agent-system)
- [Orchestrator](#orchestrator)
- [Agent Memory](#agent-memory)
- [Shared Working Memory](#shared-working-memory)
- [Planning](#planning)
- [Reflection och Review](#reflection-och-review)
- [Review Gate](#review-gate)
- [Selective Backtracking](#selective-backtracking)
- [Observability](#observability)
- [Runtime Trace](#runtime-trace)
- [Shared Blackboard](#shared-blackboard)
- [Synthesizer](#synthesizer)
- [Tool Calling](#tool-calling)
- [Function Calling](#function-calling)
- [Model Context Protocol](#model-context-protocol)
- [Software Engineering](#software-engineering)
- [AI for Software Engineering](#ai-for-software-engineering)
- [Agentic Software Engineering](#agentic-software-engineering)
- [Software Quality Assurance](#software-quality-assurance)
- [Verification and Validation](#verification-and-validation)
- [Requirement](#requirement)
- [Acceptance Criteria](#acceptance-criteria)
- [Requirement Traceability](#requirement-traceability)
- [Test Design](#test-design)
- [Test Oracle](#test-oracle)
- [Unit Test](#unit-test)
- [Integration Test](#integration-test)
- [GUI Test](#gui-test)
- [End-to-End Test](#end-to-end-test)
- [Test Automation](#test-automation)
- [Test-Driven Development](#test-driven-development)
- [Self-Healing](#self-healing)
- [Code Coverage](#code-coverage)
- [Requirement Coverage](#requirement-coverage)
- [Test Pass Rate](#test-pass-rate)
- [Iterationscykler](#iterationscykler)
- [Exekveringstid](#exekveringstid)
- [Code Quality](#code-quality)
- [SonarQube](#sonarqube)
- [Agent Framework](#agent-framework)
- [LangChain](#langchain)
- [LangGraph](#langgraph)
- [Hermes Agent Framework](#hermes-agent-framework)
- [Modellagnostisk arkitektur](#modellagnostisk-arkitektur)
- [Lokala och molnbaserade modeller](#lokala-och-molnbaserade-modeller)
- [Ollama](#ollama)
- [Hugging Face](#hugging-face)
- [Agent-as-a-Service](#agent-as-a-service)
- [REST API](#rest-api)
- [DeepEval](#deepeval)
- [Traceability Matrix](#traceability-matrix)
- [Gradio](#gradio)
- [Streamlit](#streamlit)
- [GitHub och GitHub Pages](#github-och-github-pages)
- [Continuous Integration](#continuous-integration)
- [Demonstrator](#demonstrator)
- [Artefakt](#artefakt)
- [Sammanfattning](#sammanfattning)

---

## Artificiell intelligens

Artificiell intelligens, ofta förkortat AI, är ett samlingsbegrepp för system som kan utföra uppgifter som traditionellt har krävt mänsklig intelligens. Det kan exempelvis handla om problemlösning, beslutsfattande, mönsterigenkänning, språkbearbetning, planering eller lärande.

I denna kontext används AI främst i betydelsen **generativ AI** och **agentisk AI**. Fokus ligger därmed inte på klassiska regelbaserade expertsystem, utan på moderna språkmodeller och agentramverk som kan tolka krav, generera testdesign och producera testartefakter.

AI kan delas in i flera nivåer. På en övergripande nivå finns artificiell intelligens som forskningsområde. Inom detta finns maskininlärning, där system lär sig från data. Inom maskininlärning finns djupinlärning, där neurala nätverk med många lager används. Moderna Large Language Models bygger huvudsakligen på djupinlärning och Transformer-arkitekturer.

AI är i detta sammanhang inte ett mål i sig, utan ett medel för att undersöka hur kvalitetssäkringsarbete kan stödjas av agentbaserade system.

## Maskininlärning

Maskininlärning är ett område inom AI där modeller tränas på data för att kunna identifiera mönster och göra prediktioner eller generera output. Till skillnad från traditionell programmering, där regler specificeras explicit, lär sig modellen statistiska samband från exempel.

Maskininlärning brukar ofta delas in i tre huvudtyper:

- **Övervakad inlärning**, där modellen tränas på exempel med kända svar.
- **Oövervakad inlärning**, där modellen identifierar struktur i data utan explicita etiketter.
- **Förstärkningsinlärning**, där modellen lär sig genom belöning och bestraffning i en miljö.

Maskininlärning är relevant eftersom LLM:er bygger på modeller som tränats på stora mängder text och kod. I många tillämpningar tränas inte egna modeller, utan befintliga modeller används som komponenter i större system.

## Djupinlärning

Djupinlärning är en underkategori av maskininlärning där neurala nätverk med flera lager används för att representera komplexa samband i data. Djupinlärning har haft stor betydelse för utvecklingen av moderna AI-system, särskilt inom bildanalys, taligenkänning, naturlig språkbehandling och kodgenerering.

Djupinlärning är här främst relevant som teknisk grund till de språkmodeller som används av agenter. Det är inte nödvändigt att själv implementera djupinlärningsmodeller, men det är viktigt att förstå att LLM:er inte “förstår” krav och tester på mänskligt sätt. De genererar sannolika och kontextberoende svar baserat på mönster från träningsdata och instruktioner.

Detta har betydelse för QA eftersom genererade testfall kan se rimliga ut utan att vara kompletta, korrekta eller spårbara mot krav. Därför behövs granskning, mätetal och iterativa feedbackmekanismer.

## Foundation Models

Foundation Models är stora, generella AI-modeller tränade på mycket omfattande datamängder och som kan anpassas till många olika uppgifter. En språkmodell som GPT, Claude, Llama, Qwen eller Gemini kan ses som exempel på foundation models.

Ett kännetecken för foundation models är att de inte är tränade för en enda smal uppgift, utan kan användas för många typer av uppgifter genom instruktioner, promptar, finjustering eller verktygsintegration. De kan exempelvis sammanfatta text, generera kod, analysera krav, skriva testfall eller resonera kring arkitektur.

Foundation models används ofta som den underliggande intelligensen i agenter. Själva modellen är dock inte samma sak som en agent. En modell genererar text eller kod. En agent kombinerar modellen med mål, instruktioner, verktyg, minne och ett arbetsflöde.

## Generativ AI

Generativ AI avser AI-system som kan skapa nytt innehåll. Det kan vara text, programkod, bilder, ljud, testfall, dokumentation eller andra artefakter. Inom mjukvaruutveckling används generativ AI exempelvis för kravanalys, kodgenerering, testgenerering, dokumentation, refaktorering och felsökning.

Generativ AI är relevant eftersom agenter kan skapa nya QA-artefakter. Exempel på sådana artefakter är:

- strukturerade krav
- acceptanskriterier
- testdesign
- enhetstester
- GUI- eller E2E-tester
- testdata
- granskningsrapporter

En viktig begränsning är att generativ AI kan producera output som verkar korrekt men som innehåller fel, saknar täckning eller bygger på implicita antaganden. Därför räcker det inte att generera testfall. Testfallen måste också kunna granskas, spåras mot krav och helst exekveras.

## Large Language Models

Large Language Models, ofta förkortat LLM:er, är stora språkmodeller tränade på omfattande text- och kodmängder. De används för att förstå och generera naturligt språk och programkod. Moderna LLM:er bygger vanligtvis på Transformer-arkitekturen och har visat stark förmåga inom bland annat textgenerering, kodgenerering, sammanfattning och frågebesvarande.

En LLM tar emot en kontext, exempelvis en användarfråga, instruktion eller ett dokumentutdrag, och genererar sedan en fortsättning. I ett agentiskt system fungerar LLM:n som den centrala besluts- och genereringskomponenten.

Exempel på LLM:er är:

- GPT
- Claude
- Gemini
- Llama
- Qwen
- DeepSeek
- Hermes
- Mistral

Det är viktigt att skilja mellan **modell** och **agent**. En modell är den underliggande språk- eller kodmodellen. En agent är ett system som använder modellen för att uppnå ett mål, ofta genom att använda verktyg, läsa och skriva filer, köra tester eller interagera med andra agenter.

I ett sådant system kan olika agenter använda olika modeller. Exempelvis kan en billigare eller lokal modell användas för kravanalys, medan en starkare kodmodell används för testgenerering eller implementation.

LLM:er är centrala i många sådana system, men de har flera begränsningar:

- de kan hallucinera
- de kan missa krav
- de kan skapa inkonsekventa testfall
- de kan generera kod som inte kör
- de kan överanpassa sig till prompten
- de kan sakna förståelse för domänspecifika begränsningar

Därför behövs agentorkestrering, granskningsloopar och utvärderingsmått.

## Prompt Engineering

Prompt engineering innebär att formulera instruktioner till en språkmodell på ett sätt som ökar sannolikheten för användbar output. En prompt kan innehålla uppgift, kontext, formatkrav, exempel och begränsningar.

I agentbaserade system används promptar för att styra agenternas beteende. Exempelvis kan Requirements Analyst Agent få instruktionen att extrahera krav och acceptanskriterier i JSON-format. Test Design Agent kan instrueras att skapa testfall med testtyp, teststeg, testdata och testorakel.

Prompt engineering är viktigt eftersom små skillnader i instruktioner kan påverka output kraftigt. För ett QA-system är det särskilt viktigt att promptarna kräver:

- strukturerat outputformat
- spårbarhet till krav-ID
- explicita antaganden
- identifiering av risker
- granskning av täckning
- konsekvent terminologi

I ett forskningsprojekt bör promptar behandlas som en del av metoden. De bör versioneras, dokumenteras och kunna återanvändas.

## Embeddings

Embeddings är numeriska representationer av text, kod eller andra objekt. Syftet är att placera semantiskt liknande innehåll nära varandra i ett vektorrum. Detta gör det möjligt att söka efter innehåll baserat på betydelse snarare än exakta nyckelord.

Exempelvis kan två formuleringar som “appen ska visa felmeddelande vid nätverksfel” och “systemet ska informera användaren om API-anropet misslyckas” hamna nära varandra i vektorrummet trots att orden skiljer sig.

Embeddings används ofta i RAG-system för att hitta relevanta dokument, krav, testfall eller tidigare buggrapporter. De blir särskilt relevanta när agenter ska kunna återanvända tidigare testdesign, befintliga testfall eller domänkunskap.

## Vector Databases

En vektordatabas lagrar embeddings och gör det möjligt att söka efter semantiskt liknande innehåll. Istället för att bara matcha ord kan en vektordatabas hitta innehåll som är begreppsmässigt relevant.

I ett QA-sammanhang kan en vektordatabas användas för att lagra:

- kravdokument
- testfall
- acceptanskriterier
- buggrapporter
- tidigare testdesign
- kodsnuttar
- arkitekturbeslut

Vektordatabaser är ofta inte huvudfokus i en första analys, men de kan stödja ett agentiskt system genom att ge agenterna tillgång till tidigare kunskap. Detta blir särskilt relevant när en enkel demonstrator utvecklas till ett mer realistiskt QA-stöd.

## Retrieval-Augmented Generation

Retrieval-Augmented Generation, RAG, är en teknik där en språkmodell kombineras med informationssökning. Istället för att enbart förlita sig på modellens interna parametrar hämtas relevant information från externa dokument eller databaser och ges som kontext till modellen. Den ursprungliga RAG-idén kombinerar parametrisk kunskap i modellen med icke-parametrisk kunskap i en extern informationskälla. ([arXiv](https://arxiv.org/abs/2005.11401?utm_source=chatgpt.com))

Ett typiskt RAG-flöde är:

```text
Fråga eller uppgift
  -> sök relevant information
  -> hämta dokumentutdrag
  -> skicka kontext till LLM
  -> generera svar
```

RAG kan användas som stödkomponent, men behöver inte vara huvudbidraget i en studie eller prototyp. Skillnaden mellan RAG och agentiska system är viktig:

- RAG hjälper modellen att hitta relevant information.
- En agent kan planera, använda verktyg, skapa artefakter, modifiera filer och initiera nya steg.
- Ett multi-agent-system kan fördela ansvar mellan flera specialiserade agenter.

RAG kan därför integreras i exempelvis Test Design Agent, som kan söka efter tidigare testfall eller tidigare krav innan nya testfall skapas.

## AI Agent

En AI-agent är ett system som använder en AI-modell, ofta en LLM, för att utföra en uppgift mer autonomt än en vanlig chatbot. En agent kan ha ett mål, instruktioner, tillgång till verktyg, minne, möjlighet att läsa och skriva filer samt förmåga att interagera med andra system.

En enkel chatbot svarar på en fråga. En agent kan däremot utföra ett arbetsflöde. Exempelvis kan en agent:

- läsa ett kravdokument
- extrahera krav
- spara resultatet som JSON
- skapa testfall
- köra tester
- analysera fel
- föreslå förbättringar

I forskning om LLM-baserade agenter inom software engineering beskrivs agenter ofta som system som utökar LLM:ers förmåga genom att ge dem möjlighet att uppfatta och använda externa resurser och verktyg. ([arXiv](https://arxiv.org/abs/2409.02977?utm_source=chatgpt.com))

I ett QA-arbetsflöde kan en agent beskrivas som en specialiserad komponent med ett tydligt ansvar, exempelvis kravanalys, testdesign, testgenerering eller granskning.

## Agentic AI

Agentic AI beskriver AI-system som inte bara genererar svar, utan också kan agera mot mål över flera steg. Det innebär att systemet kan planera, välja verktyg, utföra handlingar, utvärdera resultat och eventuellt iterera.

Agentic AI skiljer sig från vanlig generativ AI genom graden av handlingsförmåga. En generativ AI-modell kan skriva ett testfall. Ett agentiskt system kan analysera krav, besluta vilka tester som behövs, skapa testfall, kontrollera täckning och begära förbättring om täckningen är otillräcklig.

Agentisk AI används ofta för att beskriva en övergripande arkitektur där en orkestrator koordinerar flera specialiserade agenter. Detta är centralt när fokus inte bara ligger på att generera enstaka artefakter, utan på att undersöka hur ett fler-stegsflöde kan stödja kravbaserad testdesign.

## Multi-Agent System

Ett Multi-Agent System består av flera agenter som samarbetar eller samordnas för att lösa en uppgift. Varje agent kan ha en särskild roll, specialisering eller uppgift.

I traditionell mjukvaruarkitektur kan man beskriva detta som en uppdelning av ansvar. I ett multi-agent-system förstärks detta genom att varje agent kan använda en LLM och potentiellt fatta egna beslut inom sitt ansvarsområde.

Ett exempel på rolluppdelning är följande agenter:

- Orchestrator Agent
- Requirements Analyst Agent
- Test Design Agent
- Test Generation Agent
- Review Agent

Syftet med denna uppdelning är att efterlikna ett QA-arbetsflöde där kravanalys, testdesign, testimplementation och granskning är olika aktiviteter. Multi-agent-arkitekturen gör det också möjligt att använda olika modeller för olika uppgifter.

## Orchestrator

En orkestrator är en komponent eller agent som styr arbetsflödet mellan andra agenter. Orkestratorn ansvarar för att delegera uppgifter, samla resultat, initiera iterationer och avgöra när arbetsflödet kan gå vidare.

I ett enkelt agentflöde är sekvensen hårdkodad:

```text
Agent 1 -> Agent 2 -> Agent 3
```

I ett mer agentiskt system styrs flödet av en orkestrator:

```text
Krav
  -> Orchestrator
  -> Requirements Analyst
  -> Review
  -> Test Design
  -> Review
  -> Test Generation
  -> Review
  -> Slutresultat
```

Skillnaden är viktig. I en hårdkodad kedja sker stegen alltid i samma ordning. I ett orkestrerat system kan resultat från en agent granskas och skickas tillbaka för förbättring innan nästa steg startar.

I agentiska system är orkestratorn central eftersom den gör det möjligt att gå bortom en enkel hårdkodad agentkedja.

## Agent Memory

Agentminne syftar på information som en agent kan behålla eller återanvända över tid. Det kan vara korttidsminne under en körning eller långtidsminne mellan olika körningar.

Exempel på minne i ett sådant system kan vara:

- tidigare krav
- genererade acceptanskriterier
- tidigare testfall
- tidigare granskningskommentarer
- modellval
- kända felmönster
- testdesignbeslut

Minnet kan implementeras på olika sätt, exempelvis som JSON-filer, databasposter, embeddings eller versionshanterade artefakter. För en första prototyp kan filbaserat minne vara tillräckligt.

Agentminne är viktigt för QA eftersom testdesign ofta bygger på tidigare erfarenhet. Ett system som kan återanvända tidigare testmönster kan potentiellt skapa mer konsekventa och relevanta tester.

## Shared Working Memory

Shared Working Memory är ett mer specifikt begrepp än allmänt agentminne. Det syftar på ett delat arbetsminne som flera agenter kan läsa från och skriva till under samma körning.

I just detta projekt är begreppet centralt eftersom den egenbyggda lösningen använder ett synligt run-scoped arbetsminne med både delad och agentprivat information. Det är alltså inte bara ett teoretiskt minnesbegrepp, utan en konkret del av hur prototypen styr kontext, återkoppling och spårbarhet mellan stegen.

## Planning

Planning innebär att en agent eller orkestrator bryter ner ett mål i delsteg. I ett QA-system kan målet vara att skapa testartefakter från krav. Detta kan delas upp i kravanalys, acceptanskriterier, testdesign, testgenerering och granskning.

Planning är en viktig del av agentiska system eftersom det gör att systemet kan arbeta över flera steg snarare än att bara ge ett direkt svar. Planeringen kan exempelvis ligga hos en Orchestrator Agent.

Exempel:

```text
Mål: Skapa testartefakter från krav

Plan:
1. Extrahera krav
2. Skapa acceptanskriterier
3. Designa tester
4. Generera konkreta testfall
5. Granska spårbarhet
6. Iterera vid behov
```

## Reflection och Review

Reflection innebär att ett AI-system granskar sitt eget eller en annan agents output och försöker identifiera brister. Termen används ofta i praktiken i form av en Review Agent eller motsvarande granskningssteg.

Review Agent har en viktig QA-roll. Den ska inte primärt skapa nya testfall, utan granska om de artefakter som skapats är tillräckliga. Exempel på granskningsfrågor är:

- Är varje krav täckt av minst ett testfall?
- Finns tydliga acceptanskriterier?
- Finns testorakel?
- Är teststegen exekverbara?
- Finns antaganden dokumenterade?
- Finns risker eller luckor?

Review Agent kan därmed fungera som en kvalitetsgrind mellan agentstegen.

## Review Gate

Review Gate är inte nödvändigtvis ett universellt standardbegrepp, men det är användbart i detta sammanhang för att beskriva ett granskningssteg som fungerar som kvalitetsgrind innan arbetsflödet får gå vidare.

I projektet syns detta dels i den egna Review Agent-logiken, dels i Hermes-spåret där verifiering och gate-beslut användes som ett tydligt kontrollsteg innan slutartefakten syntetiserades. Begreppet bör därför förstås som projektnära och arbetsflödesspecifikt.

## Selective Backtracking

Selective Backtracking beskriver ett arbetsflöde där systemet inte alltid startar om hela processen från början, utan endast går tillbaka till det steg som behöver förbättras.

Detta är särskilt relevant i just denna prototyp, eftersom orkestratorn försöker skicka tillbaka arbetet till minsta rimliga tidigare steg, exempelvis Requirements Analyst eller Test Design, i stället för att göra en full omkörning. Begreppet är alltså viktigt här som beskrivning av projektets routingstrategi.

## Observability

Observability betyder här att användaren kan följa vad systemet faktiskt gör under körning, inte bara se slutresultatet. Det omfattar exempelvis insyn i agentinput, agentoutput, routingbeslut, vald modell, timeoutstatus och minnesuppdateringar.

Observability är mycket centralt i detta projekt och mer konkret än i många allmänna agentdiskussioner. Här handlar det alltså inte bara om loggning i bred mening, utan om att prototypen medvetet byggts för att göra agentbeteende och körspår granskningsbara i GUI och loggar.

## Runtime Trace

Runtime Trace syftar på den spårkedja av händelser som uppstår under en körning, till exempel när ett steg startar, avslutas, skickas vidare eller stoppas.

Begreppet är projektspecifikt relevant eftersom prototypen visar runtime activity och andra körspår i realtid. En runtime trace gör det lättare att förstå varför ett agentflöde lyckades, misslyckades eller fastnade i iterationer.

## Shared Blackboard

Shared Blackboard kommer från blackboard-liknande samarbetsmönster där flera agenter delar en gemensam arbetsyta. Det är nära besläktat med delat minne, men används oftare när fokus ligger på samordning mellan flera roller som skriver till samma gemensamma kontext.

I detta projekt är begreppet främst relevant för Hermes-lösningen, där en root task fungerade som ett shared blackboard för swarmen. Därför bör det förklaras som ett jämförelsebegrepp knutet till det externa ramverksspåret snarare än som huvudterm för den egenbyggda lösningen.

## Synthesizer

En Synthesizer är en agentroll vars uppgift är att sammanfoga och förädla resultat från flera tidigare agentsteg till en slutlig, samlad artefakt. Till skillnad från en vanlig worker-agent producerar den alltså inte främst ett delresultat utifrån råinput, utan tar emot flera mellanresultat och sammanställer dem till en mer komplett leverabel.

I Hermes-spåret användes Synthesizer som den avslutande rollen efter verifieringssteget. Den tog då emot material från tidigare specialistroller och formade den slutliga testdesignen. Begreppet är därför relevant i detta projekt som en beskrivning av Hermes Agent-lösningen, inte som en central komponent i den egenbyggda HF QA agent service-lösningen.

## Tool Calling

Tool Calling innebär att en agent kan använda externa verktyg för att utföra handlingar. Det kan exempelvis vara att läsa filer, skriva JSON, söka i dokument, köra tester eller anropa ett API.

Tool Calling är en central skillnad mellan en vanlig LLM och en agent. En LLM kan föreslå ett kommando. En agent med verktygsåtkomst kan potentiellt utföra kommandot.

I ett sådant system kan tool calling användas för att:

- läsa kravfiler
- skriva strukturerade krav i JSON
- skapa testfall som filer
- köra testverktyg
- läsa testresultat
- generera rapporter

Detta gör systemet mer integrerat och närmare ett verkligt QA-arbetsflöde.

## Function Calling

Function Calling är en specifik form av tool calling där modellen anropar fördefinierade funktioner med strukturerade argument. Det kan exempelvis handla om att modellen returnerar ett JSON-objekt som sedan används för att anropa en funktion i programmet.

Exempel:

```json
{
  "requirement_id": "R1",
  "test_type": "unit",
  "priority": "high"
}
```

Function Calling är särskilt relevant när man vill ha strukturerad output från en LLM. Det kan användas för att skapa konsekventa kravobjekt, testdesignobjekt och granskningsresultat.

## Model Context Protocol

Model Context Protocol, MCP, är en öppen standard för att koppla AI-applikationer till externa datakällor och verktyg. Syftet är att skapa ett standardiserat sätt för AI-system att få åtkomst till kontext, data och funktioner. ([Anthropic](https://www.anthropic.com/news/model-context-protocol?utm_source=chatgpt.com))

MCP kan beskrivas som ett integrationslager mellan AI-modeller och omgivande system. Istället för att varje agentramverk bygger egna speciallösningar för filsystem, databaser, GitHub, testverktyg eller dokumenthantering kan MCP ge ett gemensamt protokoll.

MCP är relevant som ett möjligt integrationsmönster. För en första prototyp är det inte säkert att MCP behöver implementeras, men begreppet är viktigt eftersom moderna agentplattformar allt oftare använder standardiserade verktygsintegrationer.

## Software Engineering

Software Engineering avser systematisk utveckling, drift och underhåll av mjukvarusystem. Det omfattar kravhantering, design, implementation, testning, deployment, underhåll och kvalitetssäkring.

Detta projekt är placerat inom software engineering eftersom det undersöker hur AI-agenter kan stödja ett konkret mjukvaruutvecklingsflöde: från krav till testartefakter.

Fokus ligger inte på AI som fristående teknik, utan på hur AI kan integreras i en mjukvaruprocess.

## AI for Software Engineering

AI for Software Engineering innebär användning av AI-tekniker för att stödja mjukvaruutveckling. Exempel är kodgenerering, kravanalys, testgenerering, felsökning, refaktorering, dokumentation och kodgranskning.

LLM-baserade agenter har blivit särskilt intressanta inom software engineering eftersom de kan kombinera språkförståelse, kodgenerering och verktygsanvändning. En aktuell survey beskriver hur LLM-baserade agenter används inom software engineering och hur flera agenter och mänsklig interaktion kan bidra till att hantera komplexa problem. ([arXiv](https://arxiv.org/abs/2409.02977?utm_source=chatgpt.com))

I detta sammanhang fokuseras AI for Software Engineering på QA och testrelaterade aktiviteter snarare än generell kodproduktion.

## Agentic Software Engineering

Agentic Software Engineering innebär att agentiska AI-system används för att stödja eller automatisera delar av mjukvaruutvecklingsprocessen. Skillnaden mot enklare AI-assistenter är att agentiska system kan arbeta över flera steg, använda verktyg och samordna flera specialiserade roller.

Exempel på agentiska software engineering-flöden är:

- krav till kod
- krav till testfall
- buggrapport till fix
- kod till testsvit
- testresultat till kodreparation
- Pull Request-granskning

Agentic Software Engineering kan användas för att skapa QA-orienterade arbetsflöden där agenter transformerar krav till testdesign och testartefakter.

## Software Quality Assurance

Software Quality Assurance, QA, omfattar processer, metoder och aktiviteter som syftar till att säkerställa mjukvarukvalitet. QA handlar inte bara om att hitta fel genom testning, utan även om att bygga kvalitet genom kravhantering, granskning, processkontroll, spårbarhet och förbättring.

QA-perspektivet är centralt. Målet är inte bara att generera kod eller tester, utan att undersöka hur agentiska system kan stödja ett kvalitetssäkrat arbetsflöde.

Viktiga QA-aspekter i projektet är:

- kravtäckning
- testdesign
- spårbarhet
- testorakel
- review-loopar
- mätbar kvalitet
- iterationscykler

## Verification and Validation

Verification and Validation, ofta förkortat V&V, är centrala begrepp inom kvalitetssäkring.

- **Verification** handlar om att kontrollera att systemet byggs korrekt enligt specifikation.
- **Validation** handlar om att kontrollera att rätt system byggs utifrån användarens behov.

I denna kontext kan verification kopplas till att genererade tester spåras mot krav och att testartefakter följer specificerade format. Validation är svårare, eftersom den kräver förståelse för om kraven faktiskt motsvarar verkliga behov.

Ett agentiskt QA-system kan potentiellt stödja både verification och validation, men den första prototypen bör främst fokusera på verification.

## Requirement

Ett krav beskriver en egenskap, funktion, begränsning eller kvalitet som ett system ska uppfylla. Krav kan vara funktionella eller icke-funktionella.

Exempel på funktionellt krav:

```text
Systemet ska kunna visa ett skämt från ett externt API.
```

Exempel på icke-funktionellt krav:

```text
Systemet ska visa svar inom två sekunder.
```

I kravdrivna agentflöden är krav ofta den huvudsakliga inputen. En Requirements Analyst Agent kan bryta ner kravtext till strukturerade krav med ID, beskrivning, aktör, handling, villkor och acceptanskriterier.

## Acceptance Criteria

Acceptanskriterier beskriver under vilka villkor ett krav anses vara uppfyllt. De gör kravet mer testbart och fungerar som brygga mellan krav och testdesign.

Exempel:

```text
Krav: Användaren ska kunna hämta ett nytt skämt.

Acceptanskriterier:
- När användaren klickar på knappen "New joke" ska ett nytt API-anrop skickas.
- När API-anropet lyckas ska ett nytt skämt visas.
- Om API-anropet misslyckas ska ett felmeddelande visas.
```

Acceptanskriterier är centrala eftersom en Test Design Agent kan använda dem för att skapa testfall.

## Requirement Traceability

Requirement Traceability innebär att krav kan kopplas till andra artefakter, exempelvis acceptanskriterier, testfall, kod eller buggrapporter. Spårbarhet är viktigt för att kunna visa att varje krav har verifierats.

Spårbarhet används ofta för att mäta kravtäckning. Varje genererat testfall bör referera till ett eller flera krav-ID.

Exempel:

| Krav-ID | Testfall | Testtyp |
|---|---|---|
| R1 | TC-001 | Enhetstest |
| R2 | TC-002 | GUI-test |
| R3 | TC-003 | E2E-test |

Spårbarhet är också viktigt för Review Agent, som kan identifiera krav utan testtäckning.

## Test Design

Testdesign är processen att utforma testfall baserat på krav, risker, systembeteende och acceptanskriterier. Testdesign handlar inte bara om att skriva testkod, utan om att bestämma vad som ska testas, varför det ska testas och hur testet ska avgöra om resultatet är korrekt.

En Test Design Agent kan vara ansvarig för att skapa en testdesign som innehåller:

- testtyp
- testsyfte
- teststeg
- testdata
- testorakel
- koppling till krav
- risker och antaganden

Testdesign är en central QA-aktivitet och bör särskiljas från testgenerering. Testdesign beskriver vad som ska testas. Testgenerering skapar de konkreta testartefakterna.

## Test Oracle

Ett testorakel avgör om ett testresultat är korrekt eller felaktigt. Utan ett testorakel kan ett test exekveras, men det går inte att veta om resultatet är rätt.

Exempel:

```text
Om API:et returnerar status 200 och ett fält "value", ska texten i "value" visas i användargränssnittet.
```

Detta är ett testorakel eftersom det anger förväntat beteende.

I AI-genererad testdesign är testorakel särskilt viktigt. Ett vanligt problem är att modeller genererar teststeg utan tydliga förväntade resultat. Därför bör Test Design Agent alltid tvingas ange testorakel.

## Unit Test

Ett enhetstest testar en liten isolerad del av systemet, exempelvis en funktion, klass eller komponent. Enhetstester är ofta snabba och används för att verifiera logik på låg nivå.

I sådana system kan enhetstester användas för att testa exempelvis:

- parsning av API-svar
- hantering av fel
- transformationslogik
- validering av input

Enhetstester är särskilt viktiga i ett TDD-flöde eftersom de kan skapas tidigt och användas för att styra implementation.

## Integration Test

Ett integrationstest verifierar att flera komponenter fungerar tillsammans. Exempelvis kan ett integrationstest kontrollera att en backend-komponent korrekt anropar ett externt API och hanterar svaret.

Integrationstester blir relevanta när en demonstrator eller applikation innehåller både frontend, backend och extern API-koppling.

## GUI Test

Ett GUI-test testar systemet genom det grafiska användargränssnittet. Det kan exempelvis kontrollera att knappar, textfält och felmeddelanden fungerar som förväntat.

GUI-testning är relevant när genererade tester ska kunna verifiera användarens synliga interaktion med en webbapplikation.

GUI-tester kräver ofta selektorer, exempelvis:

```text
#new-joke-button
#joke-text
#error-message
```

Därför behöver Test Design Agent definiera selektorer som senare implementationen måste följa.

## End-to-End Test

Ett End-to-End-test, E2E-test, testar ett systemflöde från användarens perspektiv genom flera lager av systemet. Ett E2E-test kan exempelvis öppna webbsidan, klicka på en knapp, vänta på ett API-svar och kontrollera att resultatet visas.

E2E-tester är ofta mer realistiska än enhetstester men också långsammare och mer känsliga för miljöproblem.

E2E-tester kan användas för att verifiera att hela flödet från krav till fungerande användarinteraktion är korrekt.

## Test Automation

Testautomation innebär att tester exekveras automatiskt av verktyg istället för manuellt av en människa. Testautomation är centralt i moderna CI/CD-flöden.

Testautomation är relevant på två nivåer:

1. Agenterna genererar testartefakter automatiskt.
2. De genererade testerna kan köras automatiskt för att verifiera systemet.

Detta gör att projektet ligger nära både AI-assisterad testdesign och automatiserad QA.

## Test-Driven Development

Test-Driven Development, TDD, är en utvecklingsmetodik där tester skrivs före produktionskoden. Ett klassiskt TDD-flöde beskrivs ofta som:

```text
Red -> Green -> Refactor
```

Det betyder:

- skriv ett test som först misslyckas
- implementera minsta möjliga kod för att testet ska passera
- förbättra koden utan att ändra beteendet

TDD kan användas som designprincip. Då skapar Test Design Agent och Test Generation Agent testdesign och testfall innan eventuell implementation sker. En Implementation Agent eller motsvarande komponent kan sedan skapa eller modifiera kod tills testerna passerar.

## Self-Healing

Self-healing innebär att ett system automatiskt upptäcker fel, analyserar orsaken och försöker korrigera problemet. I kontexten av agentisk mjukvaruutveckling kan self-healing innebära att en agent kör tester, läser felmeddelanden, modifierar kod eller testartefakter och kör tester igen.

Self-healing kan beskrivas som en iterativ feedback-loop:

```text
Generera artefakt
  -> Granska eller testa
  -> Identifiera fel
  -> Förbättra artefakt
  -> Kör igen
```

Self-healing är inte samma sak som att systemet alltid hittar rätt lösning. Det innebär snarare att systemet har en mekanism för att iterera baserat på feedback.

## Code Coverage

Code Coverage, eller kodtäckning, mäter hur stor del av koden som exekveras av testerna. Vanliga typer av täckning är:

- radtäckning
- funktions- eller metodtäckning
- grentäckning

Kodtäckning är ett användbart men begränsat mått. Hög kodtäckning betyder inte nödvändigtvis att testerna är bra. Tester kan exekvera kod utan att kontrollera rätt beteende.

Kodtäckning kan användas som ett kompletterande mått, men bör inte vara det enda måttet på testkvalitet.

## Requirement Coverage

Requirement Coverage mäter hur stor andel krav som täcks av testfall. Detta är särskilt relevant i sammanhang där målet är kravbaserad testdesign.

Exempel:

```text
Antal krav med minst ett testfall / Totalt antal krav
```

Om 8 av 10 krav har minst ett kopplat testfall är kravtäckningen 80 %.

Kravtäckning är centralt för Review Agent, som kan identifiera krav utan testfall eller krav med otillräcklig testdesign.

## Test Pass Rate

Test Pass Rate mäter andelen tester som passerar vid exekvering.

Exempel:

```text
Antal passerade tester / Totalt antal tester
```

Detta är ett enkelt men viktigt mått. I ett self-healing-flöde kan Test Pass Rate användas för att avgöra om systemet behöver iterera.

## Iterationscykler

Iterationscykler mäter hur många gånger systemet behöver gå igenom en gransknings- eller reparationsloop innan resultatet godkänns.

Detta är ett särskilt intressant mått eftersom det fångar hur effektivt ett agentiskt system är. Om ett system kräver många iterationer kan det tyda på bristande promptar, svag modell, dålig testdesign eller otydlig kravstruktur.

## Exekveringstid

Exekveringstid mäter hur lång tid ett agentflöde eller testflöde tar att köra. Detta kan mätas per agentsteg eller för hela pipeline.

Exempel:

| Steg | Tid |
|---|---|
| Kravanalys | 20 sekunder |
| Testdesign | 45 sekunder |
| Testgenerering | 60 sekunder |
| Granskning | 30 sekunder |
| Totalt | 155 sekunder |

Exekveringstid är relevant eftersom agentiska system kan bli långsamma, särskilt om flera modeller, verktyg och review-loopar används.

## Code Quality

Code Quality, eller kodkvalitet, avser egenskaper som påverkar hur lätt kod är att förstå, underhålla, testa och vidareutveckla. Exempel på kodkvalitetsmått är:

- komplexitet
- duplicering
- kodlukt
- maintainability
- security issues
- reliability issues

Kodkvalitet kan användas som mått om systemet även genererar kod eller testkod. För Python kan verktyg som ruff, pylint och radon användas. För bredare analys kan SonarQube vara relevant.

## SonarQube

SonarQube är ett verktyg för statisk kodanalys. Det kan analysera kodkvalitet, säkerhetsproblem, duplicering, kodlukt och ibland testtäckning beroende på konfiguration.

SonarQube kan användas som ett möjligt verktyg för att mäta kvaliteten på genererad kod eller genererade tester. För en första prototyp kan enklare verktyg som linting och coverage vara tillräckliga, men SonarQube är relevant som industriellt etablerat verktyg.

## Agent Framework

Ett agentramverk är ett bibliotek eller en plattform för att skapa, konfigurera och köra AI-agenter. Agentramverk erbjuder ofta stöd för roller, verktygsanrop, minne, orkestrering, kommunikation mellan agenter och integration med olika LLM:er.

Exempel på agentramverk eller agentplattformar är:

- CrewAI
- LangGraph
- AutoGen
- OpenAI Agents SDK
- OpenClaw
- Hermes Agent Framework

Valet av agentramverk är en central del av många litteraturstudier och prototyper. Ett viktigt mål är att förstå vilka ramverk som passar bäst för QA-arbetsflöden där krav, testdesign, testgenerering och granskning behöver samordnas.

## LangChain

LangChain är ett biblioteksekosystem för att bygga LLM-baserade applikationer. Det erbjuder byggblock för promptar, kedjor, verktygsanrop, minne, dokumenthämtning och integration med olika modellleverantörer.

LangChain är relevant eftersom det länge varit en vanlig bas för agentliknande och verktygsstödda LLM-flöden. I detta projekt är LangChain främst relevant som omgivande ekosystem till LangGraph, snarare än som huvudramverk för den egenbyggda lösningen.

## LangGraph

LangGraph är ett grafbaserat agentramverk inom LangChain-ekosystemet. Det används för att definiera noder, tillstånd och övergångar i agentiska arbetsflöden på ett mer explicit sätt än i enklare promptkedjor.

LangGraph är relevant här eftersom det användes som ett jämförelsespår till den egenbyggda orkestratorlösningen. Styrkan ligger i tydlig modellering av grafstruktur, state management och övergångar mellan steg. Begränsningen i detta projekt var att flödet blev mer hårdkodat än i den egenbyggda lösningen med mer dynamisk routing.

## Hermes Agent Framework

Hermes Agent Framework är ett agentramverk som användes som ett externt jämförelsespår i projektet. Det blev särskilt relevant genom den swarm-lösning som sattes upp för att jämföra hur snabbt och tydligt ett QA-liknande fleragentflöde kunde byggas i ett annat ramverk.

I projektet användes Hermes för att skapa en Kanban-liknande swarm med tydliga roller, shared blackboard och verifieringssteg. Därför är Hermes viktigt både som begrepp i litteraturstudien och som praktiskt jämförelseobjekt mot den egenbyggda lösningen och LangGraph-spåret.

## Modellagnostisk arkitektur

En modellagnostisk arkitektur innebär att systemet inte är hårt bundet till en specifik LLM. Istället kan olika modeller användas beroende på uppgift, kostnad, tillgänglighet och kvalitet.

Exempel:

```yaml
requirements_model: qwen
test_design_model: deepseek
test_generation_model: gpt
review_model: claude
```

Detta är viktigt i projektet eftersom olika agenter kan ha olika behov. Kravanalys kan kanske utföras av en lokal modell, medan testgenerering kan kräva en starkare kodmodell.

## Lokala och molnbaserade modeller

Lokala modeller körs på egen hårdvara eller i egen miljö, ofta via verktyg som Ollama. Molnbaserade modeller körs via API:er från exempelvis OpenAI, Anthropic, Google eller Hugging Face.

Lokala modeller kan ge bättre kontroll, lägre marginalkostnad och potentiellt bättre datasekretess. Molnbaserade modeller kan ge högre kvalitet, bättre kodförmåga och enklare drift.

Det kan vara relevant att stödja båda alternativen. Det gör en prototyp mer flexibel och gör det möjligt att jämföra olika modellval.

## Ollama

Ollama är ett verktyg för att köra lokala språkmodeller. Det används ofta tillsammans med modeller som Llama, Qwen, Mistral, DeepSeek och Hermes.

Ollama kan användas om agenter ska kunna köras med lokala modeller. Detta gör det möjligt att testa hur långt man kan komma utan kommersiella API:er.

## Hugging Face

Hugging Face är en plattform för AI-modeller, datasets och applikationer. Hugging Face Spaces kan användas för att publicera enkla AI-demonstratorer och webbaserade gränssnitt.

Hugging Face är relevant på två sätt:

1. som möjlig källa till modeller och API:er
2. som hostingmiljö för demonstratorn

Eftersom projektet redan har erfarenhet från en tidigare RAG-prototyp på Hugging Face är det ett naturligt alternativ för den första demonstratorn.

I detta projekt användes Hugging Face också för att hosta `qa-agent-service` och göra agentfunktioner tillgängliga via publika endpoints. Därmed blev Hugging Face inte bara en modellplattform utan också en praktisk driftmiljö för agentnära tjänster.

## Agent-as-a-Service

Agent-as-a-Service kan användas som begrepp när agentfunktionalitet exponeras som en separat tjänst i stället för att all agentlogik körs direkt i samma applikation. I praktiken innebär det att klienter anropar en agentbackend via nätverk, exempelvis genom HTTP-baserade endpoints.

Detta begrepp passar väl in på projektets `qa-agent-service`, där Requirements Analyst, Test Design och Review kunde exponeras som publika tjänster på Hugging Face. Även om termen inte alltid används lika konsekvent i litteraturen är den användbar här för att beskriva skillnaden mellan:

- agenter som kör direkt i samma app
- agenter som används som en separat hostad tjänst

## REST API

REST API är ett vanligt sätt att exponera funktionalitet över HTTP. En klient skickar förfrågningar till definierade endpoints och får tillbaka svar i exempelvis JSON-format.

REST API är relevant i projektet eftersom `qa-agent-service` utvecklades från ett mer nyckelberoende Hugging Face-upplägg till publika REST-endpoints. Detta gjorde tjänsten lättare att återanvända från olika klienter och ramverk, inklusive jämförelser mot Hermes och andra integrationsspår.

## DeepEval

DeepEval är ett ramverk för att utvärdera LLM-baserade applikationer och agentflöden. Det används för att mäta kvalitet i genererat innehåll med hjälp av definierade kriterier och evalueringslogik, snarare än enbart manuella intryck.

DeepEval är relevant här eftersom det fanns tankar på att använda det för att bedöma kvaliteten i genererade testfall. Även om den praktiska utvärderingen senare i hög grad kom att bygga på Hermes-jämförelser och manuell Senior QA-granskning är DeepEval fortfarande ett viktigt begrepp att ha med i kunskapslistan.

## Traceability Matrix

Traceability Matrix är ett QA-begrepp för en struktur som kopplar krav till motsvarande testfall, verifieringssteg eller andra artefakter. Syftet är att visa att varje krav kan följas till någon form av validering.

Begreppet är relevant här eftersom spårbarhet mellan krav och testdesign är en av projektets kärnfrågor. I Hermes-jämförelsen producerades också en konkret traceability matrix, vilket gör att termen är praktiskt förankrad i det arbete som faktiskt genomfördes.

## Gradio

Gradio är ett Python-baserat ramverk för att bygga enkla webbgränssnitt för AI-applikationer och demonstratorer. Det används ofta för snabb prototyputveckling, särskilt tillsammans med Hugging Face Spaces.

Gradio är centralt i projektet eftersom AI Agents-delen byggdes i Gradio. Ett viktigt skäl var att det redan fanns viss tidigare erfarenhet av verktyget, vilket gjorde det till ett pragmatiskt val för att snabbt få fram en fungerande publik experimentmiljö.

## Streamlit

Streamlit är ett Python-ramverk för att bygga datadrivna webbapplikationer och interaktiva gränssnitt med relativt liten mängd kod. Det används ofta för prototyper, dashboards och AI-demonstratorer.

Streamlit är relevant i projektet eftersom LangGraph-spåret kom att köras i Streamlit. Skälet var att Gradio medförde praktiska begränsningar för just den delen av arbetet, vilket gjorde Streamlit till ett mer fungerande alternativ i den jämförelsen.

## GitHub och GitHub Pages

GitHub används för versionshantering, källkod och dokumentation. GitHub Pages används för att publicera projektets kunskapsbas som en öppen webbsida.

GitHub kan fylla två roller:

- teknisk versionshantering av kod och dokument
- publik dokumentationsyta för kunskapsbasen

GitHub Pages gör att litteraturstudien och kunskapsbasen kan publiceras löpande och göras tillgänglig för handledare, kollegor och framtida läsare.

## Continuous Integration

Continuous Integration, CI, innebär att kod och tester körs automatiskt när ändringar görs i ett repository. CI kan användas för att bygga, testa och deploya mjukvara.

CI kan användas för att:

- köra genererade tester
- mäta testresultat
- beräkna kodtäckning
- deploya demonstratorn
- publicera dokumentation

GitHub Actions är ett vanligt verktyg för CI i GitHub-baserade projekt.

## Demonstrator

En demonstrator är en prototyp som visar att en idé är tekniskt möjlig. Den behöver inte vara produktionsklar, men ska vara tillräckligt konkret för att kunna användas i utvärdering.

En demonstrator kan vara ett webbaserat system där användaren skickar in krav och får ut testartefakter. Demonstratorn används då för att undersöka om en föreslagen agentarkitektur är praktiskt genomförbar.

## Artefakt

En artefakt är ett konkret resultat som produceras i en utvecklings- eller QA-process. I ett sådant sammanhang kan artefakter vara:

- strukturerade krav
- acceptanskriterier
- testdesign
- testfall
- testdata
- selektorer
- rapporter
- kodfiler

Agentflödet kan beskrivas som en process där varje agent producerar eller granskar artefakter.

## Sammanfattning

Detta kapitel har introducerat de centrala begrepp som projektet bygger på. Den viktigaste distinktionen är skillnaden mellan en LLM, en AI-agent och ett agentiskt multi-agent-system.

En LLM är en modell som genererar text eller kod. En AI-agent använder en LLM tillsammans med instruktioner, verktyg och mål. Ett multi-agent-system består av flera specialiserade agenter som samordnas, ofta av en orkestrator.

En central idé i detta område är att använda agentisk AI för att stödja QA-arbetsflöden. Fokus ligger då på att transformera krav till testdesign och testartefakter med spårbarhet, granskning och möjlighet till iteration.

---

Detta material har tagits fram tillsammans med Generativ AI och har därefter granskats och bearbetats i projektets dokumentationsarbete.
---
