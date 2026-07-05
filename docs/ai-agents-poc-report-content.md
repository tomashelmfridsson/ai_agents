# AI Agents POC Rapport

## Syfte

Detta dokument fungerar som projektets samlade Rapport öcer Litteratur studie och Bygge av en QA agentic prototyp Proof of Concept (POC). Syftet med POC:en är i första hand att skapa en praktisk förståelse för hur agenter och agentiska lösningar fungerar, särskilt i ett QA-perspektiv. Fokus ligger därför på att undersöka hur specialiserade agentroller, orkestrering, routing, minne, återkopplingsloopar och granskning kan användas för kravbaserad testdesign och testgenerering, samt att beskriva vilka agentiska egenskaper som redan har demonstrerats och vilka områden som fortfarande återstår att utvärdera.

## Projektets utvecklingsresa

Arbetet började med att förstå hur AI-agenter fungerar i teori och praktik. Den första fasen handlade därför om att läsa in oss på agentbegreppet, agentisk orkestrering, minne, routing, återkopplingsslingor och granskning i multi-agentmiljöer. Målet var inte enbart att använda ett färdigt ramverk, utan att först förstå vad som faktiskt krävs för att bygga ett agentiskt QA-system. Detta finns beskrivet i Litteraturstudien.

Därefter försökte vi bygga en egen agentisk lösning från grunden. Men inna dess behövde vi bygga agenter. Vi byggde tre agenter, en för att anaöysera et brett krav med titel  och förfina det till användbara krav. Nästa agent skrev sedan testdesign och testfall utifrån dessa krav. Men litteraturstudien sa att detta aldrig blir tillräckligt utan det allra bästa är att ha en exekveringsfas och i detta fall skulel det vara testfallen. Nu hade vi inget System Under Test (SUT) så istället skapades en oberoende granskningsagent som hade som uppgift att approva testfallen utifrån kraven. Dessa Agenter skapade med vibe kodning AI assisterad kodning, och kördes först lokalt men är nu publicerade publikt på Huggingface med en dockerlösning. Varje Agent var egentligen en LLM med en prompt med ett direktiv som beskrev den uppgift och vilken leverabel den skulle generera.

När vi nu hade agenter klara var det dags att börja skapa en multiagent lösning. Först skapades en skevenstionss lösning där vi Designade Krav, skapade testfall och sedan granskade.
Dessa tidiga experiment kördes med lokala LLM:er, framför allt Llama-baserade modeller via lokal inferens. Detta gav praktisk förståelse för hur långt man kunde komma med egen sekventiell orkestrering, men också vilka begränsningar som uppstod i kvalitet, stabilitet och exekveringstid.

Nästa steg blev att gå över till Hugging Face-baserad körning för de live-LLM:er som användes i arbetsflödet. Därigenom kunde vi få tillgång till starkare och mer flexibla modeller, samtidigt som vi behöll kontrollen över vår egen agentlogik och vår egen experimentmiljö.

## Från sekventiellt flöde till agentisk routing

En viktig insikt var att arbetsflödet inte borde vara strikt synkront i formen requirements -> design -> review som ett fast sekventiellt rör. I praktiken visade det sig att agenterna behövde kunna hoppa mellan noder på ett smartare sätt beroende på kvaliteten i mellanresultaten. Då infördes En Orkestrering med smartare hantering.

För att stödja detta behövdes tre centrala mekanismer för att hantera att för myclet bru reducerade agenternas förmåga och fick för mycket irrelevant information:

- privat agentminne för lokala anteckningar och mellanresultat
- delat minne för gemensam kontext mellan agenterna
- icke-fix routing där nästa steg bestäms dynamiskt i stället för hårdkodas fullt ut som till sist blev det en LLM baserad Orkestrering.

Detta ledde fram till en lösning där orkestratorn blev den styrande komponenten. Routing kunde då avgöras utifrån resultat, brister, feedback och stopvillkor i stället för från en helt statisk stegordning.
Men fortfarande var det hårdkodat vilka steg som fick hoppas mellan. tex om Testdesign agenten tyckte kraven var undermåliga kunde den skicka tillbaka till krav agenten att gör om följande krav eller om gransknings agenten inte kunde approva så kunde den skicka tillbaka till Tewtdesign att förbättra testfallen för ett eller flera krav.

