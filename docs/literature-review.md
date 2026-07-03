# Litteraturstudie om AI-agenter för Software Quality Assurance

> **Status:** Under utveckling (Version 0.2)  
> **Språk:** Svenska  
> **Senast uppdaterad:** 2026-07-03

---

# Om dokumentet

Detta dokument utgör litteraturstudien för projektet **AI-agenter för Software Quality Assurance**.

Syftet med litteraturstudien är att skapa en grundläggande förståelse för AI-agenter, agentiska system och deras användning inom Software Engineering och Software Quality Assurance. Resultatet används som kunskapsunderlag inför den fortsatta utvecklingen av projektets forskningsprototyp.

Litteraturstudien är **inte** en systematisk litteraturöversikt (SLR), utan en riktad litteraturstudie där ett begränsat antal forskningsartiklar valts ut utifrån deras relevans för projektets syfte.

Dokumentet utvecklas successivt under projektets gång.

---

# Användning av AI

Denna litteraturstudie utvecklas i samarbete mellan författaren och generativ AI.

AI används som stöd för:

- identifiering av relevanta forskningsartiklar
- sammanfattning av forskningsresultat
- strukturering av litteraturstudien
- begreppsförklaringar
- språkgranskning
- diskussion kring forskningsluckor

Samtliga sammanfattningar och slutsatser granskas och verifieras av författaren innan de inkluderas i dokumentet.

---

# Innehåll

1. Introduktion
2. Metod
3. Genomgång av forskningsartiklar
4. Sammanfattning
5. Referenser

---

# 1. Introduktion

Utvecklingen av generativ AI och stora språkmodeller (Large Language Models, LLM) har under de senaste åren förändrat hur mjukvaruutveckling bedrivs. Från att initialt ha använts som intelligenta kodassistenter har forskningen successivt utvecklats mot agentiska AI-system där flera specialiserade AI-agenter samarbetar för att lösa komplexa uppgifter genom hela mjukvaruutvecklingsprocessen.

Parallellt har Software Quality Assurance (QA) blivit ett område där AI förväntas kunna bidra med förbättrad kravanalys, testdesign, testgenerering och kvalitetssäkring. Trots den snabba utvecklingen är forskningsområdet fortfarande ungt och flera frågor kring arkitektur, samarbete mellan agenter och kvalitetssäkring återstår att besvara.

Syftet med denna litteraturstudie är därför att skapa en översikt över aktuell forskning inom området och identifiera vilka idéer, arkitekturer och arbetssätt som är relevanta för utvecklingen av agentiska QA-system.

---

# 2. Metod

Denna studie är en riktad litteraturstudie.

Syftet har inte varit att genomföra en fullständig systematisk litteraturöversikt, utan att identifiera ett begränsat antal forskningsartiklar som tillsammans ger en god förståelse för forskningsområdet.

Urvalet har fokuserat på tre typer av publikationer:

- översiktsartiklar (Survey Papers)
- forskningsartiklar om agentiska system
- forskningsartiklar inom AI-assisterad Software Quality Assurance

Tyngdpunkten ligger på publikationer från **2023–2026**, då utvecklingen inom Agentic AI varit särskilt snabb.

Artiklarna har valts utifrån:

- vetenskaplig relevans
- aktualitet
- koppling till projektets forskningsfråga
- betydelse för utformningen av den planerade forskningsprototypen

---

# 3. Genomgång av forskningsartiklar

Följande forskningsartiklar utgör grunden för litteraturstudien.

# Val av forskningsartiklar

Denna litteraturstudie är en **riktad litteraturstudie** och inte en systematisk litteraturöversikt (SLR).

Syftet är att skapa en god förståelse för forskningsområdet kring AI-agenter, agentiska system och Software Quality Assurance, samt att använda resultaten som kunskapsunderlag inför den separata forskningsprototypen.

Artiklarna har valts utifrån följande kriterier:

- hög vetenskaplig relevans
- aktualitet
- betydelse inom forskningsområdet
- koppling till AI-agenter och Software Engineering
- relevans för kravanalys, testdesign och testgenerering inom Software Quality Assurance

Tyngdpunkten ligger på publikationer från **2023–2026**, då utvecklingen inom Agentic AI har varit särskilt snabb.

---

# Översiktsartiklar

Dessa artiklar utgör grunden för litteraturstudien och bör läsas först.

