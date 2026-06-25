# AI-agenter för Software Quality Assurance

> **Status:** Under utveckling (Version 0.1)  
> **Språk:** Svenska  
> **Senast uppdaterad:** 2026-06-25

---

## Om dokumentet

Detta dokument utvecklas som en levande kunskapsbas inom **AI-agenter**, **Agentic AI** och **Software Quality Assurance (QA)**.

Syftet är att stegvis bygga upp en strukturerad förståelse för området genom att kombinera:

- Teoretisk bakgrund
- Litteraturstudier
- Jämförelser av agentramverk
- Designbeslut
- Implementation av en prototyp
- Utvärdering och experiment

Dokumentet har tre huvudsakliga syften:

1. Att fungera som kunskapsbas under projektets gång.
2. Att utgöra underlag för sommarprojektet.
3. Att på sikt kunna ligga till grund för ett eller flera forskningsarbeten.

---

## Användning av AI

Detta dokument utvecklas i samarbete mellan författaren och generativ AI (OpenAI ChatGPT).

AI används som stöd för:

- strukturering av innehåll
- begreppsförklaringar
- litteratursammanställningar
- textutkast
- diskussion kring arkitektur och design

Allt innehåll granskas, verifieras och revideras av författaren innan det inkluderas i dokumentet.

---

# Innehåll

1. Projektframework
2. Teoretisk bakgrund och centrala begrepp
3. Litteraturstudie
4. Agentramverk
5. Systemarkitektur
6. Designbeslut
7. Prototyp och implementation
8. Experiment och utvärdering
9. Framtida arbete
10. Forskningsartiklar
11. Referenser

---

# 1. Projektframework

## Forskningsfråga

Hur kan ett agentiskt QA-system med orkestrator och specialiserade agenter stödja kravbaserad testdesign och testgenerering, samt vilka agentramverk och arkitekturer är mest lämpade för detta ändamål?

## Delmål

1. Kartlägga relevanta agentramverk och jämföra deras lämplighet för QA-arbetsflöden.
2. Implementera en demonstrator som transformerar krav till testartefakter.
3. Utvärdera demonstratorn med tydliga kvalitets- och effektivitetsmått.

## Avgränsning

- Fokus ligger på QA-automation och agentorkestrering.
- Demonstratorn prioriterar spårbarhet från krav till testartefakter.
- Arkitekturen skall vara modellagnostisk och kunna använda både lokala och molnbaserade LLM:er.
- Projektet fokuserar på agentisk orkestrering snarare än generell kodgenerering.

---

# 2. Teoretisk bakgrund och centrala begrepp

Detta kapitel introducerar centrala begrepp som behövs för att förstå projektets forskningsfråga, arkitektur och prototyp. Kapitlet fungerar som en teoretisk grund för den fortsatta litteraturstudien och för de designbeslut som senare görs i projektet.

## 2.1 Artificiell intelligens

Artificiell intelligens, ofta förkortat AI, är ett samlingsbegrepp för system som kan utföra uppgifter som traditionellt har krävt mänsklig intelligens. Det kan exempelvis handla om problemlösning, beslutsfattande, mönsterigenkänning, språkbearbetning, planering eller lärande.

I detta projekt används AI främst i betydelsen **generativ AI** och **agentisk AI**. Det innebär att fokus inte ligger på klassiska regelbaserade expertsystem, utan på moderna språkmodeller och agentramverk som kan tolka krav, generera testdesign och producera testartefakter.

AI kan delas in i flera nivåer. På en övergripande nivå finns artificiell intelligens som forskningsområde. Inom detta finns maskininlärning, där system lär sig från data. Inom maskininlärning finns djupinlärning, där neurala nätverk med många lager används. Moderna Large Language Models bygger huvudsakligen på djupinlärning och Transformer-arkitekturer.

I projektet är AI inte ett mål i sig. AI används som ett medel för att undersöka hur kvalitetssäkringsarbete kan stödjas av agentbaserade system.

## 2.2 Maskininlärning

Maskininlärning är ett område inom AI där modeller tränas på data för att kunna identifiera mönster och göra prediktioner eller generera output. Till skillnad från traditionell programmering, där regler specificeras explicit, lär sig modellen statistiska samband från exempel.

Maskininlärning brukar ofta delas in i tre huvudtyper:

- **Övervakad inlärning**, där modellen tränas på exempel med kända svar.
- **Oövervakad inlärning**, där modellen identifierar struktur i data utan explicita etiketter.
- **Förstärkningsinlärning**, där modellen lär sig genom belöning och bestraffning i en miljö.

I detta projekt är maskininlärning relevant eftersom LLM:er bygger på modeller som tränats på stora mängder text och kod. Projektet kommer dock inte att träna egna modeller. Istället används befintliga modeller som komponenter i ett agentiskt QA-system.