En viktig upptäckt som blev en förfining i denna orkestrering är att formulera målet explicit som att nå `approved=true` från Review Agent, i stället för att använda ett vagare uttryck som försöktes med i början `quality sufficient`, Good enough!. Det senare lämnar större tolkningsutrymme för när körningen faktiskt ska stoppas, medan `approved=true` ger ett tydligt verifieringsmål, skarpare routingbeslut och bättre spårbarhet i efterhand. För denna POC är därför `approved=true` ett bättre styrmål än ett allmänt kvalitetsuttryck, eftersom orkestratorn då kan arbeta mot en konkret granskningssignal snarare än en diffus kvalitetskänsla.

För att få ännu bättre Orkestrering byggdes därefter en LLM baserad Orkestrator. Detta gav en hel del förbättringar framförallt då vi innan kunde se problem med loopar mellan agenter precis som även många forskningsrapporter ifrån litteraturstudierna påvisade och väldigt token krävande att agenterna pga de hårtkodade orkestreringsdefinitionerna kom i loopande disskusioner med varandra. Vi fick helt enkelt införa maximala antal cyckler att ta om samt hur många feedback en agent fick säga till en annan agent.

## Nuvarande AI Agents-sida och arkitektur

Den nuvarande AI Agents-lösningen ska beskrivas i olika delar:

- den publika agent lösningen använder Hugging Face-hostade modeller och agentnära körning via MCP och även REST.
- orkestreringshanteringen i appen är egenutvecklad och innehåller en LLM baserad orkestreringsAgent
- Det är ett GUI byggt i Gradio som hostas på huggingface som man kan använda. Appen innehåller denna HF orkestrerings tjänsten men man kan också välja att köra egna agent modeller med egna direktiv.

Själva AI Agents-delen byggdes alltså i Gradio. Ett viktigt skäl var att det redan fanns viss tidigare kännedom om Gradio, vilket gjorde det till ett pragmatiskt val för att snabbt få fram en fungerande publik experimentmiljö. Nästa expreiment med LangGraph som orkestrator kom däremot att köras i Streamlit. Skälet var inte att Streamlit nödvändigtvis var förstahandsvalet i sig, utan att Gradio medförde flera praktiska begränsningar i just den delen av arbetet, vilket gjorde Streamlit till ett mer fungerande alternativ för LangGraph-spåret.


## HF-publicering, endpoints och MCP

Som en del av utvecklingen publicerades alltså agenterna på Hugging Face så att de blev tillgängliga via publika endpoints och MCP-relaterade integrationsmönster. Detta gjorde att arkitekturen kunde flyttas från enbart lokal experimentkörning till en mer öppen och integrerbar lösning där agenterna kunde användas utanför den lokala appmiljön.

Tidigt i arbetet var tanken att `qa-agent-service` som blev arbetsnamnet för agentlösningen, 3 sparata agenter som kunde anropas via REST och MCP, främst skulle användas via Hugging Face-nycklar. När Hermes Agent senare skulle användas som jämförelse- och integrationsspår blev det dock tydligare att en bättre lösning var att göra tjänstens REST- och MCP-endpoints publika. På så sätt blev agentservicen enklare att återanvända mellan olika klienter och ramverk, i stället för att vara kopplad till ett mer slutet nyckelberoende upplägg. Detta gjordes med en Dockerlösning.

Detta var en viktig övergång eftersom det gjorde det möjligt att kombinera:

- egen agentdesign och orkestratorlogik
- externa hostade agenttjänster
- framtida integrationer mot verktyg och standardiserade agentgränssnitt

## LangGraph som nästa steg

Efter detta byggdes också en LangGraph-baserad lösning. LangGraph kan beskrivas som ett kodbibliotek inom LangChain-ekosystemet för grafbaserad agentisk orkestrering. Det gav ett sätt att uttrycka agentnoder, övergångar och kontrollflöden på ett mer formaliserat sätt.

Den lösningen blev i viss mån lik en MBT-inspirerad struktur, där noder, övergångar och tillstånd blev tydliga. Samtidigt visade arbetet att LangGraph inte på egen hand gav samma enkla agentiska frihet som den egenbyggda lösningen. Jämfört med vår egen arkitektur blev LangGraph-lösningen mer hårdkodad, medan vår egen lösning i högre grad kunde använda en LLM-baserad orkestrator för att styra routingen dynamiskt.

