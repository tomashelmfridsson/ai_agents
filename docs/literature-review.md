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

Beskrivning av den föreslagna arkitekturen.

- Orchestrator Agent
- Requirements Analyst Agent
- Test Design Agent
- Test Generation Agent
- Review Agent

---

<a id="designbeslut"></a>

# 6. Designbeslut

Motivering av arkitektur- och teknikval.

---

<a id="prototyp-och-implementation"></a>

# 7. Prototyp och implementation

Beskrivning av implementationen.

---

<a id="experiment-och-utvardering"></a>

# 8. Experiment och utvärdering

Föreslagna utvärderingsmått:

- Kravtäckning
- Kodtäckning
- Test Pass Rate
- Exekveringstid
- Antal iterationscykler
- Kodkvalitet

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
