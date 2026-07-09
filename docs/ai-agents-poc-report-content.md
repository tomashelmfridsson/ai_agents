# AI-agent POC-rapport

## Syfte

Detta dokument fungerar som projektets samlade rapport över litteraturstudien och utvecklingen av en QA-orienterad agentisk Proof of Concept (POC). Syftet med POC:en är i första hand att skapa en praktisk förståelse för hur [AI-agenter](../theoretical-background-and-central-concepts/#ai-agent) och [agentiska lösningar](../theoretical-background-and-central-concepts/#agentic-ai) fungerar, särskilt ur ett [Software Quality Assurance](../theoretical-background-and-central-concepts/#software-quality-assurance)-perspektiv.

Fokus ligger därför på att undersöka hur specialiserade agentroller, [orkestrering](../theoretical-background-and-central-concepts/#orchestrator), routing, [minne](../theoretical-background-and-central-concepts/#agent-memory), återkopplingsloopar och granskning kan användas för kravbaserad [testdesign](../theoretical-background-and-central-concepts/#test-design) och testgenerering. Rapporten beskriver också vilka agentiska egenskaper som redan har demonstrerats och vilka områden som fortfarande återstår att utvärdera.

## Projektets utvecklingsresa

Arbetet började med att förstå hur [AI-agenter](../theoretical-background-and-central-concepts/#ai-agent) fungerar i teori och praktik. Den första fasen handlade därför om att läsa in oss på agentbegreppet, agentisk [orkestrering](../theoretical-background-and-central-concepts/#orchestrator), [minne](../theoretical-background-and-central-concepts/#agent-memory), routing, återkopplingsslingor och granskning i [multi-agentmiljöer](../theoretical-background-and-central-concepts/#multi-agent-system). Målet var inte enbart att använda ett färdigt [agentramverk](../theoretical-background-and-central-concepts/#agent-framework), utan att först förstå vad som faktiskt krävs för att bygga ett agentiskt QA-system. Detta arbetssätt stöds av översiktsartiklarna Large Language Model-Based Agents for Software Engineering och Agents in Software Engineering, som visar att förståelsen för agenternas arkitektur, minne, planering och samarbete är en förutsättning för att kunna konstruera effektiva agentiska system.

Därefter försökte vi bygga en egen agentisk lösning från grunden. Innan detta var möjligt behövde vi först bygga själva agenterna. Vi tog fram tre agenter: en agent för att analysera ett övergripande krav och förfina det till användbara krav, en agent för att skapa [testdesign](../theoretical-background-and-central-concepts/#test-design) och testfall utifrån dessa krav, samt en oberoende granskningsagent. Valet att dela upp arbetet mellan specialiserade agentroller stöds av flera studier, bland annat AgentCoder, MetaGPT och The Rise of Agentic Testing. Samtliga visar att rollspecialisering kan förbättra kvalitet, spårbarhet och möjligheten till återkoppling jämfört med en ensam generell agent.

Litteraturstudien pekade tydligt på att en lösning utan någon form av exekverings- eller granskningsfas sällan blir tillräcklig. Eftersom vi inte hade något System Under Test (SUT) valde vi därför att låta en oberoende granskningsagent bedöma testfallen mot kraven. Detta ligger i linje med AgentCoder, där en separat testagent används för att verifiera den genererade lösningen. Även The Rise of Agentic Testing betonar vikten av en oberoende granskningsfunktion för att minska risken att samma agent både producerar och godkänner sitt eget resultat. 

Dessa agenter togs fram med AI-assisterad kodning, kördes först lokalt och publicerades senare publikt på [Hugging Face](../theoretical-background-and-central-concepts/#hugging-face) genom en Docker-baserad lösning. Varje agent var i praktiken en [LLM](../theoretical-background-and-central-concepts/#large-language-models) med en [prompt](../theoretical-background-and-central-concepts/#prompt-engineering) och ett direktiv som beskrev uppgiften och vilken [artefakt](../theoretical-background-and-central-concepts/#artefakt) som skulle produceras.

När de enskilda agenterna var klara blev nästa steg att skapa en fleragentlösning. Den första versionen var sekventiell: krav analyserades, testfall skapades och resultatet granskades därefter. Dessa tidiga experiment kördes med lokala [LLM:er](../theoretical-background-and-central-concepts/#large-language-models), framför allt Llama-baserade modeller via lokal inferens. Det gav praktisk förståelse för hur långt man kunde komma med egen sekventiell [orkestrering](../theoretical-background-and-central-concepts/#orchestrator), men också vilka begränsningar som uppstod i kvalitet, stabilitet och [exekveringstid](../theoretical-background-and-central-concepts/#exekveringstid).

Nästa steg blev att gå över till Hugging Face-baserad körning för de live-LLM:er som användes i arbetsflödet. Därigenom fick vi tillgång till starkare och mer flexibla modeller, samtidigt som vi behöll kontrollen över vår egen agentlogik och experimentmiljö.

## Från sekventiellt flöde till agentisk routing

En viktig insikt var att arbetsflödet inte borde vara strikt synkront i formen `requirements -> design -> review` som ett fast sekventiellt rör. I praktiken visade det sig att agenterna behövde kunna hoppa mellan noder på ett smartare sätt beroende på kvaliteten i mellanresultaten. Det ledde till en mer flexibel orkestrering. Litteraturstudien visar att moderna agentiska system sällan bygger på strikt sekventiella arbetsflöden. I stället används orkestratorer, dynamisk routing och iterativa återkopplingsloopar för att styra samarbetet mellan specialiserade agenter.

För att stödja detta behövdes tre centrala mekanismer:

- privat [agentminne](../theoretical-background-and-central-concepts/#agent-memory) för lokala anteckningar och mellanresultat
- [delat minne](../theoretical-background-and-central-concepts/#shared-working-memory) för gemensam kontext mellan agenterna
- dynamisk routing där nästa steg bestäms utifrån resultat och inte enbart genom hårdkodad stegordning

Uppdelningen mellan privat och delat minne överensstämmer med den minnesmodell som beskrivs i Agents in Software Engineering, där Short-Term Memory, Working Memory, Long-Term Memory och External Memory används för olika delar av agentens resonemang.

Detta ledde fram till en lösning där orkestratorn blev den styrande komponenten. Routing kunde då avgöras utifrån resultat, brister, feedback och stopvillkor i stället för utifrån en helt statisk stegordning. Samtidigt var vissa övergångar fortfarande begränsade. Om Test Design Agent till exempel bedömde att kraven var svaga kunde arbetet skickas tillbaka till Requirements Analyst Agent, och om granskningsagenten inte kunde godkänna resultatet kunde arbetet skickas tillbaka till Test Design Agent för förbättring.

En viktig förfining i denna orkestrering var att formulera målet explicit som att nå `approved=true` från Review Agent, i stället för att använda ett vagare uttryck som `quality sufficient`. Det senare lämnar större tolkningsutrymme för när körningen faktiskt ska stoppas, medan `approved=true` ger ett tydligt [verifieringsmål](../theoretical-background-and-central-concepts/#verification-and-validation), skarpare routingbeslut och bättre [spårbarhet](../theoretical-background-and-central-concepts/#requirement-traceability) i efterhand. För denna POC är därför `approved=true` ett bättre styrmål än ett allmänt kvalitetsuttryck, eftersom orkestratorn då kan arbeta mot en konkret granskningssignal snarare än en diffus kvalitetskänsla.

För att få ännu bättre orkestrering byggdes därefter en [LLM](../theoretical-background-and-central-concepts/#large-language-models)-baserad [orkestrator](../theoretical-background-and-central-concepts/#orchestrator). Detta gav flera förbättringar, framför allt eftersom vi tidigare såg problem med loopar mellan agenter. Liknande problem beskrivs även i MetaGPT, där författarna visar att okontrollerad kommunikation mellan många agenter snabbt leder till ökad tokenförbrukning och mer informationsbrus. Därför används standardiserade arbetsflöden och strukturerad kommunikation mellan agenterna.. De hårdkodade orkestreringsdefinitionerna ledde ibland till loopande diskussioner mellan agenterna och hög tokenförbrukning. Vi behövde därför införa maxgränser för antal cykler och för hur många återkopplingsmeddelanden en agent fick skicka till en annan.

## Nuvarande AI-agent-sida och arkitektur

Den nuvarande AI-agentlösningen kan beskrivas i tre delar:

- den publika agentlösningen använder [Hugging Face](../theoretical-background-and-central-concepts/#hugging-face)-hostade modeller och agentnära körning via [MCP](../theoretical-background-and-central-concepts/#model-context-protocol) och [REST](../theoretical-background-and-central-concepts/#rest-api)
- orkestreringshanteringen i appen är egenutvecklad och innehåller en [LLM](../theoretical-background-and-central-concepts/#large-language-models)-baserad orkestratoragent
- lösningen har ett GUI byggt i [Gradio](../theoretical-background-and-central-concepts/#gradio), där man både kan använda den hostade orkestreringstjänsten och välja egna agentmodeller med egna direktiv

Själva AI-agentdelen byggdes alltså i [Gradio](../theoretical-background-and-central-concepts/#gradio). Ett viktigt skäl var att det redan fanns viss tidigare erfarenhet av Gradio, vilket gjorde det till ett pragmatiskt val för att snabbt få fram en fungerande publik experimentmiljö. Nästa experiment, med [LangGraph](../theoretical-background-and-central-concepts/#langgraph) som orkestrator, kördes däremot i [Streamlit](../theoretical-background-and-central-concepts/#streamlit). Skälet var inte att Streamlit nödvändigtvis var förstahandsvalet i sig, utan att Gradio medförde flera praktiska begränsningar i just den delen av arbetet.

## HF-publicering, endpoints och MCP

Som en del av utvecklingen publicerades agenterna på [Hugging Face](../theoretical-background-and-central-concepts/#hugging-face) så att de blev tillgängliga via publika endpoints och [MCP](../theoretical-background-and-central-concepts/#model-context-protocol)-relaterade integrationsmönster. Detta gjorde att arkitekturen kunde flyttas från enbart lokal experimentkörning till en mer öppen och integrerbar lösning där agenterna kunde användas utanför den lokala appmiljön.

Tidigt i arbetet var tanken att `qa-agent-service`, som blev arbetsnamnet för agentlösningen, skulle bestå av tre separata agenter som kunde anropas via [REST](../theoretical-background-and-central-concepts/#rest-api) och [MCP](../theoretical-background-and-central-concepts/#model-context-protocol), främst via Hugging Face-nycklar. När [Hermes Agent Framework](../theoretical-background-and-central-concepts/#hermes-agent-framework) senare började användas som jämförelse- och integrationsspår blev det tydligt att en bättre lösning var att göra tjänstens REST- och MCP-endpoints publika. På så sätt blev agentservicen enklare att återanvända mellan olika klienter och ramverk, i stället för att vara kopplad till ett mer slutet nyckelberoende upplägg. Detta gjordes med en Dockerlösning.

Detta var en viktig övergång eftersom det gjorde det möjligt att kombinera:

- egen agentdesign och orkestratorlogik
- externa hostade agenttjänster
- framtida integrationer mot verktyg och standardiserade agentgränssnitt

## LangGraph som nästa steg

Efter detta byggdes också en [LangGraph](../theoretical-background-and-central-concepts/#langgraph)-baserad lösning. LangGraph kan beskrivas som ett kodbibliotek inom [LangChain](../theoretical-background-and-central-concepts/#langchain)-ekosystemet för grafbaserad agentisk orkestrering. Det gav ett sätt att uttrycka agentnoder, övergångar och kontrollflöden på ett mer formaliserat sätt.

Den lösningen blev i viss mån lik en MBT-inspirerad struktur, där noder, övergångar och tillstånd blev tydliga. Samtidigt visade arbetet att LangGraph inte på egen hand gav samma enkla agentiska frihet som den egenbyggda lösningen. Jämfört med vår egen arkitektur blev LangGraph-lösningen mer hårdkodad, medan vår egen lösning i högre grad kunde använda en LLM-baserad orkestrator för att styra routingen dynamiskt.

- LangGraph är starkt för explicit grafstruktur och kontroll
- den egenbyggda agentiska lösningen är starkare i dynamisk routing och orkestratorledd flexibilitet

## Observability, direktiv och minnesinsyn

En central designprincip genom hela arbetet var att användaren skulle kunna se vad som skickades in till varje agent, vad som kom ut från varje agent och hur agenten resonerade. Därför byggdes lösningen med tydlig [observability](../theoretical-background-and-central-concepts/#observability) i fokus. GUI-delen ska dock fortfarande betraktas som sekundär i denna POC.

Varje agent fick direktiv som beskrev hur den skulle resonera, vilken roll den hade och vilken kvalitetsnivå som förväntades. Samtidigt exponerades både [delat minne](../theoretical-background-and-central-concepts/#shared-working-memory) och [agentprivat minne](../theoretical-background-and-central-concepts/#agent-memory) i gränssnittet, så att det gick att följa inte bara slutresultatet utan även den interna arbetskontexten under körning.

Detta var viktigt av två skäl:

- för att kunna förstå varför ett resultat blev bra eller dåligt
- för att kunna felsöka routing, minne, feedback och agentbeteende

## Agentdirektiv

I den nuvarande `qa-agent-service` ligger agentbeteendet deklarativt i agentregistret och byggs sedan in i [prompten](../theoretical-background-and-central-concepts/#prompt-engineering) tillsammans med scenario, agentinput, [delat minne](../theoretical-background-and-central-concepts/#shared-working-memory), [agentprivat minne](../theoretical-background-and-central-concepts/#agent-memory), modellkonfiguration, output-kontrakt och strikta JSON-regler.

Dessa direktiv förfinades löpande under arbetet. En viktig fråga var om de skulle kunna justeras under en körning. Forskningslitteraturen tar upp detta, men pekar också på svårigheterna. Exempelvis lyfter Standard Operational Procedures (SOP) att agentinstruktioner bör vara stabila och väldefinierade. Annars riskerar inte bara tokenkostnaderna att öka, utan också bias, fel och hallucinationer att förstärkas mellan agenter.

I den aktuella HF QA agent service-konfigurationen körs samtliga tre agenter normalt med `Qwen/Qwen2.5-7B-Instruct`, med temperatur `0.2` för Requirements Analyst och Test Designer samt `0.1` för Review Agent. Det valet gjordes främst eftersom modellen var gratis, snabb och tillräckligt bra, men den var långt ifrån bäst när vi senare testade mot GPT-5.5 med hjälp av [Hermes Agent Framework](../theoretical-background-and-central-concepts/#hermes-agent-framework).

Litteraturstudien visar att högkvalitativ testdesign kräver mer än generering av välformulerade testfall. Studien Automatic High-Level Test Case Generation using Large Language Models visar att generativa modeller ofta kan skapa testfall som ser strukturerade och rimliga ut, men att de fortfarande kan missa viktiga edge cases, använda för generell testdata eller sakna tillräcklig domänförankring. Detta motiverar att Test Design Agent i POC:en har ett tydligt kvalitetskontrakt med krav på konkreta preconditions, testdata, steg, förväntade resultat, oracle-logik och spårbarhet till krav-ID.

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

Flera forskningsartiklar betonar vikten av tydliga och stabila agentinstruktioner. MetaGPT beskriver detta genom konceptet Standard Operating Procedures (SOP), där varje agent arbetar efter tydligt definierade arbetsuppgifter och producerar standardiserade artefakter. Detta minskar både informationsbrus och risken för att felaktiga antaganden sprids mellan agenterna.

## Loopar, begränsningar och approve true

Ett återkommande problem var att agenterna ibland hamnade i loopar där de skickade feedback fram och tillbaka utan att faktiskt nå ett tillräckligt bra slutresultat. För att hantera detta infördes begränsningar i:

- totalt antal rundor
- totalt antal feedbackmeddelanden
- antal feedbackmeddelanden mellan samma agentpar

Detta blev centralt i arkitekturen eftersom målet var att Review Agent i slutänden helst skulle kunna sätta `approve = true`. I praktiken visade det sig att detta var svårt att uppnå konsekvent. Vid vissa enstaka körningar gick det, men generellt var det betydligt svårare än väntat att få hela kedjan att nå ett robust godkänt slutläge.

## Utvärderingsfrågan

En viktig del av arbetet blev därför frågan om hur output från Test Design Agent faktiskt ska utvärderas. Denna utmaning beskrivs också i Automatic High-Level Test Case Generation using Large Language Models. Författarna visar att automatiska kvalitetsmått, såsom F1-score och BERTScore, endast ger en del av bilden. För att bedöma om testfall verkligen är användbara krävs även mänsklig expertgranskning, särskilt när det gäller domänkunskap, edge cases och relevansen hos testdata. Det räcker inte att agenten producerar många testfall, den avgörande frågan är hur relevanta, testbara, spårbara och granskningsbara dessa testfall är. På samma sätt uppstod frågan om hur starkt review-steget egentligen är: hur bra är Review Agent på att skilja mellan ytliga och verkligt robusta testdesigner? Detta ligger i linje med Automatic High-Level Test Case Generation using Large Language Models, där författarna visar att den svåraste delen vid AI-genererad testdesign inte bara är att producera testfall, utan att förstå domänkontexten och avgöra vad som faktiskt bör testas. Studien visar också att automatiska mått som F1-score, BERTScore och semantiska likhetsmått kan ge viss information om likhet och språklig kvalitet, men att de inte fullt ut fångar testfallens praktiska värde. Därför behöver automatiska mått kompletteras med expertgranskning, särskilt för att bedöma edge cases, testdata och domänspecifika scenarier.

Denna utvärderingsfråga är en av de mest centrala slutsatserna hittills. Systemet kan producera artefakter, men det är betydligt svårare att med hög tillförlitlighet avgöra när kvaliteten verkligen är tillräcklig. I både den interna lösningen och LangGraph-lösningen är testfallen nedladdningsbara för vidare utvärdering. Tanken var att använda exempelvis [DeepEval](../theoretical-background-and-central-concepts/#deepeval), men också senior QA-erfarenhet från praktiskt arbete i rollen som QA-expert.

## Standardscenarier för jämförelse

För att kunna jämföra lösningar mer systematiskt skapades sex standardscenarier:

- Scenario 1 - login and registration
- Scenario 2 - e-commerce checkout
- Scenario 3 - password reset
- Scenario 4 - support tickets
- Scenario 5 - inventory management
- Scenario 6 - course enrollment

Dessa används som återkommande testfall i de olika lösningarna för att kunna jämföra routing, kravanalys, testdesign, reviewbeteende, observability och sannolikheten att nå ett godkänt resultat.

## Hermes

Nästa steg i arbetet blev att undersöka om [Hermes Agent Framework](../theoretical-background-and-central-concepts/#hermes-agent-framework) kunde tillföra något som saknades i de tidigare lösningarna. Det gör Hermes relevant både som jämförelseobjekt och som möjlig inspirationskälla för hur agentstruktur, kommunikation och styrning kan organiseras framåt.

## Hermes-resultat som jämförelsepunkt

Ett viktigt delresultat var att Hermes Agent kunde skapa en fungerande testcase-generator relativt snabbt. Detta är i sig en viktig observation för POC-resultatet: det var enkelt att få fram en tydlig multi-agentliknande QA-struktur i Hermes utan att först behöva bygga all orkestreringslogik från grunden.

Den Hermes-lösning som togs fram var en Kanban Swarm med följande struktur:

- en root task som fungerade som [shared blackboard](../theoretical-background-and-central-concepts/#shared-blackboard)
- en Requirements Analyst
- en Test Designer
- en QA Risk Reviewer
- en Verifier
- en [Synthesizer](../theoretical-background-and-central-concepts/#synthesizer)

Det är viktigt att förtydliga att både **[shared blackboard](../theoretical-background-and-central-concepts/#shared-blackboard)** och **[Synthesizer](../theoretical-background-and-central-concepts/#synthesizer)** här tillhör Hermes Agent-lösningen. De är alltså inte delar av den egenbyggda HF QA agent service-lösningen eller den interna orkestratorarkitekturen i appen.

Flödet var i praktiken:

- krav in
- shared blackboard / root task
- parallella specialist-workers
- verifier gate
- synthesizer
- slutlig testdesign

Även detta flöde beskriver Hermes-spåret specifikt. I den egenbyggda lösningen används i stället en egen orkestrator, delat minne, agentprivat minne och routing mellan Requirements Analyst, Test Design och Review Agent.

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

Samtidigt måste jämförelsen beskrivas ärligt: Hermes-lösningen kördes med en betydligt starkare modellmiljö, i detta fall GPT-5.5, medan den nuvarande HF QA agent service-lösningen i stor utsträckning har byggt på mindre modeller som Qwen eller Qwen2.5-7B-Instruct. Detta stöds även av litteraturen om kravbaserad testfallsgenerering. Studien Automatic High-Level Test Case Generation using Large Language Models visar att modelljämförelser inte enbart bör tolkas utifrån modellstorlek. Mindre modeller kan prestera väl om de är domänanpassade, medan större generella modeller kan ge bättre språk och struktur men ändå missa domänspecifika edge cases. Därför bör skillnaderna mellan Hermes och HF QA agent service förstås som en kombination av modellkapacitet, domänkontext, promptning och agentarkitektur.

Det betyder att en direkt kvalitetsjämförelse mellan resultaten inte utan vidare är rättvis. Resultaten i litteraturstudien visar också att modellstorlek inte ensamt avgör kvaliteten. Automatic High-Level Test Case Generation using Large Language Models visar att mindre modeller kan prestera mycket väl om de är anpassade till rätt domän och har tillgång till relevant kontext. Skillnaderna mellan Hermes och den egna lösningen bör därför inte enbart tillskrivas modellkapacitet utan även skillnader i domänkontext, promptning och agentarkitektur. 

Samtidigt pekar resultaten på att mycket stora generella modeller inte alltid måste vara det mest relevanta valet för just den här typen av uppgift. I det här projektet är vi inte ute efter en modell som kan göra "allt", utan efter en modell som är bra på att tolka krav, resonera om testbarhet och ta fram användbara testartefakter. Litteraturen pekar också på att mindre modeller kan fungera mycket bra när de är anpassade till rätt domän eller får rätt kontext.

Skillnader i output kan bero på minst tre saker:

- skillnader i ramverk och orkestreringsmodell
- skillnader i promptning, verifiering och artefaktstruktur
- skillnader i ren modellkapacitet

Det är därför viktigt att rapporten inte framställer Hermes-resultatet som bättre enbart för att slutartefakten blev starkare. En del av styrkan kan mycket väl bero på att GPT-5.5 är en betydligt starkare modell än den mindre Qwen-varianten i HF-lösningen.

## Vad jämförelsen ändå visar

Trots denna begränsning visar Hermes-körningen flera saker som är värdefulla för POC-resultatet:

- det är enkelt att få fram en användbar testcase-generator i Hermes
- rolluppdelningen blir tydlig och lätt att beskriva
- blackboard-, verifier-gate- och synthesizer-mönstret i Hermes fungerar väl för QA-liknande artefaktflöden
- Hermes ger ett konkret jämförelseobjekt för hur snabbt man kan nå ett användbart resultat med ett externt agentramverk

Detta är därför inte bara ett alternativt experiment, utan också ett argument för att extern ramverksjämförelse är relevant: vissa ramverk kan ge snabbare väg till fungerande agentflöden, medan den egenbyggda lösningen i stället ger större kontroll över routing, minne, observability och framtida utbyggnad.

## Tokenförbrukning i den egenbyggda lösningen

En viktig ny observation i arbetet är att tokenförbrukningen nu går att följa även för den egenbyggda lösningen när `qa-agent-service` används som agentbackend. Det gör att jämförelsen mot Hermes inte längre enbart kan handla om slutkvalitet, utan också om hur mycket modellarbete som faktiskt krävs för att nå ett visst resultat.

Det mest centrala resultatet är att tokenkostnaden i våra sex scenariokörningar inte främst verkar drivas av någon allmän "agentchatt" mellan rollerna. Orchestrator-stegen står i dessa körningar för routing och stoppsignaler, men har inga egna tokenvärden i exporterna. I stället ligger nästan hela tokenförbrukningen i de steg där Requirements Analyst, Test Design Agent och Review Agent anropar modellbackend.

Det går också att se att kostnaden inte främst ligger i den första requirementsanalysen. Den är relativt billig och stabil mellan scenarierna. Den stora kostnaden uppstår i stället i den upprepade loopen mellan Test Design Agent och Review Agent. När Review Agent inte godkänner resultatet skickas feedback tillbaka till Test Design Agent, som måste läsa in krav, tidigare testdesign, feedback och övrig arbetskontext på nytt. Därefter gör Review Agent motsvarande omtag med ett större underlag än i föregående cykel. Detta innebär att varje extra cykel normalt kostar betydligt mer än den första grundrundan.

I de sex insamlade körningarna användes samma defaultgränser: `max_rounds = 10`, `max_feedback_messages = 12` och `max_feedback_per_agent_pair = 4`. Trots detta stannade samtliga körningar praktiskt på fem iterationer och fyra feedbackomgångar, där all feedback gick från Review Agent till Test Design Agent. Det betyder att det inte var den totala round-gränsen som i praktiken styrde stoppet, utan den mer specifika begränsningen för hur många gånger samma agentpar fick loopa.

Mätningen visar därför tre viktiga saker:

- den största tokenkostnaden ligger i återkommande design- och review-loopar, inte i orkestratorns routing
- varje extra cykel blir successivt dyrare, vilket tyder på att mer kontext och fler tidigare artefakter förs vidare i promptarna
- Requirements Analyst står bara för en liten del av den totala kostnaden, medan Test Design Agent och Review Agent tillsammans dominerar nästan hela tokenförbrukningen

Detta ger i sin tur en praktisk slutsats för fortsatt utveckling. Om målet är att minska kostnaden räcker det inte i första hand att byta modell eller sänka temperatur. Det viktigaste är sannolikt att minska mängden kontext som skickas in igen i varje design- och review-loop, eller att höja kvaliteten i första designomgången så att färre backtracking-cykler behövs. Det kan exempelvis handla om bättre selektion av vilka krav och vilka reviewfynd som verkligen måste skickas vidare, tydligare komprimering av tidigare artefakter eller ett mer begränsat återkopplingsformat mellan Review Agent och Test Design Agent.

För att göra detta spår transparent finns en separat bilaga med tabeller över scenario 1 till 6, inklusive jämförelse mot Hermes mätbara tokenanvändning och en uppdelning av vad som utgör grundrunda respektive extra cykler. Se [Bilaga: Tokenjämförelse mellan Hermes och vår egen QA agent service](../token-jamforelse-hermes-vs-qa-agent-service-sv/).

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

I Hermes-fallet var orkestreringen tydligt uttryckt genom Kanban tasks, [shared blackboard](../theoretical-background-and-central-concepts/#shared-blackboard) och en avslutande [synthesizer](../theoretical-background-and-central-concepts/#synthesizer)-roll. I HF-lösningen ligger motsvarande styrka mer i den egenbyggda orkestratorn, det delade minnet, agentprivat minne, feedbackbegränsningarna och den tydliga runtime-insynen i appen.

### Jämförelse mellan lösningarna

I jämförelsen är det viktigt att skilja på själva agentramverket och den underliggande agentservicen. Både den egenbyggda `ai_agent`-lösningen och LangGraph-lösningen använder HF QA agent service som agentbackend, medan Hermes Agent Kanban-lösningen kördes som en separat swarm-struktur.

| Dimension | Vår egen ai_agent-lösning | LangGraph-lösning | Hermes Agent Kanban-lösning |
|---|---|---|---|
| Agentbackend | HF QA agent service | HF QA agent service | Hermes/Kanban swarm med GPT-5.5 i den körning som testades |
| Modellstyrka | Främst Qwen / Qwen2.5-7B-Instruct i nuvarande jämförelse | Främst Qwen / Qwen2.5-7B-Instruct i nuvarande jämförelse | GPT-5.5 |
| Orkestrering | Egenbyggd orkestrator i appen | Grafbaserad orkestrering i LangGraph | Kanban tasks, shared blackboard och synthesizer i Hermes-swarmspåret |
| Rollseparation | Tydlig och styrd av egen arkitektur | Tydlig, men mer formellt definierad via grafnoder | Mycket tydlig och snabb att etablera |
| Routing | Dynamisk routing via orkestrator och selektiv backtracking | Mer grafstyrd och mer explicit definierad i flödet | Mer workflow-styrd via swarm-struktur |
| Minne | Delat minne, agentprivat minne och memory timeline | Beror på graf- och state-implementationen, men stödjer tydligt state-flöde | Blackboard-liknande delning mellan tasks |
| Verifiering | Review Agent och stopvillkor, men `approve = true` har varit svårt att nå konsekvent | Kan bygga in review- och verifieringssteg, men mer explicit i flödesdefinitionen | Tydlig verifier gate före Hermes Synthesizer |
| Observability | Stark GUI-insyn i input, output, resonemang, minne och runtime events | Bra spårbarhet i graf och nodflöden, men mindre integrerad än vår egen GUI-lösning | Kanban/task-spår och artefakter |
| Styrka | Stark forskningsplattform för routing, minne, observability och utvärdering | Stark för explicit grafstruktur, nodstyrning och MBT-liknande modellering | Snabb väg till komplett testcase-generator |
| Begränsning | Resultatet påverkas av mindre modeller och svårigheten att nå stabil `approve = true` | Kan bli mer hårdkodad och mindre fri i dynamisk agentisk routing | Styrkan påverkas sannolikt av den större modellen |

Tabellen ska inte tolkas som att en lösning generellt är bäst. Den visar snarare att lösningarna har olika styrkor: den egenbyggda `ai_agent`-lösningen ger störst kontroll över agentiskt beteende och observability, LangGraph ger en stark och tydlig grafmodell för flöden och tillstånd, medan Hermes Agent Kanban-lösningen visar hur snabbt man kan få fram en användbar testcase-generator i ett externt agentramverk.

## Slutsats om Hermes i rapporten

Delar av Hermes-resultatet bör därför finnas med i POC-rapporten som stöd för två slutsatser:

- det är förhållandevis enkelt att i Hermes skapa en testcase-generator med flera QA-liknande roller
- jämförelsen mot den egna HF QA agent service-lösningen måste göras med tydlig reservation för att modellerna inte är likvärdiga

En korrekt tolkning är därför att Hermes visade hög praktisk produktivitet och snabb väg till ett fungerande QA-flöde, medan den egna lösningen fortfarande är starkare som forskningsplattform för att studera routing, minne, observability, feedbackloopar och agentiskt beteende på mer detaljerad nivå.

## Slutsatser

Den nuvarande QA-agent-POC:n har nu nått en nivå där den ger en praktisk förståelse för flera centrala agentbegrepp som tidigare endast fanns som teori i projektbriefen. Flera av de designval som implementerats i POC:en återkommer också i den genomgångna litteraturen. Exempel är användningen av specialiserade agentroller, en central orkestrator, gemensamt arbetsminne, iterativa återkopplingsloopar och en oberoende granskningsfunktion. Detta stärker att den utvecklade lösningen ligger nära de arkitekturprinciper som idag dominerar forskningen inom agentiska system för Software Engineering och Software Quality Assurance. POC:n visar i körbar form hur ett fleragentsystem kan organiseras kring specialiserade roller, styras av en orkestrator och kombineras med både strukturerad baslinjekörning och LLM-backed körning.

Det som nu tydligt är uppnått är:

- specialiserade agentroller med tydligt ansvar
- orkestratorstyrd routing
- selektiv backtracking i stället för endast full rerun
- delat arbetsminne och agentprivat minne
- per-agent modell-, provider-, timeout- och direktivkonfiguration
- runtime-insyn genom GUI, runtime activity och live log
- bevarande av delresultat vid fel
- stöd för både lokal Ollama-körning och externa modellstrategier

Detta innebär att projektet i hög grad har uppnått målet att förstå vad agentiska system är på en praktisk nivå, särskilt inom ett QA-orienterat arbetsflöde. Systemet visar inte bara att flera agenter kan existera samtidigt, utan också hur routing, återkoppling, minne, observability och styrbar exekvering påverkar resultatet.

Samtidigt återstår viktiga steg innan lösningen kan beskrivas som ett mer generellt agentramverk:

- agentexpansion är fortfarande kodnära och inte fullt dynamisk
- tool-runtime och MCP-baserad integration är ännu inte en central del av arkitekturen
- persistence och checkpointing är inte generiska på ramverksnivå
- jämförelsen mot externa agentramverk är ännu inte genomförd empiriskt i samma detalj som den interna POC:n
- resultaten av testcase-genereringarna för scenarierna i de olika lösningarna har ännu inte granskats i detalj

En intressant fortsättning vore därför att undersöka hur enkelt det skulle vara att träna eller finjustera en mindre modell för just den här typen av QA-orienterade uppgifter. Om en mindre och mer nischad modell kan ge jämförbar kvalitet i kravtolkning och testdesign skulle det kunna ge lägre kostnad, snabbare körning och större kontroll över lösningen.

Den mest korrekta tolkningen i detta läge är därför att projektet har nått målet att förstå och demonstrera centrala agentegenskaper, men att nästa steg är att jämföra denna POC mer systematiskt mot etablerade agentplattformar och att avgöra vilka delar som bör behållas, generaliseras eller ersättas. Det vore också mycket intressant att prova detta i praktiken hos ett företag.