- LangGraph är starkt för explicit grafstruktur och kontroll
- den egenbyggda agentiska lösningen är starkare i dynamisk routing och orkestratorledd flexibilitet

## Observability, direktiv och minnesinsyn

En central designprincip genom hela arbetet var att användaren skulle kunna se vad som skickades in till varje agent, vad som kom ut från varje agent och hur agenten resonerade. Därför byggdes lösningen med tydlig observability i fokus. Men så jättestor vikt har inte lagt på GUI delarna utan detta får betraktas som sekundart i denna POC.

Varje agent fick direktiv som beskrev hur den skulle resonera, vilken roll den hade och vilken kvalitetsnivå som förväntades. Samtidigt exponerades både shared memory och agent-private memory i gränssnittet så att det gick att följa inte bara slutresultatet utan även den interna arbetskontexten under körning.

Detta var viktigt av två skäl:

- för att kunna förstå varför ett resultat blev bra eller dåligt
- för att kunna felsöka routing, minne, feedback och agentbeteende

## Agentdirektiv

I den nuvarande `qa-agent-service` ligger agentbeteendet deklarativt i agentregistret och byggs sedan in i prompten tillsammans med scenario, agentinput, shared memory, agent-private memory, modellkonfiguration, output-kontrakt och strikta JSON-regler. 

Dessa direktiv förfinades på vägen hela tiden och tanken kom om det skulle vara möjligt att justera dem under en körning. Det finnns forskningslitteratur som tar upp detta ämne men också vilka svårighetsgrader
t.ex. Standard Operational Procedures (SOP) nämner att agenternas instruktioner bör vara stabila och väldefinierade, annars kan inte bara token kostnaderna skena utan också bias och felen hallucinationerna ökar och späs på av nästa agent.

I den aktuella HF QA agent service-konfigurationen körs samtliga tre agenter normalt med `Qwen/Qwen2.5-7B-Instruct`, med temperatur `0.2` för Requirements Analyst och Test Designer samt `0.1` för Review Agent.
detta främst för att den var gratis, snabb och tillräckligt bra, men långt ifrån bäst när vi sedan testgörde mot GPT 5.5 med hjälp av Hermes Agent framework.

### Requirements Analyst Agent

```text
Purpose: Extract only requirements supported by the provided text and make uncertainty explicit.
Required behavior:
- Preserve traceability to original requirement text.
- Create stable requirement IDs using REQ-001, REQ-002, etc.
- Separate supported requirements from assumptions, ambiguities, and open questions.
- Prefer smaller, testable requirements when the text contains multiple behaviors.
Required output:
- requirement_id
- original_text
- normalized_text
- priority
- acceptance_criteria
- assumptions
- open_questions
- ambiguities
- decision_basis
- agent_explanation
Forbidden behavior:
- Do not invent missing business rules.
- Do not silently resolve ambiguity.
- Do not produce vague acceptance criteria.
Quality bar: Each requirement must be testable, traceable, and clearly separated from uncertainty.
```

### Test Design Agent

```text
Purpose: Create concrete, reviewable, executable test cases from structured requirements.
Required behavior:
- Maintain traceability to requirement IDs.
- Include concrete preconditions, data, steps, expected results, and oracle logic.
- Cover relevant positive, negative, boundary, validation, authorization, and error paths.
- Preserve valid existing test cases during selective revision.
Required output:
- test_case_id
- requirement_ids
- title
- test_type
- scenario_type
- preconditions
- test_data
- steps
- expected_results
- oracle
- risks
- decision_basis
- agent_explanation
Forbidden behavior:
- Do not use vague steps or expected results.
- Do not create placeholders.
- Do not ignore unresolved assumptions or ambiguities.
Quality bar: Every test case must be specific, executable, observable, and traceable.
```

### Review Agent

```text
Purpose: Critically review generated requirements and tests and decide whether quality is sufficient.
Required behavior:
- Check traceability, oracle strength, observable expected results, and coverage.
- Check unresolved assumptions, placeholder language, and suspicious one-to-one mappings.
- Identify weakest test cases first and provide targeted improvement actions.
Required output:
- approved
- verdict
- coverage_ratio
- findings
- improvement_actions
- decision_basis
- agent_explanation
Forbidden behavior:
- Do not approve generic or weakly testable cases.
- Do not ignore weak oracle logic or missing negative and boundary coverage.
- Do not make the final orchestration decision.
Quality bar: The review must explain exactly why quality passes or fails with concrete recommendations.
```