## 2.3 Djupinlärning

Djupinlärning är en underkategori av maskininlärning där neurala nätverk med flera lager används för att representera komplexa samband i data. Djupinlärning har haft stor betydelse för utvecklingen av moderna AI-system, särskilt inom bildanalys, taligenkänning, naturlig språkbehandling och kodgenerering.

För detta projekt är djupinlärning främst relevant som teknisk grund till de språkmodeller som används av agenterna. Det är inte nödvändigt att själv implementera djupinlärningsmodeller, men det är viktigt att förstå att LLM:er inte “förstår” krav och tester på mänskligt sätt. De genererar sannolika och kontextberoende svar baserat på mönster från träningsdata och instruktioner.

Detta har betydelse för QA eftersom genererade testfall kan se rimliga ut utan att vara kompletta, korrekta eller spårbara mot krav. Därför behövs granskning, mätetal och iterativa feedbackmekanismer.

## 2.4 Foundation Models

Foundation Models är stora, generella AI-modeller tränade på mycket omfattande datamängder och som kan anpassas till många olika uppgifter. En språkmodell som GPT, Claude, Llama, Qwen eller Gemini kan ses som exempel på foundation models.

Ett kännetecken för foundation models är att de inte är tränade för en enda smal uppgift, utan kan användas för många typer av uppgifter genom instruktioner, promptar, finjustering eller verktygsintegration. De kan exempelvis sammanfatta text, generera kod, analysera krav, skriva testfall eller resonera kring arkitektur.

I projektet används foundation models som den underliggande intelligensen i agenterna. Själva modellen är dock inte samma sak som en agent. En modell genererar text eller kod. En agent kombinerar modellen med mål, instruktioner, verktyg, minne och ett arbetsflöde.

## 2.5 Generativ AI

Generativ AI avser AI-system som kan skapa nytt innehåll. Det kan vara text, programkod, bilder, ljud, testfall, dokumentation eller andra artefakter. Inom mjukvaruutveckling används generativ AI exempelvis för kravanalys, kodgenerering, testgenerering, dokumentation, refaktorering och felsökning.

I detta projekt är generativ AI relevant eftersom agenterna ska kunna skapa nya QA-artefakter. Exempel på sådana artefakter är:

- strukturerade krav
- acceptanskriterier
- testdesign
- enhetstester
- GUI- eller E2E-tester
- testdata
- granskningsrapporter

En viktig begränsning är att generativ AI kan producera output som verkar korrekt men som innehåller fel, saknar täckning eller bygger på implicita antaganden. Därför räcker det inte att generera testfall. Testfallen måste också kunna granskas, spåras mot krav och helst exekveras.

## 2.6 Large Language Models

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

I projektet kan olika agenter använda olika modeller. Exempelvis kan en billigare eller lokal modell användas för kravanalys, medan en starkare kodmodell används för testgenerering eller implementation.

LLM:er är centrala för projektet, men de har flera begränsningar:

- de kan hallucinera
- de kan missa krav
- de kan skapa inkonsekventa testfall
- de kan generera kod som inte kör
- de kan överanpassa sig till prompten
- de kan sakna förståelse för domänspecifika begränsningar

Därför behövs agentorkestrering, granskningsloopar och utvärderingsmått.

## 2.7 Prompt Engineering

Prompt engineering innebär att formulera instruktioner till en språkmodell på ett sätt som ökar sannolikheten för användbar output. En prompt kan innehålla uppgift, kontext, formatkrav, exempel och begränsningar.

I projektet används promptar för att styra agenternas beteende. Exempelvis kan Requirements Analyst Agent få instruktionen att extrahera krav och acceptanskriterier i JSON-format. Test Design Agent kan instrueras att skapa testfall med testtyp, teststeg, testdata och testorakel.

Prompt engineering är viktigt eftersom små skillnader i instruktioner kan påverka output kraftigt. För ett QA-system är det särskilt viktigt att promptarna kräver:

- strukturerat outputformat
- spårbarhet till krav-ID
- explicita antaganden
- identifiering av risker
- granskning av täckning
- konsekvent terminologi

I ett forskningsprojekt bör promptar behandlas som en del av metoden. De bör versioneras, dokumenteras och kunna återanvändas.

## 2.8 Embeddings

Embeddings är numeriska representationer av text, kod eller andra objekt. Syftet är att placera semantiskt liknande innehåll nära varandra i ett vektorrum. Detta gör det möjligt att söka efter innehåll baserat på betydelse snarare än exakta nyckelord.

Exempelvis kan två formuleringar som “appen ska visa felmeddelande vid nätverksfel” och “systemet ska informera användaren om API-anropet misslyckas” hamna nära varandra i vektorrummet trots att orden skiljer sig.

