# AI Guidelines

Detta dokument beskriver hur AI-assistenten ska arbeta i detta repo.

## Arbetsprinciper

1. AI-assistenten ska i normalfallet försöka lösa problem själv innan användaren störs med onödiga frågor.
2. AI-assistenten får göra upp till tre seriösa försök att lösa ett problem själv innan problemet eskaleras till användaren.
3. Varje försök ska vara tydligt avgränsat och bygga på faktisk analys, verifiering eller implementation, inte bara omformulering av samma idé.
4. Om problemet fortfarande inte är löst efter tre försök ska AI-assistenten:
   - beskriva vad som har provats
   - beskriva varför det inte fungerade
   - föreslå nästa rimliga väg framåt

## Acceptanskriterier

1. Varje ny uppgift ska ha ett eller flera acceptanskriterier.
2. AI-assistenten ska alltid föreslå acceptanskriterier tidigt i arbetet.
3. Acceptanskriterierna ska fastställas tillsammans med användaren innan större implementationer görs, när det är praktiskt möjligt.
4. Acceptanskriterierna ska uttryckligen godkännas av användaren innan AI-assistenten börjar implementera en lösning.
5. Om användaren ger en enkel och tydlig uppgift kan AI-assistenten föreslå acceptanskriterier, men implementation ska ändå vänta tills användaren har godkänt dem.
6. Acceptanskriterier ska vara testbara, konkreta och kopplade till observerbart beteende.
7. Varje acceptanskriterium ska ha en rimlig verifieringsmetod som går att genomföra i praktiken.

## Format för acceptanskriterier

AI-assistenten bör som standard formulera acceptanskriterier i stil med:

- `När` användaren utför en viss handling, `ska` ett visst resultat uppstå.
- `När` ett fel inträffar, `ska` systemet ge ett tydligt och verifierbart felbeteende.
- `När` uppgiften är klar, `ska` det gå att verifiera resultatet genom kod, test, UI eller logg.

## Exempel på arbetssätt

För varje uppgift bör AI-assistenten om möjligt börja med:

1. En kort sammanfattning av uppgiften.
2. Ett förslag på acceptanskriterier.
3. Genomförande.
4. Verifiering mot acceptanskriterierna.

## Verifiering

1. Verifieringsmetoden ska matcha typen av acceptanskriterium.
2. Buildstatus, deploystatus, loggar och `curl` är inte tillräckliga som enda verifiering för UI- eller browserbeteenden.
3. Om ett acceptanskriterium gäller klick, rendering, ny flik, navigation eller annat klientbeteende ska det verifieras i en faktisk browsermiljö när det är möjligt.
4. Om full verifiering inte har kunnat göras ska detta sägas uttryckligen, och acceptanskriteriet ska inte beskrivas som uppfyllt.
5. AI-assistenten ska skilja tydligt på:
   - vad som är implementerat
   - vad som är verifierat
   - vad som bara är sannolikt eller preliminärt

## Eskalering

AI-assistenten ska eskalera tidigare än tre försök om:

- uppgiften riskerar att förstöra data eller miljö
- nödvändiga behörigheter saknas
- användarbeslut krävs för att välja mellan flera rimliga vägar
- externa system blockerar fortsatt framdrift
