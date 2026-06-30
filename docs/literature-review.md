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

1. [Projektframework](#projektframework)
2. [Teoretisk bakgrund och centrala begrepp](../theoretical-background-and-central-concepts/)
3. [Litteraturstudie](#litteraturstudie)
4. [Agentramverk](#agentramverk)
5. [Systemarkitektur](#systemarkitektur)
6. [Designbeslut](#designbeslut)
7. [Prototyp och implementation](#prototyp-och-implementation)
8. [Experiment och utvärdering](#experiment-och-utvardering)
9. [Framtida arbete](#framtida-arbete)
10. [Forskningsartiklar](#forskningsartiklar)
11. [Referenser](#referenser)

---

<a id="projektframework"></a>

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

<a id="litteraturstudie"></a>

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
- Relevans för studiens syfte

---

<a id="agentramverk"></a>

# 4. Agentramverk

Jämförelse av aktuella agentramverk och deras lämplighet för QA.

---

<a id="systemarkitektur"></a>

# 5. Systemarkitektur

Den aktuella prototypen är en QA-agentplattform med en orkestratorstyrd, flerstegsbaserad arbetsgång. Arkitekturen är inte längre endast en konceptskiss utan speglar den POC som faktiskt har implementerats i systemet. Fokus ligger på att kunna jämföra deterministisk körning med LLM-stödd körning, lokala och externa modellstrategier, samt att kunna följa hur agenterna samverkar under en verklig exekvering.

Kärnan i systemet utgörs av fyra aktiva agentroller:

- **Orchestrator Agent**, som alltid initierar körningen och beslutar vilken agent som ska köras härnäst.
- **Requirements Analyst Agent**, som omvandlar fri kravtext till strukturerade, testbara krav.
- **Test Design Agent**, som härleder testfall och orakel från de strukturerade kraven.
- **Review Agent**, som granskar täckning, testbarhet, svaga antaganden och kvaliteten i testdesignen.

Arkitekturen är uppbyggd kring ett registreringslager för agenter och en separat arbetsflödesgraf. Det innebär att agentdefinitioner, standardmodeller, timeoutvärden och stegindex ligger i en agentregistry, medan körordningen och stegnoderna hålls i ett workflow graph. Denna uppdelning gör att nya agenter kan läggas till utan att hela orkestreringslogiken behöver skrivas om från grunden. I stället för ett helt hårdkodat sekventiellt flöde finns därmed en explicit modell av vilka steg som finns och vilken agent som ansvarar för respektive steg.

En central del av arkitekturen är **orchestrator-first routing**. Varje körning startar i orkestratorsteget och inte direkt i kravanalysen. Orkestratorn fungerar som styrpunkt både vid första start och vid återkopplingsslingor. När en senare agent identifierar brister väljer orkestratorn minsta rimliga backtracking-steg, exempelvis tillbaka till Requirements Analyst eller enbart tillbaka till Test Design. Detta ger en mer agentisk struktur än ett rent linjärt rör, eftersom körningen kan ändra riktning beroende på mellanresultat.

För tillståndshantering används en **RunSession** med ett gemensamt **WorkingMemory**. Minnesmodellen består av tre delar:

- **Shared memory**, för gemensamma nyckel-värden som aktuell fas, källkrav, review-resultat och väntande återkoppling.
- **Agent private memory**, där varje agent kan lagra lokala anteckningar eller mellanresultat.
- **Memory timeline**, som loggar när minnet uppdateras och av vem.

Denna lösning innebär att agenterna inte behöver starta helt från noll mellan stegen inom samma körning. Delad arbetskontext kan återanvändas av efterföljande agenter, samtidigt som privata minnesytor kan hållas separata när det behövs.

Ett annat bärande arkitekturelement är **per-agent runtime configuration**. Varje agent har egen konfiguration för exekveringsläge, providerstrategi, modellfamilj, modelloverride, direktiv och timeout. Därmed kan exempelvis Requirements Analyst köras med en annan lokal Ollama-modell och ett längre timeoutvärde än Review Agent. Samtidigt finns ett globalt lager i gränssnittet där samma LLM-inställningar kan appliceras på samtliga agenter, vilket förenklar experiment och jämförelser.

Arkitekturen innehåller också ett **observability-lager**. Under körning emitteras runtime events för stage start, stage completion och routingbeslut. Dessa används både för GUI-uppdateringar och för skrivning till en live-loggfil. Resultatet blir att systemet inte endast producerar ett slutresultat, utan även en körbar spårkedja över vilka agenter som kördes, med vilken modell, hur lång tid det tog och varför arbetsflödet skickades vidare eller stoppades.

Slutligen bevarar arkitekturen **partial results on failure**. Om exempelvis Requirements Analyst eller Test Design Agent hinner producera ett resultat men en senare agent stoppar på timeout eller modellfel, visas ändå de färdiga delresultaten i GUI och skrivs till körlogg. Det gör arkitekturen bättre lämpad för experimentella QA-flöden där felutfall och mellanresultat är analytiskt värdefulla.

---

<a id="designbeslut"></a>

# 6. Designbeslut

Flera centrala designbeslut i prototypen har tagits som svar på svagheter i enklare, helt sekventiella agentflöden.

Det första beslutet är att använda **orkestratorn som första aktiva steg**. Ett tidigare, enklare upplägg där Requirements Analyst startade direkt gav sämre kontroll över körordning, återkoppling och framtida utbyggnad. Genom att låta orkestratorn alltid starta körningen blir det också tydligt att det är en styrande agent som äger routingbesluten. Detta är särskilt viktigt när fler agenter senare ska kunna införas, exempelvis för deepeval-baserad utvärdering eller grafisk visualisering av testmodeller.

Det andra beslutet är att använda **delat arbetsminne** i stället för att låta varje agent arbeta helt isolerat. Isolerade agentkörningar är enklare att implementera, men de ger svagare kontinuitet och gör det svårare att förstå hur gemensam kontext påverkar senare steg. Ett delat minne ligger närmare hur många agentplattformar arbetar i praktiken, där vissa tillstånd behöver vara gemensamt tillgängliga genom hela körningen.

Det tredje beslutet är att stödja **per-agent modell- och timeoutkonfiguration**. I praktiken är olika steg olika tunga. Requirements Analyst arbetar ofta på bred, tvetydig textmassa och behöver därför längre timeout och ibland en annan modellprofil än exempelvis Review Agent. Ett enda globalt timeoutvärde visade sig vara för grovt, särskilt när lokala modeller på en resursbegränsad maskin kan ha stor variation i svarstid.

Det fjärde beslutet är att ge **lokal Ollama-körning** en framträdande roll. Motivet är dels kostnadskontroll, dels möjlighet att jämföra lokal inferens mot molnbaserade alternativ. Detta ligger i linje med studiens syfte att undersöka QA-agenter under olika modell- och driftstrategier. Samtidigt kräver lokal inferens tydligare felhantering. Därför har systemet kompletterats med snabbare validering av modellnamn och tydligare felmeddelanden när konfigurerad lokal modell inte finns tillgänglig.

Det femte beslutet är att prioritera **live runtime visibility**. I experimentella agentflöden räcker det inte att endast få ett slutligt godkänt eller underkänt resultat. Det måste gå att se vilken agent som kör, vilken modell som används, om routing har skett och var körningen stannade. Därför genererar systemet både runtime-aktivitet i GUI och en levande loggfil som kan följas under pågående körning.

Det sjätte beslutet är att **bevara delresultat vid fel**. Många prototypsystem tappar tidigare steg om ett senare steg fallerar. För QA-analys är det ett dåligt utfall eftersom mellanresultaten ofta är lika intressanta som slutresultatet. Systemet har därför utformats så att redan färdiga agentresultat presenteras även när körningen avbryts av timeout, modellfel eller otillåten vidare routing.

Det sjunde beslutet gäller **global kontra lokal konfigurationskontroll**. För jämförande experiment behövs ibland snabb massändring av modellstrategi för alla agenter, medan andra experiment kräver finjustering per agent. Därför finns både ett globalt “apply to all”-steg och fortsatt stöd för individuell agentkonfiguration. Detta är en pragmatisk kompromiss mellan användbarhet och experimentell precision.

---

<a id="prototyp-och-implementation"></a>

# 7. Prototyp och implementation

Prototypen har implementerats som en lokal Gradio-baserad applikation som kombinerar konfiguration, körning, visualisering och dokumentation i samma arbetsyta. Implementationen består av ett backendlager för agentkörning och ett GUI-lager för styrning och insyn.

Backenddelen innehåller agentklasser, agentregistry, arbetsflödesgraf, orkestreringslogik, minnesmodell, LLM-runtime, lagring av körningar och loggskrivning. Orkestratorn kör varje agent med en dedikerad timeout via en exekveringsomslutning som kan avbryta långsamma steg och rapportera vilken agent som överskred sin gräns. Agenternas runtimekonfiguration byggs dynamiskt utifrån gränssnittets val och kan växla mellan strukturerad baslinje och LLM-backed exekvering.

Stöd för **Ollama local** har implementerats som en första klassens providerstrategi. I praktiken innebär detta att användaren kan välja modellfamilj eller skriva ett explicit modelloverride, såsom `qwen3:8b`, `deepseek-r1:8b` eller `gemma3:4b`. Den faktiska modellidentifieringen löses innan agenten körs, vilket gör att resolved model kan visas i både GUI och logg. Detta har varit viktigt för att kunna förstå vilken lokal modell som faktiskt användes när ett steg blev långsamt eller misslyckades.

GUI:t innehåller flera konfigurationsnivåer. För varje agent kan användaren ställa in exekveringsläge, provider, modellfamilj, override, timeout och agentdirektiv. Därutöver finns ett globalt konfigurationsområde där samma LLM-inställningar kan appliceras på samtliga agenter. Terminologin har också harmoniserats så att begreppet **Maximum rounds** används konsekvent för den övergripande gränsen för antalet arbetsflödesrundor.

Under körning uppdateras flera resultatpaneler i realtid:

- **Run status**, som visar övergripande körstatus och senaste händelse.
- **Run report**, som visar sammanfattning, använda modeller, timeoutinformation och delresultat vid fel.
- **Runtime activity**, som visar stegvisa runtime events med tidsdata och agentnamn.
- **Working memory**, som visualiserar shared memory, agent private memory och memory timeline.

En separat **live log file** skapas i början av körningen och fylls på successivt med konfiguration och runtime events. Loggfilen fungerar som ett externt spår som kan följas utanför GUI:t. Parallellt sparas fullständiga körningar i databasen tillsammans med strukturerade stage traces, review-resultat och metadata om runtimekonfigurationen. Detta gör att prototypen inte endast är en körmotor utan också en spårbar experimentplattform.

Dokumentationen är integrerad i samma applikation. Litteraturstudie, project brief, AI developing guidelines och QA agent developing requirements exponeras både i gränssnittet och via publicering på GitHub Pages. Detta är ett viktigt implementeringsval eftersom applikationen därmed fungerar både som forskningsprototyp och som dokumenterad artefakt med en publik läsbar yta.

---

<a id="experiment-och-utvardering"></a>

# 8. Experiment och utvärdering

I den nuvarande POC:n bör utvärderingen utgå från den faktiska agentplattformen snarare än från generella antaganden om ett framtida system. Det innebär att utvärderingen bör omfatta både **produktkvalitet i QA-resultatet** och **driftbeteende i den agentiska körningen**.

Ett första utvärderingsområde är **kravkvalitet och spårbarhet**. Här bör man analysera om Requirements Analyst producerar krav som är testbara, explicita och kopplade till tydliga acceptanskriterier. Ett relevant mått är hur stor andel av de identifierade kraven som senare återkommer i testdesign och review utan att förlora sin spårbarhet.

Ett andra område är **kvaliteten i testdesignen**. Här är det inte tillräckligt att räkna antalet testfall. Viktigare är om testfallen innehåller konkreta steg, observerbara förväntade resultat och tydliga orakel. Review Agentens findings och improvement actions kan användas som kvalitativa indikatorer på vilka svagheter som fortfarande finns i testmaterialet.

Ett tredje område är **orkestreringens effektivitet**. Eftersom systemet nu arbetar med orchestrator-first routing och selektiv backtracking bör man mäta:

- hur många rundor som faktiskt behövs innan stopvillkor uppnås,
- hur ofta orkestratorn skickar tillbaka arbetet till Requirements Analyst respektive Test Design Agent,
- om återkopplingen är tillräckligt riktad för att minska onödiga omkörningar.

Ett fjärde område är **runtimeprestanda och stabilitet**. Här är följande mått särskilt relevanta:

- körtid per agentsteg,
- total körtid per arbetsflödesrunda,
- antal timeoutavbrott,
- skillnader mellan modeller vid lokal Ollama-körning,
- påverkan av per-agent timeoutinställningar.

Detta är särskilt viktigt eftersom observationer från prototypen visar att vissa lokala modeller kan vara praktiskt användbara för lättare steg men för långsamma eller instabila för mer krävande kravanalys, särskilt på en lokal maskin med begränsade resurser.

Ett femte område är **observability och felsökbarhet**. Här bör man bedöma om GUI:t och loggstrukturen faktiskt hjälper användaren att förstå körningen. Exempel på frågor är om det går att se vilken modell som kördes, var i flödet systemet befann sig, vilka steg som hann bli klara innan ett fel, och om minnespanelen ger meningsfull insyn i delad och privat agentkontext.

Ett sjätte område är **jämförelsen mellan deterministisk baslinje och LLM-backed exekvering**. Den nuvarande prototypen lämpar sig väl för sådana jämförelser eftersom samma arbetsflöde kan köras med olika exekveringslägen och olika runtimekonfigurationer. Det gör det möjligt att jämföra kvalitet, körhastighet, stabilitet och behov av mänsklig eftergranskning under kontrollerade former.

Sammanfattningsvis är prototypen nu nära en verklig agentisk experimentmiljö, men utvärderingen bör fortfarande beskriva den som en **QA Agent POC** snarare än ett fullständigt generellt agentramverk. Systemet har fått flera egenskaper som normalt förknippas med agentiska lösningar, såsom routing, gemensamt minne, spårning, partiell återhämtning och konfigurerbar runtime. Däremot återstår fortfarande framtida arbete kring bredare agentexpansion, mer generisk persistence, djupare tool-runtime och eventuella MCP-baserade integrationsmönster.

---

<a id="framtida-arbete"></a>

# 9. Framtida arbete

Identifierade förbättringar och fortsatta forskningsmöjligheter.

---

<a id="forskningsartiklar"></a>

# 10. Forskningsartiklar

Detta kapitel kommer att innehålla en sammanställning av relevanta forskningsartiklar och rapporter.

---

<a id="referenser"></a>

# 11. Referenser

Referenslista enligt vald referensstandard (preliminärt IEEE).
