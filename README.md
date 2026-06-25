---
title: ai_agents
sdk: gradio
app_file: app.py
pinned: false
---

# Agentisk QA-plattform för kravbaserad testdesign

Detta repo innehåller en startpunkt för sommarprojektet:

1. `docs/` samlar forskningsfråga, litteraturspår och utvärderingsram.
2. `src/qa_platform/` innehåller en körbar demonstrator med orkestrator och specialiserade agenter.
3. `tests/` verifierar kärnflödet för krav -> analys -> testdesign -> testgenerering -> granskning.

## Projektmål

Att undersöka hur ett agentiskt QA-system kan transformera naturligt språk i kravspecifikationer till verifierbara testartefakter, med fokus på:

- orkestrering
- specialiserade agentroller
- iterationsloopar
- spårbarhet mellan krav och tester

## Arkitektur

Demonstratorn innehåller följande roller:

- `OrchestratorAgent`: styr arbetsflöde, iterationer och samordning.
- `RequirementsAnalystAgent`: extraherar strukturerade krav och acceptanskriterier.
- `TestDesignAgent`: föreslår testtyper, testfall, teststeg och orakel.
- `TestGenerationAgent`: genererar konkreta testartefakter och testdatautkast.
- `ReviewAgent`: granskar täckning, kvalitet och beslutar om godkännande eller ny iteration.

## Kom igång

Starta webbappen lokalt med Gradio:

```bash
pip install -r requirements.txt
python3 app.py
```

Repot använder samma Gradio-version som Hugging Face Space-byggmiljön för att undvika versionskonflikter vid deploy.

Öppna sedan den lokala Gradio-adressen som skrivs ut i terminalen, normalt `http://127.0.0.1:7860`.

Litteraturstudien öppnas i en separat flik via den publika Markdown-filen i repot.

Kör tester:

```bash
python3 -m unittest discover -s tests
```

## Struktur

```text
.
├── app.py
├── docs
│   ├── literature-review.md
│   └── project-framework.md
├── src
│   └── qa_platform
│       ├── __init__.py
│       ├── agents.py
│       ├── models.py
│       ├── orchestrator.py
│       └── web.py
└── tests
    └── test_pipeline.py
```

## Nästa steg

- koppla varje agent till valbar modellbackend, exempelvis Ollama eller moln-API
- lägga till persistens för tidigare tester och kravspårbarhet
- komplettera med faktisk kodanalys, exekvering av genererade tester och mätvärdesinsamling
- anpassa `app.py` för deploy i Hugging Face Spaces med Gradio som värdruntime