| Nr | Artikel | År | Kort beskrivning | Länk |
|---:|----------|----|------------------|------|
| 1 | **Large Language Model-Based Agents for Software Engineering: A Survey** | 2024 | Den viktigaste översiktsartikeln inom området. Beskriver LLM-baserade agenter, agentkomponenter, multi-agent-system och forskningsläget inom Software Engineering. | https://arxiv.org/abs/2409.02977 |
| 2 | **Agents in Software Engineering: Survey, Landscape and Vision** | 2025 | Kompletterar den första surveyartikeln och presenterar ramverket Perception–Memory–Action samt forskningslandskapet för AI-agenter inom Software Engineering. | https://arxiv.org/abs/2409.09030 |
| 3 | **The Rise of Agentic Testing: Multi-Agent Systems for Robust Software Quality Assurance** | 2026 | Beskriver hur flera AI-agenter samarbetar för att generera, exekvera, analysera och förbättra tester i en iterativ QA-process. | https://arxiv.org/abs/2601.02454 |
| 4 | **AgentCoder: Multi-Agent-based Code Generation with Iterative Testing and Optimisation** | 2023 | Ett av de mest inflytelserika arbetena kring agentisk mjukvaruutveckling där flera specialiserade agenter samarbetar genom återkopplingsloopar. | https://arxiv.org/abs/2312.13010 |
| 5 | **Automatic High-Level Test Case Generation using Large Language Models** | 2025 | Visar hur stora språkmodeller kan generera hög-nivå testfall direkt från krav och use cases. Mycket nära projektets fokus på kravbaserad testdesign. | https://arxiv.org/abs/2503.17998 |

---

# Forskningsartiklar

Dessa artiklar ger en djupare förståelse för olika agentarkitekturer och moderna arbetssätt.

| Nr | Artikel | År | Kort beskrivning | Länk |
|---:|----------|----|------------------|------|
| 6 | **MetaGPT: Meta Programming for Multi-Agent Collaborative Framework** | 2023 | Beskriver ett rollbaserat multi-agent-system där olika AI-agenter motsvarar klassiska roller inom mjukvaruutveckling, exempelvis Product Manager, Architect, Engineer och QA. | https://arxiv.org/abs/2308.00352 |
| 7 | **SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering** | 2024 | Visar hur AI-agenter kan arbeta direkt mot verkliga kodbaser, terminaler, Git-repositorier och utvecklingsverktyg. | https://arxiv.org/abs/2405.15793 |
| 8 | **Agentic AI in the Software Development Lifecycle: Architecture, Empirical Evidence, and the Reshaping of Software Engineering** | 2026 | Beskriver hur agentiska arbetssätt påverkar hela mjukvaruutvecklingsprocessen och presenterar en modern referensarkitektur för Agentic Software Engineering. | https://arxiv.org/abs/2604.26275 |

---

# Kompletterande litteratur

Denna artikel är intressant men bedöms inte vara nödvändig för att uppfylla målen med denna litteraturstudie.

| Nr | Artikel | År | Kort beskrivning | Länk |
|---:|----------|----|------------------|------|
| 9 | **AI-driven Software Development: A Pragmatic Path to Agentic Development Processes** | 2026 | Diskuterar hur organisationer successivt kan gå från AI-assisterad utveckling till fullt agentiska utvecklingsprocesser. Fokus ligger på införande, styrning och organisatoriska aspekter. | https://arxiv.org/abs/2606.15283 |

---

# Sammanfattning

Denna läslista består av totalt **nio utvalda forskningsartiklar**.

Urvalet bedöms ge en god balans mellan:

- grundläggande teori om AI-agenter,
- moderna agentarkitekturer,
- Agentic Software Engineering,
- Software Quality Assurance,
- kravanalys,
- testdesign,
- testgenerering.

Målet är inte att ge en fullständig översikt över forskningsområdet, utan att skapa ett tillräckligt kunskapsunderlag för att förstå området och motivera de designval som senare görs i projektets forskningsprototyp.


## 3.1 Large Language Model-Based Agents for Software Engineering: A Survey (2024)

*Sammanfattning skrivs efter genomgång.*

---

## 3.2 Agents in Software Engineering: Survey, Landscape and Vision (2025)

Denna översiktsartikel syftar till att skapa en gemensam förståelse för vad en AI-agent är inom Software Engineering och hur moderna agentiska system kan beskrivas med ett enhetligt ramverk. Författarna konstaterar att begreppet AI-agent används på många olika sätt i litteraturen – från enkla språkmodeller med en prompt till avancerade system med planering, minne, verktygsanvändning och flera samverkande agenter. Artikelns främsta bidrag är därför en konceptuell modell som beskriver de centrala komponenterna i en modern AI-agent.

