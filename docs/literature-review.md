## Litteraturstudie om AI-agenter för Software Quality Assurance

> **Status:** Under utveckling (Version 0.3)  
> **Språk:** Svenska  
> **Senast uppdaterad:** 2026-07-05

---

## Om dokumentet

Detta dokument utgör litteraturstudien för projektet **AI-agenter för Software Quality Assurance**.

Syftet med litteraturstudien är att skapa en grundläggande förståelse för AI-agenter, agentiska system och deras användning inom Software Engineering och Software Quality Assurance. Resultatet används som kunskapsunderlag inför den fortsatta utvecklingen av projektets forskningsprototyp.

---

## Användning av AI

Denna litteraturstudie utvecklas i samarbete mellan författaren och generativ AI.

AI används som stöd för:

- identifiering av relevanta forskningsartiklar
- sammanfattning av forskningsresultat
- strukturering av litteraturstudien
- begreppsförklaringar
- språkgranskning

Samtliga sammanfattningar och slutsatser granskas och verifieras innan de inkluderas i dokumentet.

---

## Innehåll

1. Introduktion
2. Metod
3. Genomgång av forskningsartiklar
4. Referenser

---

## 1. Introduktion

Utvecklingen av generativ AI och stora språkmodeller (Large Language Models, LLM) har under de senaste åren förändrat hur mjukvaruutveckling bedrivs. Från att initialt ha använts som intelligenta kodassistenter har forskningen successivt utvecklats mot agentiska AI-system där flera specialiserade AI-agenter samarbetar för att lösa komplexa uppgifter genom hela mjukvaruutvecklingsprocessen.

Parallellt har Software Quality Assurance (QA) blivit ett område där AI förväntas kunna bidra med förbättrad kravanalys, testdesign, testgenerering och kvalitetssäkring. Trots den snabba utvecklingen är forskningsområdet fortfarande ungt och flera frågor kring arkitektur, samarbete mellan agenter och kvalitetssäkring återstår att besvara.

Syftet med denna litteraturstudie är därför att skapa en översikt över aktuell forskning inom området och identifiera vilka idéer, arkitekturer och arbetssätt som är relevanta för utvecklingen av agentiska QA-system.

---

## 2. Metod

Denna studie är en riktad litteraturstudie.

Syftet har inte varit att genomföra en fullständig systematisk litteraturöversikt, utan att identifiera ett begränsat antal forskningsartiklar som tillsammans ger en god förståelse för forskningsområdet.

Urvalet har fokuserat på tre typer av publikationer:

- översiktsartiklar
- forskningsartiklar om agentiska system
- forskningsartiklar inom AI-assisterad Software Quality Assurance

Tyngdpunkten ligger på publikationer från **2023–2026**, då utvecklingen inom Agentic AI varit särskilt snabb.

---

## 3. Genomgång av forskningsartiklar

Följande forskningsartiklar utgör grunden för litteraturstudien.

---

## Översiktsartiklar

Dessa artiklar utgör grunden för litteraturstudien och bör läsas först.

| Nr | Artikel | År | Kort beskrivning | Länk |
|---:|----------|----|------------------|------|
| 1 | **Large Language Model-Based Agents for Software Engineering: A Survey** | 2024 | Den viktigaste översiktsartikeln inom området. Beskriver LLM-baserade agenter, agentkomponenter, multi-agent-system och forskningsläget inom Software Engineering. | https://arxiv.org/abs/2409.02977 |
| 2 | **Agents in Software Engineering: Survey, Landscape and Vision** | 2025 | Kompletterar den första surveyartikeln och presenterar ramverket Perception–Memory–Action samt forskningslandskapet för AI-agenter inom Software Engineering. | https://arxiv.org/abs/2409.09030 |
| 3 | **The Rise of Agentic Testing: Multi-Agent Systems for Robust Software Quality Assurance** | 2026 | Beskriver hur flera AI-agenter samarbetar för att generera, exekvera, analysera och förbättra tester i en iterativ QA-process. | https://arxiv.org/abs/2601.02454 |
| 4 | **AgentCoder: Multi-Agent-based Code Generation with Iterative Testing and Optimisation** | 2023 | Ett av de mest inflytelserika arbetena kring agentisk mjukvaruutveckling där flera specialiserade agenter samarbetar genom återkopplingsloopar. | https://arxiv.org/abs/2312.13010 |
| 5 | **Automatic High-Level Test Case Generation using Large Language Models** | 2025 | Visar hur stora språkmodeller kan generera hög-nivå testfall direkt från krav och use cases. Mycket nära projektets fokus på kravbaserad testdesign. | https://arxiv.org/abs/2503.17998 |