Direktiven visar också en viktig del av projektets inriktning: målet var inte bara att få modellerna att generera text, utan att ge dem tydliga kvalitetskontrakt per roll och ett strikt output-kontrakt. På så sätt blev direktiven en central del av hur agentbeteende, spårbarhet, granskningsbarhet och strukturerad JSON-output kunde studeras i POC:en.

## Loopar, begränsningar och approve true

Ett återkommande problem var att agenterna ibland hamnade i loopar där de skickade feedback fram och tillbaka utan att faktiskt nå ett tillräckligt bra slutresultat. För att hantera detta infördes begränsningar i:

- totalt antal rundor
- totalt antal feedbackmeddelanden
- antal feedbackmeddelanden mellan samma agentpar

Detta blev centralt i arkitekturen eftersom målet var att Review Agent i slutänden helst skulle kunna sätta `approve = true`. I praktiken visade det sig att detta var svårt att uppnå konsekvent. Vid vissa enstaka körningar gick det, men generellt var det betydligt svårare än väntat att få hela kedjan att nå ett robust godkänt slutläge.

## Utvärderingsfrågan

En viktig del av arbetet blev därför frågan om hur output från Test Design Agent faktiskt ska utvärderas. Det räcker inte att agenten producerar många testfall; den avgörande frågan är hur relevanta, testbara, spårbara och granskningsbara dessa testfall är. På samma sätt uppstod frågan om hur starkt review-steget egentligen är: hur bra är Review Agent på att skilja mellan ytliga och verkligt robusta testdesigner?

Denna utvärderingsfråga är en av de mest centrala slutsatserna hittills. Systemet kan producera artefakter, men det är betydligt svårare att med hög tillförlitlighet avgöra när kvaliteten verkligen är tillräcklig.
I både den interna och i Langgraph lösningarna är testfallen nedladdningsbara för att eutvärderas, tanken var att använda t.ex. DeepEval som är ett program för detta men även min seniora QA expertis efter många år i rollen som QA expert.

## Standardscenarier för jämförelse

För att kunna jämföra lösningar mer systematiskt skapades sex standardscenarier:

- Scenario 1 - login and registration
- Scenario 2 - e-commerce checkout
- Scenario 3 - password reset
- Scenario 4 - support tickets
- Scenario 5 - inventory management
- Scenario 6 - course enrollment

Dessa används som återkommande testfall i de olika lösningarna för att kunna jämföra routing, kravanalys, testdesign, reviewbeteende, observability och sannolikheten att nå ett godkänt resultat.

## Hermes som nästa undersökningsspår

Nästa steg i arbetet blev att undersöka om Hermes Agent Framework kunde tillföra något som saknades i de tidigare lösningarna. Det gör Hermes relevant både som jämförelseobjekt och som möjlig inspirationskälla för hur agentstruktur, kommunikation och styrning kan organiseras framåt.

## Hermes-resultat som jämförelsepunkt

Ett viktigt delresultat var att Hermes Agent kunde skapa en fungerande testcase-generator relativt snabbt. Detta är i sig en viktig observation för POC-resultatet: det var enkelt att få fram en tydlig multi-agentliknande QA-struktur i Hermes utan att först behöva bygga all orkestreringslogik från grunden.

Den Hermes-lösning som togs fram var en Kanban Swarm med följande struktur:

- en root task som fungerade som shared blackboard
- en Requirements Analyst
- en Test Designer
- en QA Risk Reviewer
- en Verifier
- en Synthesizer

Flödet var i praktiken:

- krav in
- shared blackboard / root task
- parallella specialist-workers
- verifier gate
- synthesizer
- slutlig testdesign

Detta är viktigt eftersom Hermes därmed visade att det går att skapa en ganska komplett testcase-generator med tydlig rollseparation, verifieringssteg och syntes av slutartefakt på ett relativt direkt sätt.

## Vad Hermes-lösningen producerade

I Hermes-fallet användes ett konkret login/lockout-krav som ingång. Lösningen producerade bland annat:

- acceptance criteria
- antaganden
- risks och open questions
- scenarios
- traceability matrix
- release gate recommendation

Verifier-steget rapporterade dessutom ett passerat gate-resultat och en omfattande täckning av bland annat lockout-regler, invalid credentials, timing-risker och spårbarhet. Detta gör Hermes-resultatet relevant som ett konkret jämförelseobjekt mot den egna HF-baserade QA agent service-lösningen.

## Viktig jämförelsebegränsning

Samtidigt måste jämförelsen beskrivas ärligt: Hermes-lösningen kördes med en betydligt starkare modellmiljö, i ditt fall GPT-5.5, medan den nuvarande HF QA agent service-lösningen i stor utsträckning har byggt på mindre modeller som Qwen eller Qwen2.5-7B-Instruct.

Det betyder att en direkt kvalitetsjämförelse mellan resultaten inte utan vidare är rättvis. Skillnader i output kan bero på minst tre saker:

- skillnader i ramverk och orkestreringsmodell
- skillnader i promptning, verifiering och artifact-struktur
- skillnader i ren modellkapacitet

Det är därför viktigt att rapporten inte framställer Hermes-resultatet som bättre enbart för att slutartefakten blev starkare. En del av styrkan kan mycket väl bero på att GPT-5.5 är en betydligt starkare modell än den mindre Qwen-varianten i HF-lösningen.

## Vad jämförelsen ändå visar

Trots denna begränsning visar Hermes-körningen flera saker som är värdefulla för POC-resultatet:

- det är enkelt att få fram en användbar testcase-generator i Hermes
- rolluppdelningen blir tydlig och lätt att beskriva
- blackboard- och verifier-gate-mönstret fungerar väl för QA-liknande artefaktflöden
- Hermes ger ett konkret jämförelseobjekt för hur snabbt man kan nå ett användbart resultat med ett externt agentramverk

Detta är därför inte bara ett alternativt experiment, utan också ett argument för att extern ramverksjämförelse är relevant: vissa ramverk kan ge snabbare väg till fungerande agentflöden, medan den egenbyggda lösningen i stället ger större kontroll över routing, minne, observability och framtida utbyggnad.

## Jämförelse mot HF QA agent service

När Hermes jämförs med den egna HF QA agent service-lösningen bör fokus därför ligga på flera dimensioner samtidigt, inte bara slutkvalitet:

- orkestreringsmodell
- rollseparation
- verifier gate
- artifact output
- traceability
- reproducerbarhet
- observerbarhet
- modellkapacitet

I Hermes-fallet var orkestreringen tydligt uttryckt genom Kanban tasks och shared blackboard. I HF-lösningen ligger motsvarande styrka mer i den egenbyggda orkestratorn, det delade minnet, agent-private memory, feedbackbegränsningarna och den tydliga runtime-insynen i appen.

### Jämförelse mellan tre lösningar

I jämförelsen är det viktigt att skilja på själva agentramverket och den underliggande agentservicen. Både den egenbyggda `ai_agent`-lösningen och LangGraph-lösningen använder HF QA agent service som agentbackend, medan Hermes Agent Kanban-lösningen kördes som en separat swarm-struktur.

| Dimension | Vår egen ai_agent-lösning | LangGraph-lösning | Hermes Agent Kanban-lösning |
|---|---|---|---|
| Agentbackend | HF QA agent service | HF QA agent service | Hermes/Kanban swarm med GPT-5.5 i den körning som testades |
| Modellstyrka | Främst Qwen / Qwen2.5-7B-Instruct i nuvarande jämförelse | Främst Qwen / Qwen2.5-7B-Instruct i nuvarande jämförelse | GPT-5.5 |
| Orkestrering | Egenbyggd orkestrator i appen | Grafbaserad orkestrering i LangGraph | Kanban tasks och shared blackboard |
| Rollseparation | Tydlig och styrd av egen arkitektur | Tydlig, men mer formellt definierad via grafnoder | Mycket tydlig och snabb att etablera |
| Routing | Dynamisk routing via orkestrator och selektiv backtracking | Mer grafstyrd och mer explicit definierad i flödet | Mer workflow-styrd via swarm-struktur |
| Minne | Shared memory, agent-private memory och memory timeline | Beror på graf- och state-implementationen, men stödjer tydligt state-flöde | Blackboard-liknande delning mellan tasks |
| Verifiering | Review Agent och stopvillkor, men `approve = true` har varit svårt att nå konsekvent | Kan bygga in review- och verifieringssteg, men mer explicit i flödesdefinitionen | Tydlig verifier gate före synthesizer |
| Observability | Stark GUI-insyn i input, output, resonemang, minne och runtime events | Bra spårbarhet i graf och nodflöden, men mindre integrerad än vår egen GUI-lösning | Kanban/task-spår och artefakter |
| Styrka | Stark forskningsplattform för routing, minne, observability och utvärdering | Stark för explicit grafstruktur, nodstyrning och MBT-liknande modellering | Snabb väg till komplett testcase-generator |
| Begränsning | Resultatet påverkas av mindre modeller och svårigheten att nå stabil `approve = true` | Kan bli mer hårdkodad och mindre fri i dynamisk agentisk routing | Styrkan påverkas sannolikt av den större modellen |