Författarna identifierar fyra grundläggande pelare som tillsammans beskriver agentens funktionalitet: Perception, Reasoning, Action och Evolution. Perception handlar om agentens förmåga att uppfatta och tolka information från omgivningen, exempelvis kravspecifikationer, källkod, testresultat eller användarinstruktioner. Reasoning beskriver hur agenten analyserar informationen, drar slutsatser och fattar beslut med hjälp av språkmodellen. Action omfattar agentens förmåga att utföra konkreta handlingar, såsom att generera kod, skapa testfall, uppdatera filer eller använda externa verktyg. Den fjärde pelaren, Evolution, beskriver hur agenten successivt kan förbättra sitt beteende genom återkoppling, erfarenheter, reflektion och iterationer.

Artikeln lyfter även fram minne som en central komponent i agentarkitekturen. Författarna skiljer mellan flera olika typer av minne. Short-Term Memory används för att hålla aktuell kontext under en pågående uppgift, medan Long-Term Memory lagrar mer permanent kunskap, exempelvis tidigare erfarenheter, domänkunskap eller historiska lösningar. Working Memory används för att dela information mellan flera samverkande agenter under samma körning och möjliggör därmed ett gemensamt arbetsflöde. Slutligen beskriver artikeln även External Memory, där agenten hämtar information från externa kunskapskällor såsom RAG-lösningar, vektordatabaser, Git-repositorier eller dokumenthanteringssystem.

En annan viktig slutsats är att moderna agentiska system i allt större utsträckning bygger på specialiserade agentroller snarare än en enda generell agent. Genom att dela upp arbetet mellan exempelvis en Requirements Agent, en Test Design Agent och en Review Agent kan varje agent fokusera på en avgränsad uppgift, vilket förbättrar både kvalitet, spårbarhet och möjligheten till återkoppling. Artikeln visar även att en orkestrator ofta används för att koordinera samarbetet mellan agenterna och styra arbetsflödet.

För denna studie är artikeln särskilt relevant eftersom den ger en tydlig teoretisk modell för hur agentiska system kan byggas upp. De fyra pelarna och den beskrivna minnesarkitekturen utgör ett användbart ramverk för att analysera och jämföra olika agentlösningar. Samtidigt ligger artikelns beskrivning nära den agentarkitektur som senare används i projektets forskningsprototyp, där specialiserade QA-agenter samverkar under ledning av en orkestrator och delar information genom ett gemensamt arbetsminne. Jag skulle därför betrakta denna artikel som en av de viktigaste teoretiska referenserna i litteraturstudien.

---

## 3.3 The Rise of Agentic Testing: Multi-Agent Systems for Robust Software Quality Assurance (2026)

Denna artikel undersöker hur agentiska AI-system kan användas för att automatisera och förbättra Software Quality Assurance. Till skillnad från traditionella AI-lösningar, där en enskild språkmodell används för att generera testfall eller besvara frågor, förespråkar författarna en multi-agentarkitektur där flera specialiserade agenter samarbetar genom hela testprocessen. Syftet är att skapa ett mer robust, spårbart och iterativt arbetssätt där olika agentroller ansvarar för olika delar av testprocessen.

Artikeln presenterar en referensarkitektur bestående av flera samverkande agenter. En Test Generation Agent ansvarar för att analysera krav och generera testfall, en Execution Agent kör testerna och samlar in resultat, medan en Review Agent analyserar utfallet och identifierar brister eller förbättringsmöjligheter. Resultatet används därefter som återkoppling till tidigare steg, vilket skapar en iterativ förbättringsprocess där testfallen successivt kan förfinas.

En central idé i artikeln är att testning inte längre bör ses som ett linjärt arbetsflöde utan som en kontinuerlig återkopplingsloop. Genom att kombinera testgenerering, exekvering och granskning kan systemet identifiera brister i testfallen och automatiskt initiera nya iterationer. Författarna menar att detta leder till bättre testkvalitet, högre kravtäckning och mer robusta testsviter än om varje steg utförs isolerat.

Artikeln diskuterar även flera utmaningar med agentisk testning. Eftersom flera agenter samarbetar blir koordination, kommunikation och spårbarhet viktiga aspekter. Författarna betonar därför behovet av en orkestrator som ansvarar för att styra arbetsflödet, överföra information mellan agenterna och avgöra när en ny iteration ska genomföras eller när processen kan avslutas. De lyfter också fram vikten av gemensamt minne och tydliga granskningsmekanismer för att minska risken för felaktiga eller hallucinatoriska resultat.