---

## Forskningsartiklar

Dessa artiklar ger en djupare förståelse för olika agentarkitekturer och moderna arbetssätt.

| Nr | Artikel | År | Kort beskrivning | Länk |
|---:|----------|----|------------------|------|
| 6 | **MetaGPT: Meta Programming for Multi-Agent Collaborative Framework** | 2023 | Beskriver ett rollbaserat multi-agent-system där olika AI-agenter motsvarar klassiska roller inom mjukvaruutveckling, exempelvis Product Manager, Architect, Engineer och QA. | https://arxiv.org/abs/2308.00352 |
| 7 | **SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering** | 2024 | Visar hur AI-agenter kan arbeta direkt mot verkliga kodbaser, terminaler, Git-repositorier och utvecklingsverktyg. | https://arxiv.org/abs/2405.15793 |

---

## Sammanfattning

Denna läslista består av totalt **sju utvalda forskningsartiklar**.

Urvalet bedöms ge en god balans mellan:

- grundläggande teori om AI-agenter,
- moderna agentarkitekturer,
- Agentic Software Engineering,
- Software Quality Assurance,
- kravanalys,
- testdesign,
- testgenerering.

Målet är inte att ge en fullständig översikt över forskningsområdet, utan att skapa ett tillräckligt kunskapsunderlag för att förstå området och motivera de designval som senare görs i projektets forskningsprototyp.


## 3.1 Publikation 1: Large Language Model-Based Agents for Software Engineering: A Survey (2024)

Denna översiktsartikel ger en omfattande genomgång av forskningsområdet kring LLM-baserade AI-agenter inom Software Engineering. Författarna analyserar 124 vetenskapliga publikationer och sammanställer hur AI-agenter används genom olika delar av mjukvaruutvecklingsprocessen, exempelvis kravhantering, design, kodgenerering, testning, kodgranskning och underhåll. Syftet är att kartlägga forskningsläget, identifiera gemensamma arkitekturmönster och peka ut områden där ytterligare forskning behövs.

Artikeln visar att utvecklingen av AI-agenter har gått från enkla språkmodeller till mer avancerade agentiska system som kombinerar planering, minne, verktygsanvändning och återkopplingsloopar. Samtidigt konstateras att de flesta lösningar fortfarande befinner sig på forsknings- eller prototypnivå och att det saknas etablerade arkitekturer för många tillämpningsområden.

En viktig slutsats är att användningen av AI-agenter ökar inom hela Software Engineering, men att forskningen är ojämnt fördelad. Områden som kodgenerering och programmeringsassistans dominerar, medan exempelvis Software Quality Assurance, kravdriven testdesign och verifiering fortfarande är betydligt mindre utforskade. Författarna identifierar därför dessa områden som lovande riktningar för framtida forskning.

Betydelse för denna studie

Denna artikel fungerar främst som en översikt över forskningsområdet och ger en bred förståelse för hur AI-agenter används inom Software Engineering. Till skillnad från senare artiklar presenterar den ingen specifik agentarkitektur, utan sammanfattar det aktuella forskningsläget och identifierar återkommande designprinciper och forskningsluckor. För denna studie är artikeln viktig eftersom den motiverar varför agentiska QA-system är ett relevant forskningsområde och visar att det fortfarande finns begränsad forskning kring AI-agenter för kravanalys, testdesign och Software Quality Assurance.

---

## 3.2 Publikation 2: Agents in Software Engineering: Survey, Landscape and Vision (2025)