Embeddings används ofta i RAG-system för att hitta relevanta dokument, krav, testfall eller tidigare buggrapporter. I detta projekt kan embeddings bli relevanta om agenterna ska kunna återanvända tidigare testdesign, befintliga testfall eller projektkunskap.

## 2.9 Vector Databases

En vektordatabas lagrar embeddings och gör det möjligt att söka efter semantiskt liknande innehåll. Istället för att bara matcha ord kan en vektordatabas hitta innehåll som är begreppsmässigt relevant.

I ett QA-sammanhang kan en vektordatabas användas för att lagra:

- kravdokument
- testfall
- acceptanskriterier
- buggrapporter
- tidigare testdesign
- kodsnuttar
- arkitekturbeslut

I detta projekt är vektordatabaser inte huvudfokus, men de kan stödja ett agentiskt system genom att ge agenterna tillgång till tidigare kunskap. Detta är särskilt relevant om projektet senare utvecklas från en enkel demonstrator till ett mer realistiskt QA-stöd.

## 2.10 Retrieval-Augmented Generation

Retrieval-Augmented Generation, RAG, är en teknik där en språkmodell kombineras med informationssökning. Istället för att enbart förlita sig på modellens interna parametrar hämtas relevant information från externa dokument eller databaser och ges som kontext till modellen. Den ursprungliga RAG-idén kombinerar parametrisk kunskap i modellen med icke-parametrisk kunskap i en extern informationskälla. ([arXiv](https://arxiv.org/abs/2005.11401?utm_source=chatgpt.com))

Ett typiskt RAG-flöde är:

```text
Fråga eller uppgift
  -> sök relevant information
  -> hämta dokumentutdrag
  -> skicka kontext till LLM
  -> generera svar
```

I detta projekt kan RAG användas som stödkomponent, men det är inte projektets huvudbidrag. Skillnaden mellan RAG och agentiska system är viktig:

- RAG hjälper modellen att hitta relevant information.
- En agent kan planera, använda verktyg, skapa artefakter, modifiera filer och initiera nya steg.
- Ett multi-agent-system kan fördela ansvar mellan flera specialiserade agenter.

RAG kan därför integreras i exempelvis Test Design Agent, som kan söka efter tidigare testfall eller tidigare krav innan nya testfall skapas.

## 2.11 AI Agent

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

I detta projekt är en agent en specialiserad komponent i QA-arbetsflödet. Varje agent har ett tydligt ansvar, exempelvis kravanalys, testdesign, testgenerering eller granskning.

## 2.12 Agentic AI

Agentic AI beskriver AI-system som inte bara genererar svar, utan också kan agera mot mål över flera steg. Det innebär att systemet kan planera, välja verktyg, utföra handlingar, utvärdera resultat och eventuellt iterera.

Agentic AI skiljer sig från vanlig generativ AI genom graden av handlingsförmåga. En generativ AI-modell kan skriva ett testfall. Ett agentiskt system kan analysera krav, besluta vilka tester som behövs, skapa testfall, kontrollera täckning och begära förbättring om täckningen är otillräcklig.

I projektet används agentisk AI för att beskriva den övergripande arkitekturen där en orkestrator koordinerar flera specialiserade agenter. Detta är centralt eftersom projektet inte bara handlar om att generera testfall, utan om att undersöka hur ett agentiskt QA-flöde kan stödja kravbaserad testdesign.

## 2.13 Multi-Agent System

Ett Multi-Agent System består av flera agenter som samarbetar eller samordnas för att lösa en uppgift. Varje agent kan ha en särskild roll, specialisering eller uppgift.

I traditionell mjukvaruarkitektur kan man beskriva detta som en uppdelning av ansvar. I ett multi-agent-system förstärks detta genom att varje agent kan använda en LLM och potentiellt fatta egna beslut inom sitt ansvarsområde.

I projektet föreslås följande agenter:

- Orchestrator Agent
- Requirements Analyst Agent
- Test Design Agent
- Test Generation Agent
- Review Agent

Syftet med denna uppdelning är att efterlikna ett QA-arbetsflöde där kravanalys, testdesign, testimplementation och granskning är olika aktiviteter. Multi-agent-arkitekturen gör det också möjligt att använda olika modeller för olika uppgifter.

## 2.14 Orchestrator

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

I projektet är orkestratorn central eftersom handledarfeedbacken pekar på att systemet bör vara agentiskt snarare än en enkel agentkedja.

## 2.15 Agent Memory

Agentminne syftar på information som en agent kan behålla eller återanvända över tid. Det kan vara korttidsminne under en körning eller långtidsminne mellan olika körningar.

Exempel på minne i detta projekt kan vara:

- tidigare krav
- genererade acceptanskriterier
- tidigare testfall
- tidigare granskningskommentarer
- modellval
- kända felmönster
- testdesignbeslut

Minnet kan implementeras på olika sätt, exempelvis som JSON-filer, databasposter, embeddings eller versionshanterade artefakter. För en första prototyp kan filbaserat minne vara tillräckligt.

Agentminne är viktigt för QA eftersom testdesign ofta bygger på tidigare erfarenhet. Ett system som kan återanvända tidigare testmönster kan potentiellt skapa mer konsekventa och relevanta tester.

## 2.16 Planning

Planning innebär att en agent eller orkestrator bryter ner ett mål i delsteg. I ett QA-system kan målet vara att skapa testartefakter från krav. Detta kan delas upp i kravanalys, acceptanskriterier, testdesign, testgenerering och granskning.

Planning är en viktig del av agentiska system eftersom det gör att systemet kan arbeta över flera steg snarare än att bara ge ett direkt svar. I detta projekt kan planeringen ligga hos Orchestrator Agent.

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

## 2.17 Reflection och Review

Reflection innebär att ett AI-system granskar sitt eget eller en annan agents output och försöker identifiera brister. I detta projekt används termen främst i form av en Review Agent.

Review Agent har en viktig QA-roll. Den ska inte primärt skapa nya testfall, utan granska om de artefakter som skapats är tillräckliga. Exempel på granskningsfrågor är:

- Är varje krav täckt av minst ett testfall?
- Finns tydliga acceptanskriterier?
- Finns testorakel?
- Är teststegen exekverbara?
- Finns antaganden dokumenterade?
- Finns risker eller luckor?

Review Agent kan därmed fungera som en kvalitetsgrind mellan agentstegen.

## 2.18 Tool Calling

Tool Calling innebär att en agent kan använda externa verktyg för att utföra handlingar. Det kan exempelvis vara att läsa filer, skriva JSON, söka i dokument, köra tester eller anropa ett API.

Tool Calling är en central skillnad mellan en vanlig LLM och en agent. En LLM kan föreslå ett kommando. En agent med verktygsåtkomst kan potentiellt utföra kommandot.

I detta projekt kan tool calling användas för att:

- läsa kravfiler
- skriva strukturerade krav i JSON
- skapa testfall som filer
- köra testverktyg
- läsa testresultat
- generera rapporter

Detta gör systemet mer integrerat och närmare ett verkligt QA-arbetsflöde.

## 2.19 Function Calling

Function Calling är en specifik form av tool calling där modellen anropar fördefinierade funktioner med strukturerade argument. Det kan exempelvis handla om att modellen returnerar ett JSON-objekt som sedan används för att anropa en funktion i programmet.

Exempel:

```json
{
  "requirement_id": "R1",
  "test_type": "unit",
  "priority": "high"
}
```

Function Calling är särskilt relevant när man vill ha strukturerad output från en LLM. I detta projekt kan det användas för att skapa konsekventa kravobjekt, testdesignobjekt och granskningsresultat.

## 2.20 Model Context Protocol

Model Context Protocol, MCP, är en öppen standard för att koppla AI-applikationer till externa datakällor och verktyg. Syftet är att skapa ett standardiserat sätt för AI-system att få åtkomst till kontext, data och funktioner. ([Anthropic](https://www.anthropic.com/news/model-context-protocol?utm_source=chatgpt.com))

MCP kan beskrivas som ett integrationslager mellan AI-modeller och omgivande system. Istället för att varje agentramverk bygger egna speciallösningar för filsystem, databaser, GitHub, testverktyg eller dokumenthantering kan MCP ge ett gemensamt protokoll.

I detta projekt är MCP relevant som ett möjligt framtida integrationsmönster. För en första prototyp är det inte säkert att MCP behöver implementeras, men begreppet är viktigt eftersom moderna agentplattformar allt oftare använder standardiserade verktygsintegrationer.

## 2.21 Software Engineering

Software Engineering avser systematisk utveckling, drift och underhåll av mjukvarusystem. Det omfattar kravhantering, design, implementation, testning, deployment, underhåll och kvalitetssäkring.

Detta projekt är placerat inom software engineering eftersom det undersöker hur AI-agenter kan stödja ett konkret mjukvaruutvecklingsflöde: från krav till testartefakter.

Projektets fokus ligger inte på AI som fristående teknik, utan på hur AI kan integreras i en mjukvaruprocess.

## 2.22 AI for Software Engineering

AI for Software Engineering innebär användning av AI-tekniker för att stödja mjukvaruutveckling. Exempel är kodgenerering, kravanalys, testgenerering, felsökning, refaktorering, dokumentation och kodgranskning.

LLM-baserade agenter har blivit särskilt intressanta inom software engineering eftersom de kan kombinera språkförståelse, kodgenerering och verktygsanvändning. En aktuell survey beskriver hur LLM-baserade agenter används inom software engineering och hur flera agenter och mänsklig interaktion kan bidra till att hantera komplexa problem. ([arXiv](https://arxiv.org/abs/2409.02977?utm_source=chatgpt.com))

I detta projekt fokuseras AI for Software Engineering på QA och testrelaterade aktiviteter snarare än generell kodproduktion.

## 2.23 Agentic Software Engineering

Agentic Software Engineering innebär att agentiska AI-system används för att stödja eller automatisera delar av mjukvaruutvecklingsprocessen. Skillnaden mot enklare AI-assistenter är att agentiska system kan arbeta över flera steg, använda verktyg och samordna flera specialiserade roller.

Exempel på agentiska software engineering-flöden är:

- krav till kod
- krav till testfall
- buggrapport till fix
- kod till testsvit
- testresultat till kodreparation
- Pull Request-granskning

I detta projekt används agentic software engineering för att skapa ett QA-orienterat arbetsflöde där agenter transformerar krav till testdesign och testartefakter.

## 2.24 Software Quality Assurance

Software Quality Assurance, QA, omfattar processer, metoder och aktiviteter som syftar till att säkerställa mjukvarukvalitet. QA handlar inte bara om att hitta fel genom testning, utan även om att bygga kvalitet genom kravhantering, granskning, processkontroll, spårbarhet och förbättring.

I detta projekt är QA-perspektivet centralt. Målet är inte bara att generera kod eller tester, utan att undersöka hur agentiska system kan stödja ett kvalitetssäkrat arbetsflöde.

Viktiga QA-aspekter i projektet är:

- kravtäckning
- testdesign
- spårbarhet
- testorakel
- review-loopar
- mätbar kvalitet
- iterationscykler

## 2.25 Verification and Validation

Verification and Validation, ofta förkortat V&V, är centrala begrepp inom kvalitetssäkring.

- **Verification** handlar om att kontrollera att systemet byggs korrekt enligt specifikation.
- **Validation** handlar om att kontrollera att rätt system byggs utifrån användarens behov.

I projektets kontext kan verification kopplas till att genererade tester spåras mot krav och att testartefakter följer specificerade format. Validation är svårare, eftersom den kräver förståelse för om kraven faktiskt motsvarar verkliga behov.

Ett agentiskt QA-system kan potentiellt stödja både verification och validation, men den första prototypen bör främst fokusera på verification.

## 2.26 Requirement

Ett krav beskriver en egenskap, funktion, begränsning eller kvalitet som ett system ska uppfylla. Krav kan vara funktionella eller icke-funktionella.

Exempel på funktionellt krav:

```text
Systemet ska kunna visa ett skämt från ett externt API.
```

Exempel på icke-funktionellt krav:

```text
Systemet ska visa svar inom två sekunder.
```

I projektet är krav den huvudsakliga inputen till agentflödet. Requirements Analyst Agent ska bryta ner kravtext till strukturerade krav med ID, beskrivning, aktör, handling, villkor och acceptanskriterier.

## 2.27 Acceptance Criteria

Acceptanskriterier beskriver under vilka villkor ett krav anses vara uppfyllt. De gör kravet mer testbart och fungerar som brygga mellan krav och testdesign.

Exempel:

```text
Krav: Användaren ska kunna hämta ett nytt skämt.

Acceptanskriterier:
- När användaren klickar på knappen "New joke" ska ett nytt API-anrop skickas.
- När API-anropet lyckas ska ett nytt skämt visas.
- Om API-anropet misslyckas ska ett felmeddelande visas.
```

I projektet är acceptanskriterier centrala eftersom Test Design Agent använder dem för att skapa testfall.

## 2.28 Requirement Traceability

Requirement Traceability innebär att krav kan kopplas till andra artefakter, exempelvis acceptanskriterier, testfall, kod eller buggrapporter. Spårbarhet är viktigt för att kunna visa att varje krav har verifierats.

I projektet används spårbarhet för att mäta kravtäckning. Varje genererat testfall bör referera till ett eller flera krav-ID.

Exempel:

| Krav-ID | Testfall | Testtyp |
|---|---|---|
| R1 | TC-001 | Enhetstest |
| R2 | TC-002 | GUI-test |
| R3 | TC-003 | E2E-test |

Spårbarhet är också viktigt för Review Agent, som kan identifiera krav utan testtäckning.

## 2.29 Test Design

Testdesign är processen att utforma testfall baserat på krav, risker, systembeteende och acceptanskriterier. Testdesign handlar inte bara om att skriva testkod, utan om att bestämma vad som ska testas, varför det ska testas och hur testet ska avgöra om resultatet är korrekt.

I projektet är Test Design Agent ansvarig för att skapa en testdesign som innehåller:

- testtyp
- testsyfte
- teststeg
- testdata
- testorakel
- koppling till krav
- risker och antaganden

Testdesign är en central QA-aktivitet och bör särskiljas från testgenerering. Testdesign beskriver vad som ska testas. Testgenerering skapar de konkreta testartefakterna.

## 2.30 Test Oracle

Ett testorakel avgör om ett testresultat är korrekt eller felaktigt. Utan ett testorakel kan ett test exekveras, men det går inte att veta om resultatet är rätt.

Exempel:

```text
Om API:et returnerar status 200 och ett fält "value", ska texten i "value" visas i användargränssnittet.
```

Detta är ett testorakel eftersom det anger förväntat beteende.

I AI-genererad testdesign är testorakel särskilt viktigt. Ett vanligt problem är att modeller genererar teststeg utan tydliga förväntade resultat. Därför bör Test Design Agent alltid tvingas ange testorakel.

## 2.31 Unit Test

Ett enhetstest testar en liten isolerad del av systemet, exempelvis en funktion, klass eller komponent. Enhetstester är ofta snabba och används för att verifiera logik på låg nivå.

I projektet kan enhetstester användas för att testa exempelvis:

- parsning av API-svar
- hantering av fel
- transformationslogik
- validering av input

Enhetstester är särskilt viktiga i ett TDD-flöde eftersom de kan skapas tidigt och användas för att styra implementation.

## 2.32 Integration Test

Ett integrationstest verifierar att flera komponenter fungerar tillsammans. Exempelvis kan ett integrationstest kontrollera att en backend-komponent korrekt anropar ett externt API och hanterar svaret.

I projektet kan integrationstester bli relevanta om demonstratorn innehåller både frontend, backend och extern API-koppling.

## 2.33 GUI Test

Ett GUI-test testar systemet genom det grafiska användargränssnittet. Det kan exempelvis kontrollera att knappar, textfält och felmeddelanden fungerar som förväntat.

I projektet är GUI-testning relevant eftersom genererade tester ska kunna verifiera användarens synliga interaktion med en webbapplikation.

GUI-tester kräver ofta selektorer, exempelvis:

```text
#new-joke-button
#joke-text
#error-message
```

Därför behöver Test Design Agent definiera selektorer som senare implementationen måste följa.

## 2.34 End-to-End Test

Ett End-to-End-test, E2E-test, testar ett systemflöde från användarens perspektiv genom flera lager av systemet. Ett E2E-test kan exempelvis öppna webbsidan, klicka på en knapp, vänta på ett API-svar och kontrollera att resultatet visas.

E2E-tester är ofta mer realistiska än enhetstester men också långsammare och mer känsliga för miljöproblem.

I projektet kan E2E-tester användas för att verifiera att hela flödet från krav till fungerande användarinteraktion är korrekt.

## 2.35 Test Automation

Testautomation innebär att tester exekveras automatiskt av verktyg istället för manuellt av en människa. Testautomation är centralt i moderna CI/CD-flöden.

I projektet är testautomation relevant på två nivåer:

1. Agenterna genererar testartefakter automatiskt.
2. De genererade testerna kan köras automatiskt för att verifiera systemet.

Detta gör att projektet ligger nära både AI-assisterad testdesign och automatiserad QA.

## 2.36 Test-Driven Development

Test-Driven Development, TDD, är en utvecklingsmetodik där tester skrivs före produktionskoden. Ett klassiskt TDD-flöde beskrivs ofta som:

```text
Red -> Green -> Refactor
```

Det betyder:

- skriv ett test som först misslyckas
- implementera minsta möjliga kod för att testet ska passera
- förbättra koden utan att ändra beteendet

I detta projekt används TDD som designprincip. Test Design Agent och Test Generation Agent skapar testdesign och testfall innan eventuell implementation sker. Implementation Agent eller motsvarande komponent kan sedan skapa eller modifiera kod tills testerna passerar.

## 2.37 Self-Healing

Self-healing innebär att ett system automatiskt upptäcker fel, analyserar orsaken och försöker korrigera problemet. I kontexten av agentisk mjukvaruutveckling kan self-healing innebära att en agent kör tester, läser felmeddelanden, modifierar kod eller testartefakter och kör tester igen.

I projektet kan self-healing beskrivas som en iterativ feedback-loop:

```text
Generera artefakt
  -> Granska eller testa
  -> Identifiera fel
  -> Förbättra artefakt
  -> Kör igen
```

Self-healing är inte samma sak som att systemet alltid hittar rätt lösning. Det innebär snarare att systemet har en mekanism för att iterera baserat på feedback.

## 2.38 Code Coverage

Code Coverage, eller kodtäckning, mäter hur stor del av koden som exekveras av testerna. Vanliga typer av täckning är:

- radtäckning
- funktions- eller metodtäckning
- grentäckning

Kodtäckning är ett användbart men begränsat mått. Hög kodtäckning betyder inte nödvändigtvis att testerna är bra. Tester kan exekvera kod utan att kontrollera rätt beteende.

I projektet kan kodtäckning användas som ett kompletterande mått, men bör inte vara det enda måttet på testkvalitet.

## 2.39 Requirement Coverage

Requirement Coverage mäter hur stor andel krav som täcks av testfall. Detta är särskilt relevant för projektet eftersom målet är kravbaserad testdesign.

Exempel:

```text
Antal krav med minst ett testfall / Totalt antal krav
```

Om 8 av 10 krav har minst ett kopplat testfall är kravtäckningen 80 %.

Kravtäckning är centralt för Review Agent, som kan identifiera krav utan testfall eller krav med otillräcklig testdesign.

## 2.40 Test Pass Rate

Test Pass Rate mäter andelen tester som passerar vid exekvering.

Exempel:

```text
Antal passerade tester / Totalt antal tester
```

Detta är ett enkelt men viktigt mått. I ett self-healing-flöde kan Test Pass Rate användas för att avgöra om systemet behöver iterera.

## 2.41 Iterationscykler

Iterationscykler mäter hur många gånger systemet behöver gå igenom en gransknings- eller reparationsloop innan resultatet godkänns.

I projektet är detta ett särskilt intressant mått eftersom det fångar hur effektivt det agentiska systemet är. Om ett system kräver många iterationer kan det tyda på bristande promptar, svag modell, dålig testdesign eller otydlig kravstruktur.

## 2.42 Exekveringstid

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

## 2.43 Code Quality

Code Quality, eller kodkvalitet, avser egenskaper som påverkar hur lätt kod är att förstå, underhålla, testa och vidareutveckla. Exempel på kodkvalitetsmått är:

- komplexitet
- duplicering
- kodlukt
- maintainability
- security issues
- reliability issues

I projektet kan kodkvalitet användas om systemet även genererar kod eller testkod. För Python kan verktyg som ruff, pylint och radon användas. För bredare analys kan SonarQube vara relevant.

## 2.44 SonarQube

SonarQube är ett verktyg för statisk kodanalys. Det kan analysera kodkvalitet, säkerhetsproblem, duplicering, kodlukt och ibland testtäckning beroende på konfiguration.

I projektet kan SonarQube användas som ett möjligt verktyg för att mäta kvaliteten på genererad kod eller genererade tester. För en första prototyp kan enklare verktyg som linting och coverage vara tillräckliga, men SonarQube är relevant som industriellt etablerat verktyg.

## 2.45 Agent Framework

Ett agentramverk är ett bibliotek eller en plattform för att skapa, konfigurera och köra AI-agenter. Agentramverk erbjuder ofta stöd för roller, verktygsanrop, minne, orkestrering, kommunikation mellan agenter och integration med olika LLM:er.

Exempel på agentramverk eller agentplattformar är:

- CrewAI
- LangGraph
- AutoGen
- OpenAI Agents SDK
- OpenClaw
- Hermes Agent Framework

I projektet är valet av agentramverk en central del av litteraturstudien och prototypen. Ett viktigt mål är att förstå vilka ramverk som passar bäst för QA-arbetsflöden där krav, testdesign, testgenerering och granskning behöver samordnas.

## 2.46 Modellagnostisk arkitektur

En modellagnostisk arkitektur innebär att systemet inte är hårt bundet till en specifik LLM. Istället kan olika modeller användas beroende på uppgift, kostnad, tillgänglighet och kvalitet.

Exempel:

```yaml
requirements_model: qwen
test_design_model: deepseek
test_generation_model: gpt
review_model: claude
```

Detta är viktigt i projektet eftersom olika agenter kan ha olika behov. Kravanalys kan kanske utföras av en lokal modell, medan testgenerering kan kräva en starkare kodmodell.

## 2.47 Lokala och molnbaserade modeller

Lokala modeller körs på egen hårdvara eller i egen miljö, ofta via verktyg som Ollama. Molnbaserade modeller körs via API:er från exempelvis OpenAI, Anthropic, Google eller Hugging Face.

Lokala modeller kan ge bättre kontroll, lägre marginalkostnad och potentiellt bättre datasekretess. Molnbaserade modeller kan ge högre kvalitet, bättre kodförmåga och enklare drift.

I projektet är det relevant att stödja båda alternativen. Det gör prototypen mer flexibel och gör det möjligt att jämföra olika modellval.

## 2.48 Ollama

Ollama är ett verktyg för att köra lokala språkmodeller. Det används ofta tillsammans med modeller som Llama, Qwen, Mistral, DeepSeek och Hermes.

I projektet kan Ollama användas om agenterna ska kunna köras med lokala modeller. Detta gör det möjligt att testa hur långt man kan komma utan kommersiella API:er.

## 2.49 Hugging Face

Hugging Face är en plattform för AI-modeller, datasets och applikationer. Hugging Face Spaces kan användas för att publicera enkla AI-demonstratorer och webbaserade gränssnitt.

I projektet är Hugging Face relevant på två sätt:

1. som möjlig källa till modeller och API:er
2. som hostingmiljö för demonstratorn

Eftersom projektet redan har erfarenhet från en tidigare RAG-prototyp på Hugging Face är det ett naturligt alternativ för den första demonstratorn.

## 2.50 GitHub och GitHub Pages

GitHub används för versionshantering, källkod och dokumentation. GitHub Pages används för att publicera projektets kunskapsbas som en öppen webbsida.

I detta projekt fyller GitHub två roller:

- teknisk versionshantering av kod och dokument
- publik dokumentationsyta för kunskapsbasen

GitHub Pages gör att litteraturstudien och kunskapsbasen kan publiceras löpande och göras tillgänglig för handledare, kollegor och framtida läsare.

## 2.51 Continuous Integration

Continuous Integration, CI, innebär att kod och tester körs automatiskt när ändringar görs i ett repository. CI kan användas för att bygga, testa och deploya mjukvara.

I projektet kan CI användas för att:

- köra genererade tester
- mäta testresultat
- beräkna kodtäckning
- deploya demonstratorn
- publicera dokumentation

GitHub Actions är ett vanligt verktyg för CI i GitHub-baserade projekt.

## 2.52 Demonstrator

En demonstrator är en prototyp som visar att en idé är tekniskt möjlig. Den behöver inte vara produktionsklar, men ska vara tillräckligt konkret för att kunna användas i utvärdering.

I projektet är demonstratorn ett webbaserat system där användaren skickar in krav och får ut testartefakter. Demonstratorn används för att undersöka om den föreslagna agentarkitekturen är praktiskt genomförbar.

## 2.53 Artefakt

En artefakt är ett konkret resultat som produceras i en utvecklings- eller QA-process. I detta projekt kan artefakter vara:

- strukturerade krav
- acceptanskriterier
- testdesign
- testfall
- testdata
- selektorer
- rapporter
- kodfiler

Agentflödet kan beskrivas som en process där varje agent producerar eller granskar artefakter.

## 2.54 Sammanfattning

Detta kapitel har introducerat de centrala begrepp som projektet bygger på. Den viktigaste distinktionen är skillnaden mellan en LLM, en AI-agent och ett agentiskt multi-agent-system.

En LLM är en modell som genererar text eller kod. En AI-agent använder en LLM tillsammans med instruktioner, verktyg och mål. Ett multi-agent-system består av flera specialiserade agenter som samordnas, ofta av en orkestrator.

För detta projekt är den centrala idén att använda agentisk AI för att stödja QA-arbetsflöden. Fokus ligger på att transformera krav till testdesign och testartefakter med spårbarhet, granskning och möjlighet till iteration.
---

# 3. Litteraturstudie

Detta kapitel kommer att sammanfatta aktuell forskning inom:

- AI Agents
- Multi-Agent Systems
- Agentic Software Engineering
- AI-assisterad testning
- Software Quality Assurance
- Verification & Validation

Varje forskningsarbete kommer att analyseras utifrån:

- Syfte
- Metod
- Resultat
- Relevans för projektet

---

# 4. Agentramverk

Jämförelse av aktuella agentramverk och deras lämplighet för QA.

---

# 5. Systemarkitektur

Beskrivning av den föreslagna arkitekturen.

- Orchestrator Agent
- Requirements Analyst Agent
- Test Design Agent
- Test Generation Agent
- Review Agent

---

# 6. Designbeslut

Motivering av arkitektur- och teknikval.

---

# 7. Prototyp och implementation

Beskrivning av implementationen.

---

# 8. Experiment och utvärdering

Föreslagna utvärderingsmått:

- Kravtäckning
- Kodtäckning
- Test Pass Rate
- Exekveringstid
- Antal iterationscykler
- Kodkvalitet

---

# 9. Framtida arbete

Identifierade förbättringar och fortsatta forskningsmöjligheter.

---

# 10. Forskningsartiklar

Detta kapitel kommer att innehålla en sammanställning av relevanta forskningsartiklar och rapporter.

---

# 11. Referenser

Referenslista enligt vald referensstandard (preliminärt IEEE).