För denna studie är artikeln särskilt relevant eftersom den beskriver en agentarkitektur som ligger nära projektets övergripande idé. Även om den föreslagna lösningen främst fokuserar på testgenerering och testexekvering, medan den planerade forskningsprototypen utgår från kravanalys och testdesign, bygger båda lösningarna på samma grundprinciper: specialiserade agentroller, en central orkestrator och iterativa återkopplingsloopar. Artikeln visar också att Review Agenten har en central roll i att förbättra kvaliteten på de genererade testartefakterna, vilket stärker idén om att kvalitetsgranskning bör vara en egen agentfunktion och inte endast ett avslutande steg i processen.

Egna reflektioner

En viktig lärdom från artikeln är att fler agenter inte automatiskt leder till bättre resultat. Varje ny agent ökar komplexiteten genom fler överlämningar, mer kommunikation och större krav på orkestrering. Samtidigt visar artikeln att vissa agentroller tillför ett tydligt mervärde och därför är motiverade.

En sådan roll är Review Agent. På samma sätt som en person sällan upptäcker alla fel i sitt eget arbete finns det en risk att en agent inte identifierar brister i sina egna resultat. En oberoende granskningsagent kan därför analysera det producerade materialet, kontrollera kvalitet, spårbarhet och täckning samt ge återkoppling innan resultatet skickas vidare eller godkänns. Analogt kan detta liknas vid att inte rätta sitt eget matematikprov, utan låta någon annan göra en oberoende granskning.

Detta resonemang ger ett tydligt stöd för att använda en separat Review Agent i ett agentiskt QA-system, samtidigt som det talar emot att dela upp arbetsflödet i ett alltför stort antal specialiserade agenter. En välbalanserad agentarkitektur bör därför innehålla så få agenter som möjligt, men så många som behövs för att säkerställa kvalitet och spårbarhet.

---

## 3.4 AgentCoder: Multi-Agent-based Code Generation with Iterative Testing and Optimisation (2023)

*Sammanfattning skrivs efter genomgång.*

---

## 3.5 MetaGPT: Meta Programming for Multi-Agent Collaborative Framework (2023)

*Sammanfattning skrivs efter genomgång.*

---

## 3.6 SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering (2024)

*Sammanfattning skrivs efter genomgång.*

---

## 3.7 Agentic AI in the Software Development Lifecycle: Architecture, Empirical Evidence, and the Reshaping of Software Engineering (2026)

*Sammanfattning skrivs efter genomgång.*

---
## 3.8 Automatic High-Level Test Case Generation using Large Language Models (2025)

En avslutande artikel väljs inom området AI-assisterad testning eller Requirements Engineering beroende på vilket område som visar sig mest relevant för den fortsatta forskningsprototypen.

---

# 4.  Reflektioner från litteraturstudien

Efter genomgång av de utvalda forskningsartiklarna sammanfattas de viktigaste slutsatserna kring:

- AI-agenter
- Multi-Agent Systems
- Agentic Software Engineering
- AI för Software Quality Assurance
- forskningsluckor
- konsekvenser för framtida agentiska QA-system

Resultatet från litteraturstudien används som kunskapsunderlag inför projektets fortsatta designarbete.

---

# 5. Referenser


1. **Large Language Model-Based Agents for Software Engineering: A Survey (2024)**  
   https://arxiv.org/abs/2409.02977

2. **Agents in Software Engineering: Survey, Landscape and Vision (2025)**  
   https://arxiv.org/abs/2409.09030


3. **The Rise of Agentic Testing: Multi-Agent Systems for Robust Software Quality Assurance (2026)**  
   https://arxiv.org/abs/2601.02454

4. **AgentCoder: Multi-Agent-based Code Generation with Iterative Testing and Optimisation (2023)**  
   https://arxiv.org/abs/2312.13010

5. **MetaGPT: Meta Programming for Multi-Agent Collaborative Framework (2023)**  
   https://arxiv.org/abs/2308.00352

6. **SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering (2024)**  
   https://arxiv.org/abs/2405.15793

7. **Agentic AI in the Software Development Lifecycle: Architecture, Empirical Evidence, and the Reshaping of Software Engineering (2026)**  
   https://arxiv.org/abs/2604.26275

8. **AI-driven Software Development: A Pragmatic Path to Agentic Development Processes (2026)**  
   https://arxiv.org/abs/2606.15283

---

**Kommentar**

Litteraturstudien bygger på ett begränsat urval av forskningsartiklar som bedömts ge en god överblick över forskningsområdet. Målet är att skapa en stabil teoretisk grund för projektets fortsatta arbete snarare än att genomföra en fullständig systematisk litteraturöversikt.