Denna översiktsartikel syftar till att skapa en gemensam förståelse för vad en AI-agent är inom Software Engineering och hur moderna agentiska system kan beskrivas med ett enhetligt ramverk. Författarna konstaterar att begreppet AI-agent används på många olika sätt i litteraturen – från enkla språkmodeller med en prompt till avancerade system med planering, minne, verktygsanvändning och flera samverkande agenter. Artikelns främsta bidrag är därför en konceptuell modell som beskriver de centrala komponenterna i en modern AI-agent.

Författarna identifierar fyra grundläggande pelare som tillsammans beskriver agentens funktionalitet: Perception, Reasoning, Action och Evolution. Perception handlar om agentens förmåga att uppfatta och tolka information från omgivningen, exempelvis kravspecifikationer, källkod, testresultat eller användarinstruktioner. Reasoning beskriver hur agenten analyserar informationen, drar slutsatser och fattar beslut med hjälp av språkmodellen. Action omfattar agentens förmåga att utföra konkreta handlingar, såsom att generera kod, skapa testfall, uppdatera filer eller använda externa verktyg. Den fjärde pelaren, Evolution, beskriver hur agenten successivt kan förbättra sitt beteende genom återkoppling, erfarenheter, reflektion och iterationer.

Artikeln lyfter även fram minne som en central komponent i agentarkitekturen. Författarna skiljer mellan flera olika typer av minne. Short-Term Memory används för att hålla aktuell kontext under en pågående uppgift, medan Long-Term Memory lagrar mer permanent kunskap, exempelvis tidigare erfarenheter, domänkunskap eller historiska lösningar. Working Memory används för att dela information mellan flera samverkande agenter under samma körning och möjliggör därmed ett gemensamt arbetsflöde. Slutligen beskriver artikeln även External Memory, där agenten hämtar information från externa kunskapskällor såsom RAG-lösningar, vektordatabaser, Git-repositorier eller dokumenthanteringssystem.

En annan viktig slutsats är att moderna agentiska system i allt större utsträckning bygger på specialiserade agentroller snarare än en enda generell agent. Genom att dela upp arbetet mellan exempelvis en Requirements Agent, en Test Design Agent och en Review Agent kan varje agent fokusera på en avgränsad uppgift, vilket förbättrar både kvalitet, spårbarhet och möjligheten till återkoppling. Artikeln visar även att en orkestrator ofta används för att koordinera samarbetet mellan agenterna och styra arbetsflödet.

För denna studie är artikeln särskilt relevant eftersom den ger en tydlig teoretisk modell för hur agentiska system kan byggas upp. De fyra pelarna och den beskrivna minnesarkitekturen utgör ett användbart ramverk för att analysera och jämföra olika agentlösningar. Samtidigt ligger artikelns beskrivning nära den agentarkitektur som senare används i projektets forskningsprototyp, där specialiserade QA-agenter samverkar under ledning av en orkestrator och delar information genom ett gemensamt arbetsminne. Denna artikel utgör en av de viktigaste teoretiska referenserna i litteraturstudien.

---

## 3.3 Publikation 3: The Rise of Agentic Testing: Multi-Agent Systems for Robust Software Quality Assurance (2026)

Denna artikel undersöker hur agentiska AI-system kan användas för att automatisera och förbättra Software Quality Assurance. Till skillnad från traditionella AI-lösningar, där en enskild språkmodell används för att generera testfall eller besvara frågor, förespråkar författarna en multi-agentarkitektur där flera specialiserade agenter samarbetar genom hela testprocessen. Syftet är att skapa ett mer robust, spårbart och iterativt arbetssätt där olika agentroller ansvarar för olika delar av testprocessen.

Artikeln presenterar en referensarkitektur bestående av flera samverkande agenter. En Test Generation Agent ansvarar för att analysera krav och generera testfall, en Execution Agent kör testerna och samlar in resultat, medan en Review Agent analyserar utfallet och identifierar brister eller förbättringsmöjligheter. Resultatet används därefter som återkoppling till tidigare steg, vilket skapar en iterativ förbättringsprocess där testfallen successivt kan förfinas.

