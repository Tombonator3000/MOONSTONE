# Originalformbundet Moonstone-logo

`packed/bold.f/073.png` er en uaktivert kandidat i 1220 × 216. Alle bokstaver, de tre O-enes innvendige diamantformer, undertittelen og svarte skygger kommer fra originalens `bold.f`, rute 73. Ingen alternativ skrifttype eller bokstavgeometri fra rågenereringen brukes.

Råkandidaten `raw/logo-v1.png` avvek i form og tittel-/undertittelforhold. Den brukes bare som materialkilde: ett sammenhengende gullfelt på 48 × 48 piksler gir dempet luminansstruktur innenfor originalens gullflate. Originalens fargeindeksregioner bestemmer lys- og skyggeplasseringen. Gullpaletten og materialets begrensede kontrast står eksplisitt i `contract.json`. Dette er kildebevarende materialpakking, ikke en ny font eller en påstand om separat håndnytegning av hver bokstav.

`comparison.png` viser nærmeste-nabo-original øverst og kandidaten nederst. `verification/packing.json` binder faktisk kandidat-SHA til kontrakten og originalkildene. En uavhengig JavaScript-CEL-dekoder kontrollerer planmasken og alle 16 470 kildepikselmidtpunkter. Synlig flate, skygge, sammenhengende deler og samtlige originale hull kontrolleres også etter pakking. Originalen og full kildegeometri ligger under `source/`.

Gjenbygg fra reporoten:

```sh
python3 tools/hd_completion_logo_build.py
node tools/hd_completion_logo_pack.cjs
```

Node krever Playwright og Chrome, som prosjektets øvrige grafikkprøver. Verktøyene skriver bare til denne artmappen. `proposed_text_metadata` i kontrakten er et forslag som må aktiveres separat sammen med PNG og manifesthash; produksjonsmetadata endres ikke. Visuell vurdering i selve tittelbildet og Original/HD-retur gjenstår før levering.