Tabellen ska inte tolkas som att en lösning generellt är bäst. Den visar snarare att lösningarna har olika styrkor: den egenbyggda `ai_agent`-lösningen ger störst kontroll över agentiskt beteende och observability, LangGraph ger en stark och tydlig grafmodell för flöden och tillstånd, medan Hermes Agent Kanban-lösningen visar hur snabbt man kan få fram en användbar testcase-generator i ett externt agentramverk.

## Slutsats om Hermes i rapporten

Delar av Hermes-resultatet bör därför finnas med i POC-rapporten som stöd för två slutsatser:

- det är förhållandevis enkelt att i Hermes skapa en testcase-generator med flera QA-liknande roller
- jämförelsen mot den egna HF QA agent service-lösningen måste göras med tydlig reservation för att modellerna inte är likvärdiga

En korrekt tolkning är därför att Hermes visade hög praktisk produktivitet och snabb väg till ett fungerande QA-flöde, medan den egna lösningen fortfarande är starkare som forskningsplattform för att studera routing, minne, observability, feedbackloopar och agentiskt beteende på mer detaljerad nivå.

## Aktuell statusbedömning mot projektmålet

Den nuvarande QA Agent POC:n har nu nått en nivå där den ger en praktisk förståelse för flera centrala agentbegrepp som tidigare endast fanns som teori i projektbriefen. POC:n visar i körbar form hur ett fleragentsystem kan organiseras kring specialiserade roller, styras av en orkestrator och kombineras med både strukturerad baslinjekörning och LLM-backed körning.

Det som nu tydligt är uppnått är:

- specialiserade agentroller med tydligt ansvar
- orchestrator-first routing
- selektiv backtracking i stället för endast full rerun
- shared working memory och agent private memory
- per-agent modell-, provider-, timeout- och direktivkonfiguration
- runtime visibility genom GUI, runtime activity och live log
- partial-result preservation on failure
- stöd för både lokal Ollama-körning och externa modellstrategier

Detta innebär att projektet i hög grad har uppnått målet att förstå vad agentiska system är på en praktisk nivå, särskilt inom ett QA-orienterat arbetsflöde. Systemet visar inte bara att flera agenter kan existera samtidigt, utan också hur routing, återkoppling, minne, observability och styrbar exekvering påverkar resultatet.

Samtidigt återstår viktiga steg innan lösningen kan beskrivas som ett mer generellt agentramverk:

- agentexpansion är fortfarande kodnära och inte fullt dynamisk
- tool-runtime och MCP-baserad integration är ännu inte en central del av arkitekturen
- persistence och checkpointing är inte generiska på ramverksnivå
- jämförelsen mot externa agentramverk är ännu inte genomförd empiriskt i samma detalj som den interna POC:n
- resultaten av testcase genereringarna av scenarios för de olika lösningarna har inte granskats i detalj så vi vet inte hur bra lösningen är.

Den mest korrekta tolkningen i detta läge är därför att projektet har nått målet att förstå och demonstrera centrala agentegenskaper, men att nästa steg är att jämföra denna POC mer systematiskt mot etablerade agentplattformar och att avgöra vilka delar som bör behållas, generaliseras eller ersättas. Men det vore väldigt intressant att prova detta i praktiken hos ett företag.