En central idé i artikeln är att testning inte längre bör ses som ett linjärt arbetsflöde utan som en kontinuerlig återkopplingsloop. Genom att kombinera testgenerering, exekvering och granskning kan systemet identifiera brister i testfallen och automatiskt initiera nya iterationer. Författarna menar att detta leder till bättre testkvalitet, högre kravtäckning och mer robusta testsviter än om varje steg utförs isolerat.

Artikeln diskuterar även flera utmaningar med agentisk testning. Eftersom flera agenter samarbetar blir koordination, kommunikation och spårbarhet viktiga aspekter. Författarna betonar därför behovet av en orkestrator som ansvarar för att styra arbetsflödet, överföra information mellan agenterna och avgöra när en ny iteration ska genomföras eller när processen kan avslutas. De lyfter också fram vikten av gemensamt minne och tydliga granskningsmekanismer för att minska risken för felaktiga eller hallucinatoriska resultat.

För denna studie är artikeln särskilt relevant eftersom den beskriver en agentarkitektur som ligger nära projektets övergripande idé. Även om den föreslagna lösningen främst fokuserar på testgenerering och testexekvering, medan den planerade forskningsprototypen utgår från kravanalys och testdesign, bygger båda lösningarna på samma grundprinciper: specialiserade agentroller, en central orkestrator och iterativa återkopplingsloopar. Artikeln visar också att Review Agenten har en central roll i att förbättra kvaliteten på de genererade testartefakterna, vilket stärker idén om att kvalitetsgranskning bör vara en egen agentfunktion och inte endast ett avslutande steg i processen.

Betydelse för denna studie

En viktig lärdom från artikeln är att fler agenter inte automatiskt leder till bättre resultat. Varje ny agent ökar komplexiteten genom fler överlämningar, mer kommunikation och större krav på orkestrering. Samtidigt visar artikeln att vissa agentroller tillför ett tydligt mervärde och därför är motiverade.

En sådan roll är Review Agent. På samma sätt som en person sällan upptäcker alla fel i sitt eget arbete finns det en risk att en agent inte identifierar brister i sina egna resultat. En oberoende granskningsagent kan därför analysera det producerade materialet, kontrollera kvalitet, spårbarhet och täckning samt ge återkoppling innan resultatet skickas vidare eller godkänns. Analogt kan detta liknas vid att inte rätta sitt eget matematikprov, utan låta någon annan göra en oberoende granskning.

Detta resonemang ger ett tydligt stöd för att använda en separat Review Agent i ett agentiskt QA-system, samtidigt som det talar emot att dela upp arbetsflödet i ett alltför stort antal specialiserade agenter. En välbalanserad agentarkitektur bör därför innehålla så få agenter som möjligt, men så många som behövs för att säkerställa kvalitet och spårbarhet.

---

## 3.4 Publikation 4: AgentCoder: Multi-Agent-based Code Generation with Iterative Testing and Optimisation (2023)

AgentCoder presenterar ett multi-agentramverk för automatisk kodgenerering med hjälp av stora språkmodeller. Till skillnad från traditionella lösningar, där en enskild modell ansvarar för både kodgenerering och testning, bygger AgentCoder på tre specialiserade agentroller: en Programmer Agent, som genererar programkoden, en Test Designer Agent, som självständigt konstruerar testfall utifrån problemformuleringen, samt en Test Executor Agent, som exekverar testerna och återkopplar resultatet till de övriga agenterna.

En central idé i artikeln är att separera kodgenerering och testdesign. Genom att låta en oberoende agent skapa testfallen minskar risken att samma resonemang eller felaktiga antaganden återkommer i både koden och testerna. Detta ökar sannolikheten att logiska fel, gränsfall och andra brister upptäcks innan lösningen accepteras.

Agenterna arbetar iterativt genom en återkopplingsloop där resultaten från testexekveringen används för att förbättra den genererade koden. Om tester misslyckas får Programmer Agent återkoppling och kan generera en förbättrad version av lösningen. Processen upprepas tills testerna passerar eller ett fördefinierat stoppvillkor uppnås.

Experimenten visar att AgentCoder uppnår bättre resultat än flera tidigare metoder för automatisk kodgenerering. Författarna visar att kombinationen av specialiserade agentroller och iterativ återkoppling både förbättrar kodkvaliteten och minskar behovet av beräkningsresurser jämfört med flera alternativa lösningar.

Betydelse för denna studie

AgentCoder är särskilt relevant eftersom den visar hur specialiserade AI-agenter kan samarbeta för att lösa en komplex mjukvaruutvecklingsuppgift. Även om ramverket fokuserar på kodgenerering snarare än Software Quality Assurance, är flera av dess grundprinciper direkt överförbara till denna studie. Framför allt betonar artikeln värdet av tydliga agentroller, oberoende testdesign och iterativa återkopplingsloopar. Dessa principer ligger nära den planerade QA-arkitekturen där en orkestrator samordnar specialiserade agenter för kravanalys, testdesign och kvalitetsgranskning.

För denna studie har AgentCoder haft stor betydelse eftersom den visar hur specialiserade agenter kan samverka genom iterativa återkopplingsloopar.
Inte för att vi vill bygga en kodgenerator, utan för att den visar två viktiga principer:

1. Specialisering fungerar. En agent ska ha ett tydligt ansvar istället för att försöka göra allt.
2. Den som producerar ett resultat ska inte ensam verifiera det. En oberoende test- eller granskningsagent ger högre kvalitet.

Både AgentCoder och The Rise of Agentic Testing visar att specialiserade agentroller i kombination med iterativa återkopplingsloopar ger bättre kvalitet och robusthet än en ensam generell agent. Trots att artiklarna fokuserar på olika tillämpningsområden bygger de på samma grundläggande arkitekturprinciper.

---

## 3.5 Publikation 5: Automatic High-Level Test Case Generation using Large Language Models (2025)

Artikeln undersöker hur stora språkmodeller kan användas för att automatiskt generera hög-nivå testfall direkt från kravspecifikationer och användarscenarier. Fokus ligger inte på färdig testkod utan på testdesign, där modellen genererar testfall med beskrivningar av syfte, förutsättningar, teststeg och förväntade resultat. Detta ligger nära hur testdesign vanligtvis utförs av testanalytiker i praktiken.

En central slutsats är att domänkunskap är avgörande för testkvaliteten. Författarna visar att den största utmaningen inte är att generera testfall i sig, utan att förstå verksamhetsdomänen och identifiera vad som faktiskt bör testas. Modeller som har tillgång till relevant domänkontext producerar betydligt mer träffsäkra och användbara testfall än generella modeller utan sådan information.

Artikeln visar också att mindre domänanpassade modeller i vissa fall kan prestera bättre än större generella språkmodeller. Genom finjustering mot ett specifikt problemområde kan en mindre modell generera mer relevanta testfall samtidigt som beräkningskostnaden minskar. Detta visar att modellstorlek inte ensam avgör kvaliteten, utan att träning och domänanpassning har stor betydelse.

För att utvärdera kvaliteten på de genererade testfallen används flera olika metoder. Författarna kombinerar automatiska mått, såsom F1-score, BERTScore och semantiska likhetsmått, med manuell bedömning av erfarna testexperter. Resultaten visar att generativ AI ofta kan producera testfall med hög språklig kvalitet och god täckning av de huvudsakliga funktionella kraven. Samtidigt identifieras flera återkommande svagheter.

Modellerna har exempelvis en tendens att:

* generera alltför generella testfall,
* föreslå irrelevanta eller överflödiga tester,
* missa viktiga gränsfall (edge cases),
* använda otydliga eller ofullständiga testdata,
* ibland skapa testfall som verkar rimliga men saknar praktiskt värde.

Artikeln visar därför att mänsklig granskning fortfarande är viktig, särskilt för att säkerställa att ovanliga scenarier och domänspecifika undantag hanteras korrekt.

Betydelse för denna studie

Denna artikel är den som ligger närmast projektets forskningsfråga. Till skillnad från flera andra publikationer fokuserar den direkt på kravbaserad testdesign, vilket också är utgångspunkten för den utvecklade QA-prototypen. Resultaten visar att generativ AI kan ge ett värdefullt stöd vid framtagning av testfall, men att kvaliteten i hög grad beror på tillgången till domänkunskap och en väl definierad kravspecifikation. Studien visar också att automatiska kvalitetsmått bör kompletteras med expertgranskning, eftersom semantiska likhetsmått inte alltid fångar om testfallen verkligen är användbara eller om viktiga edge cases saknas.
---

## 3.6 Publikation 6: MetaGPT: Meta Programming for Multi-Agent Collaborative Framework (2023)

MetaGPT presenterar ett multi-agentramverk där utvecklingsprocessen modelleras efter hur ett verkligt mjukvaruutvecklingsteam arbetar. I stället för att låta en enda språkmodell utföra alla uppgifter delas arbetet upp mellan flera specialiserade agentroller, exempelvis Product Manager, Architect, Project Manager, Engineer och QA Engineer. Varje agent ansvarar för ett tydligt avgränsat arbetsområde och producerar artefakter som används av efterföljande agenter.

En central idé i MetaGPT är att mjukvaruutveckling kan beskrivas som en kedja av väldefinierade arbetsprodukter. Varje agent arbetar därför mot en specifik artefakt, exempelvis kravspecifikation, systemdesign eller kod, vilket skapar en tydlig struktur och spårbarhet genom hela utvecklingsprocessen.

Artikeln lägger stor vikt vid kommunikation mellan agenter. Författarna visar att fri dialog mellan många agenter snabbt leder till stora mängder text, vilket både ökar kostnaden och försämrar effektiviteten. För att minska detta introduceras principen “Code = SOP (Standard Operating Procedure)”, där kommunikationen standardiseras genom tydliga arbetsflöden och fördefinierade informationsformat. På så sätt överförs endast den information som nästa agent faktiskt behöver.

En annan viktig slutsats är att tokenförbrukningen blir en kritisk faktor i större multi-agentsystem. Om varje agent skickar hela konversationshistoriken vidare till nästa agent uppstår snabbt ett stort informationsbrus. MetaGPT visar därför hur sammanfattningar, strukturerade artefakter och selektiv informationsöverföring kan minska antalet använda tokens utan att försämra resultatet. Detta gör systemet både snabbare och billigare att köra.

Artikeln betonar också vikten av specialisering. Genom att ge varje agent ett tydligt ansvarsområde minskar komplexiteten i varje enskilt steg samtidigt som lösningen blir enklare att förstå, vidareutveckla och felsöka.

Betydelse för denna studie

MetaGPT är särskilt relevant eftersom den visar hur ett större agentiskt system kan organiseras på ett strukturerat och resurssnålt sätt. För denna studie är de viktigaste bidragen inte de specifika agentrollerna utan de arkitekturprinciper som presenteras. Framför allt betonar artikeln vikten av tydliga agentroller, standardiserad kommunikation mellan agenter och att endast överföra den information som är nödvändig för nästa steg. Dessa principer är direkt tillämpbara vid utvecklingen av ett agentiskt QA-system där flera agenter samarbetar kring kravanalys, testdesign och kvalitetsgranskning.

Egna reflektioner

Den viktigaste lärdomen från MetaGPT är att kommunikationen mellan agenter är minst lika viktig som själva agenternas intelligens. Ett väl fungerande multi-agentsystem handlar därför inte bara om att välja rätt språkmodell, utan också om att utforma effektiva informationsflöden. Genom att överföra strukturerade artefakter istället för hela konversationer kan både tokenförbrukning och exekveringstid minskas samtidigt som spårbarheten förbättras. För ett QA-system innebär detta att agenter bör kommunicera genom väldefinierade objekt, exempelvis kravlistor, testdesign eller granskningsrapporter, snarare än genom långa fria dialoger.

---

## 3.7 Publikation 7: SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering (2024)

SWE-agent presenterar ett ramverk där en AI-agent kan arbeta direkt mot en verklig utvecklingsmiljö genom ett Agent-Computer Interface (ACI). Ett ACI fungerar som ett gränssnitt mellan AI-agenten och datorn och ger agenten möjlighet att använda samma verktyg som en mänsklig utvecklare. I stället för att enbart generera text kan agenten exempelvis navigera i ett Git-repository, läsa och redigera filer, använda terminalkommandon, köra tester och analysera resultatet av dessa. Agenten kan därmed utföra en hel arbetsprocess, från att analysera ett problem till att föreslå och verifiera en lösning.

Artikelns huvudsakliga bidrag är introduktionen av Agent-Computer Interface (ACI) som ett strukturerat sätt att låta AI-agenter interagera med sin omgivning. Författarna visar att agentens tillgång till relevanta verktyg ofta är minst lika viktig som valet av språkmodell. En kraftfull språkmodell blir begränsad om den inte kan läsa projektets filer, köra tester eller hämta ytterligare information från utvecklingsmiljön. Ett väl utformat ACI gör det däremot möjligt för agenten att arbeta mer självständigt och att använda externa verktyg som en naturlig del av sitt resonemang.

Betydelse för denna studie

För denna studie är framför allt begreppet Agent-Computer Interface intressant. Även om projektets QA-agenter i första hand fokuserar på kravanalys och testdesign, visar artikeln hur framtida agentiska system skulle kunna integreras med externa verktyg. Exempelvis skulle en QA-agent via ett ACI kunna hämta krav från Jira, läsa dokumentation i Confluence, analysera källkod i ett Git-repository, köra automatiserade tester med Playwright eller Pytest och sammanställa resultaten i en rapport. Artikeln ligger därför något utanför studiens huvudsakliga fokus, men introducerar ett viktigt koncept för hur AI-agenter kan samverka med den omgivande utvecklingsmiljön.

---

## 3.8  Kompletterande Publikationer 

Utöver de artiklar som aktivt har analyserats i litteraturstudien har ytterligare två färska och relevanta arbeten identifierats sent i processen. Dessa behandlar bland annat agentiska arbetssätt och benchmark-baserad utvärdering av testgenerering och testuppdatering. Eftersom de identifierades nära inpå redovisningen har de inte inkluderats i den huvudsakliga analysen, utan placeras som kompletterande läsning.

- Publikation 8: Agentic AI in the Software Development Lifecycle: Architecture, Empirical Evidence, and the Reshaping of Software Engineering (2026)
- Publikation 9: TestEvo-Bench: An Executable and Live Benchmark for Test and Code Co-Evolution

---

## 4. Referenser


1. **Large Language Model-Based Agents for Software Engineering: A Survey (2024)**  
   https://arxiv.org/abs/2409.02977

2. **Agents in Software Engineering: Survey, Landscape and Vision (2025)**  
   https://arxiv.org/abs/2409.09030


3. **The Rise of Agentic Testing: Multi-Agent Systems for Robust Software Quality Assurance (2026)**  
   https://arxiv.org/abs/2601.02454

4. **AgentCoder: Multi-Agent-based Code Generation with Iterative Testing and Optimisation (2023)**  
   https://arxiv.org/abs/2312.13010

5. **Automatic High-Level Test Case Generation using Large Language Models (2025)**  
   https://arxiv.org/abs/2503.17998

6. **MetaGPT: Meta Programming for Multi-Agent Collaborative Framework (2023)**  
   https://arxiv.org/abs/2308.00352

7. **SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering (2024)**  
   https://arxiv.org/abs/2405.15793

8. **Agentic AI in the Software Development Lifecycle: Architecture, Empirical Evidence, and the Reshaping of Software Engineering (2026)**  
   https://arxiv.org/abs/2604.26275

9. **TestEvo-Bench: An Executable and Live Benchmark for Test and Code Co-Evolution**
   https://arxiv.org/abs/2607.02469

---
