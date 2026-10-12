/*
 * sprak.js - spraaket paa nettsiden.
 *
 * Kildeteksten i koden er norsk. Engelsk er standard, og norsk kan velges i
 * sidemenyen («Language / Språk»). Valget lagres i innstillingene (sprak: 'en'
 * eller 'no').
 *
 * De faste tekstene i index.html er engelske, saa siden er engelsk fra foerste
 * bilde og for dem som leser den uten JavaScript (soekemotorer, forhaandsvisning
 * av lenker). Sprak.start finner den norske kilden ved aa slaa opp den engelske
 * teksten baklengs i ordboken, saa en fast tekst i index.html maa vaere helt lik
 * den engelske teksten i ordboken.
 *
 *   T(tekst, ...verdier)   teksten paa valgt spraak. {0}, {1} ... byttes med
 *                          verdiene. Tekster som ikke finnes i ordboken, kommer
 *                          tilbake som de er (navn, chat, engelsk tekst).
 *   Sprak.sett(el, tekst, ...verdier)
 *                          setter teksten i et element og husker kilden, saa den
 *                          tegnes paa nytt naar spraaket byttes. Elementer med
 *                          klassen pt (spillets font) tegnes med Spillgrafikk.sett.
 *                          En verdi kan vaere en funksjon; den kalles ved hver tegning.
 *   Sprak.start(sprak)     leser de faste tekstene i index.html, finner den norske
 *                          kilden og tegner dem paa valgt spraak.
 *   Sprak.bytt(sprak)      bytter spraak og tegner alle kjente tekster paa nytt.
 *
 * Teksten i selve spillet (tittelmenyen, kartet) er engelsk og oversettes ikke.
 * Meldinger fra kjernen (C) er norske og staar ogsaa i ordboken.
 */
'use strict';

const Sprak = (() => {
    /* norsk kildetekst -> engelsk. Avsnitt med lenker og fet skrift er HTML. */
    const EN = {
        /* ---------------- index.html: knapper og overskrifter (spillets font) */
        'Inventar': 'Inventory',
        'Slutt tur': 'End turn',
        'Valg': 'Choices',
        'Skriv navn': 'Enter name',
        'Meny': 'Menu',
        'Meny (Home)': 'Menu (Home)',
        'Navnet ditt': 'Your name',
        'Avbryt': 'Cancel',
        'Navnet til ridderen': "Your knight's name",
        'Bli med i et rom': 'Join a room',
        'Bli med': 'Join',
        'Romkode eller lenke': 'Room code or link',
        'Tilbake til spillet': 'Back to the game',
        'Bilde og lyd': 'Picture and sound',
        'Hele PAL-bildet (med kanter)': 'Full PAL picture (with borders)',
        'Lydstyrke': 'Volume',
        'Vent på fire før kamp': 'Wait for fire before battles',
        'Styrekors og knapper også med mus': 'On-screen controls with a mouse too',
        'Effekter': 'Effects',
        'Skygger under figurer og tekst': 'Shadows under figures and text',
        'Litt uskarp bakgrunn': 'Slightly soft background',
        'Glød rundt lyse ting': 'Glow around bright things',
        'Sterkere og varmere farger': 'Richer, warmer colours',
        'Mørkere hjørner': 'Darker corners',
        'HD-grafikk': 'HD graphics',
        'Grafikk': 'Graphics',
        'Gult felt der HD-bilde mangler': 'Yellow box where an HD image is missing',
        'Velg HD-mappe': 'Choose HD folder',
        'Standardgrafikk': 'Standard graphics',
        'Fjern': 'Remove',
        'Lagre bakgrunnen': 'Save background',
        'Lagring': 'Saves',
        'Plass': 'Slot',
        'Lagre': 'Save',
        'Last': 'Load',
        'Fortsett': 'Load autosave',
        'Last ned': 'Download',
        'Hent fra fil': 'Load from file',
        'Nettspill': 'Online game',
        'Kopier lenken': 'Copy link',
        'Spillfil og egne filer': 'Game file and your own files',
        'Velg spillfil': 'Choose game file',
        'Legg til filer': 'Add files',
        'Fjern alle': 'Remove all',
        'Taster': 'Controls',
        'Start spillet på nytt': 'Restart the game',
        'Forlat rommet': 'Leave the room',
        'Forlat nettspillet og start på nytt': 'Leave and restart',
        'Skriv en melding og trykk Enter': 'Type a message and press Enter',
        'Laster spillet ...': 'Loading the game ...',
        'Moonstone (Mindscape 1991) i nettleseren, kjørt fra originalkoden, med nettspill for opptil fire.':
            'Moonstone (Mindscape 1991) in your browser, running the original code, with online play for up to four.',

        /* ---------------- index.html: valglister og verdier */
        'Skarp': 'Sharp',
        'Rene piksler': 'Clean pixels',
        'Myk': 'Soft',
        'Glatt (Scale4x)': 'Smooth (Scale4x)',
        'PAL (kvadratiske piksler)': 'PAL (square pixels)',
        'HD der den finnes': 'HD where available',
        'På': 'On',
        'Av': 'Off',
        'Plass {0}': 'Slot {0}',

        /* ---------------- index.html: hjelpetekster (HTML) */
        'Vises for de andre i nettspillet.': 'Shown to the other players online.',
        'Bokstaver, tall og mellomrom, opptil 13 tegn.': 'Letters, numbers and spaces, up to 13 characters.',
        'Skriv romkoden (seks tegn) eller lim inn invitasjonslenken.': 'Type the room code (six characters) or paste the invite link.',
        'ButtonWait: kampen venter på fire, så du får tid til å lese. Gjelder fra neste start.':
            'ButtonWait: battles wait for fire, so you have time to read. Takes effect the next time the game starts.',
        'Spillet tegnes i lag: bakgrunn, figurer og tekst hver for seg. Effektene bruker det.':
            'The game is drawn in layers: background, figures and text separately. The effects use that.',
        'Med HD valgt lastes fotografisk standardgrafikk automatisk: bakgrunner, blå ridderbevegelse, riddervalg, menypil og månefaser. Øvrige animasjoner bruker foreløpig originalgrafikk. Du kan også velge egne HD-bilder.':
            'With HD on, photographic standard graphics load automatically: backgrounds, the blue knight walking, knight selection, the menu pointer and moon phases. Other animations still use the original graphics. You can also pick your own HD images.',
        'Bakgrunner: lagre den som vises, tegn den i høyere oppløsning, og legg den i mappen <code>bg</code> i HD-pakken med samme navn.':
            'Backgrounds: save the one on screen, redraw it at a higher resolution and put it in the <code>bg</code> folder of the HD pack with the same name.',
        'Spillet lagres i denne nettleseren. Det lagres også automatisk når du bytter fane eller app, og hvert andre minutt. Lagringene kan lastes ned og flyttes mellom nettleser og PC.':
            'Your game is saved in this browser. It also saves automatically when you switch tab or app, and every two minutes. Saves can be downloaded and moved between browser and PC.',
        'Ingen automatisk lagring ennå.': 'No autosave yet.',
        'Moonstone har to joystickporter. Joystick 1 (port 2) brukes på kartet, i kamp mellom to riddere brukes begge. Spillere på samme joystick deler den som ved et vanlig bord: den som har turen, styrer.':
            'Moonstone has two joystick ports. Joystick 1 (port 2) is used on the map; in a fight between two knights both are used. Players on the same joystick share it like at a real table: whoever has the turn is in control.',
        'Spillfilen (Moonstonecd32-AMIGA.zip) er bygget inn i siden. Vil du bruke en annen, f.eks. «Moonstone CD32.iso», velger du den her. Gjester i nettspill trenger ingen spillfil.':
            'The game file (Moonstonecd32-AMIGA.zip) is built into the page. To use another one, such as “Moonstone CD32.iso”, choose it here. Guests in online games don’t need a game file.',
        'Filer laget med <code>tools/gfx.py build</code> (f.eks. bg1a.PIV) brukes i stedet for originalene i data/, og <code>tekster.txt</code> fra <code>tools/tekst.py</code> endrer tekstene i spillet. De brukes når spillet startes på nytt. I nettspill får gjestene dem fra verten.':
            'Files made with <code>tools/gfx.py build</code> (such as bg1a.PIV) replace the originals in data/, and <code>tekster.txt</code> from <code>tools/tekst.py</code> changes the texts in the game. They are used when the game restarts. In online games, guests get them from the host.',
        'Ingen egne filer.': 'No files of your own.',
        '<b>Introen:</b> Esc, fire, Enter eller et trykk på skjermen hopper over den.':
            '<b>Intro:</b> Esc, fire, Enter or a tap on the screen skips it.',
        '<b>Menyene i spillet:</b> klikk eller trykk på et valg, eller bruk piltastene og Enter (eller fire).':
            '<b>Game menus:</b> click or tap an item, or use the arrow keys and Enter (or fire).',
        '<b>Valgene på kartet</b> (fire på et sted): trykk på et valg under bildet, bruk styrekorset og Fire, eller tastene 1-9.':
            '<b>Choices on the map</b> (fire on a location): tap a choice below the picture, use the d-pad and Fire, or the keys 1-9.',
        '<b>Musen:</b> utenfor menyene er venstre knapp fire. Hold den og dra for fire og retning (angrepene i kamp). Høyre knapp og dra er bare retning.':
            '<b>Mouse:</b> outside the menus the left button is fire. Hold it and drag for fire plus a direction (the attacks in battle). Right button and drag is direction only.',
        '<b>Nettspill:</b> velg <b>Options</b> og <b>Online Game</b> i spillets meny.':
            '<b>Online play:</b> choose <b>Options</b> and <b>Online Game</b> in the game menu.',
        '<b>Kontrollene:</b> tastene og knappene under kan endres i spillets meny, under <b>Options</b> (Keyboard og Gamepad). Listen viser standardoppsettet.':
            '<b>Controls:</b> the keys and buttons below can be changed in the game menu under <b>Options</b> (Keyboard and Gamepad). The list shows the defaults.',
        '<b>Joystick 1:</b> piltastene, Ctrl er fire. Spillkontroller 1.':
            '<b>Joystick 1:</b> arrow keys, Ctrl is fire. Gamepad 1.',
        '<b>Joystick 2:</b> talltastaturet 8 2 4 6 (7 9 1 3 på skrå), 0 er fire. Spillkontroller 2.':
            '<b>Joystick 2:</b> keypad 8 2 4 6 (7 9 1 3 diagonally), 0 is fire. Gamepad 2.',
        '<b>Mellomrom:</b> inventaret til ridderen. <b>E:</b> avslutt turen.':
            '<b>Space:</b> the knight’s inventory. <b>E:</b> end your turn.',
        'I kamp: hold fire og trykk en retning for de åtte angrepene (se manualen).':
            'In battle: hold fire and press a direction for the eight attacks (see the manual).',
        '<b>Home:</b> denne menyen. <b>Page Up / Page Down:</b> lagre / laste. <b>End:</b> neste lagringsplass. <b>F10:</b> start på nytt.':
            '<b>Home:</b> this menu. <b>Page Up / Page Down:</b> save / load. <b>End:</b> next save slot. <b>F10:</b> restart.',
        'På spillkontroller: A = fire, B = mellomrom, Start = E, Back = Esc, LB RB X Y = 1 til 4.':
            'On a gamepad: A = fire, B = space, Start = E, Back = Esc, LB RB X Y = 1 to 4.',
        'Moonstone: A Hard Days Knight (Mindscape 1991), kjørt fra originalkoden på en emulert Amiga 500. Kjernen er skrevet i C (WebAssembly), bildet tegnes med three.js, nettspill går med PeerJS. Menyen bruker spillets egen font og grafikk.':
            'Moonstone: A Hard Days Knight (Mindscape 1991), running the original code on an emulated Amiga 500. The core is written in C (WebAssembly), the picture is drawn with three.js and online play uses PeerJS. The menu uses the game’s own font and graphics.',

        /* ---------------- app.js: spillfil og egne filer */
        'Velg spillfilen (Moonstonecd32-AMIGA.zip eller «Moonstone CD32.iso»). Den lagres bare i denne nettleseren. Gjester i nettspill trenger den ikke.':
            'Choose the game file (Moonstonecd32-AMIGA.zip or “Moonstone CD32.iso”). It is only stored in this browser. Guests in online games don’t need it.',
        'Bruker den valgte spillfilen til siden lastes på nytt': 'Using the chosen game file until the page is reloaded',
        'Spillfilen er lagret i nettleseren': 'Game file saved in this browser',
        'Brukes: {0}': 'In use: {0}',
        'Brukes når spillet startes på nytt': 'Used when the game restarts',
        'Brukes ikke etter neste omstart': 'Not used after the next restart',

        /* ---------------- app.js: oppstart og introen */
        'Spillfilen mangler.': 'The game file is missing.',
        'Laster Moonstone ...': 'Loading Moonstone ...',
        'Spillfilen mangler. Velg den under «Spillfil og egne filer» i menyen.':
            'The game file is missing. Choose it under “Game file and your own files” in the menu.',
        'Spillet ditt fra {0} er lagret. Velg Fortsett under Lagring i menyen for å spille videre.':
            'Your game from {0} is saved. Choose Load autosave under Saves in the menu to carry on.',
        'Kunne ikke starte spillet: {0}': "Couldn't start the game: {0}",
        'Trykk på et valg i menyen': 'Tap a menu item',
        'Klikk på et valg, eller bruk piltastene og Enter': 'Click a menu item, or use the arrow keys and Enter',
        'Velg ridder med klikk eller venstre/høyre og Enter': 'Choose a knight with a click or Left/Right and Enter',
        'Hopper over introen ...': 'Skipping the intro ...',
        'Du er invitert til rom {0}. Trykk på skjermen, fire eller Esc for å hoppe over introen.':
            "You're invited to room {0}. Tap the screen, press fire or Esc to skip the intro.",
        'Esc, fire eller et trykk på skjermen hopper over introen': 'Esc, fire or a tap on the screen skips the intro',
        'Trykk på skjermen eller en tast for lyd': 'Tap the screen or press a key for sound',

        /* ---------------- app.js: nettspill */
        'Lager rom ...': 'Creating a room ...',
        'Rommet {0} er klart. Velg «Copy Link» og send lenken.': 'Room {0} is ready. Choose “Copy Link” and send the link.',
        'Alle spiller sitt eget spill og ser hverandre på kartet.': 'Everyone plays their own game and sees each other on the map.',
        'Kunne ikke lage rom: {0}': "Couldn't create a room: {0}",
        'Du er invitert til rom {0}. Trykk fire for å bli med.': "You're invited to room {0}. Press fire to join.",
        'Invitasjonslenken er kopiert': 'Invite link copied',
        'Kopier lenken her i menyen': 'Copy the link here in the menu',
        'Tur for tur: verten kjører spillet for alle, én ridder om gangen':
            'Turns: the host runs the game for everyone, one knight at a time',
        'Hver for seg: alle spiller sitt eget spill og ser hverandre på kartet':
            'Separate: everyone plays their own game and sees each other on the map',
        'Kontrollene kan ikke endres i et rom tur for tur, der alle styrer menyen. Sett dem opp før du lager eller blir med i et rom.':
            "Controls can't be changed in a Turns room, where everyone shares the menu. Set them up before you create or join a room.",
        'Romkoden har seks tegn.': 'The room code has six characters.',
        'Kobler til rom {0} ...': 'Connecting to room {0} ...',
        'Du er med i rom {0}. Alle spiller sitt eget spill og ser hverandre på kartet.':
            "You're in room {0}. Everyone plays their own game and sees each other on the map.",
        'Kunne ikke laste spillet fra verten: {0} Last siden på nytt og prøv igjen.':
            "Couldn't load the game from the host: {0} Reload the page and try again.",
        'Kunne ikke laste spillet fra verten. Last siden på nytt og prøv igjen.':
            "Couldn't load the game from the host. Reload the page and try again.",
        'Du er med i spillet.': "You're in the game.",
        'Kunne ikke koble til: {0}': "Couldn't connect: {0}",
        'Romsiden styres av verten. I tittelmenyen kan alle styre.':
            'The host controls the room page. Everyone can use the title menu.',
        'Du har forlatt rommet': 'You left the room',
        'Du har forlatt nettspillet': 'You left the online game',
        'Lenken er kopiert': 'Link copied',
        'Skriv romkoden (seks tegn) eller lim inn lenken': 'Type the room code (six characters) or paste the link',
        'Skriv navnet ditt': 'Type your name',

        /* ---------------- app.js: sidemenyen i nettspill */
        'Du er vert for rom {0}. Send lenken til opptil tre andre. Alle spiller sitt eget spill og ser de andre ridderne på kartet.':
            "You're hosting room {0}. Send the link to up to three others. Everyone plays their own game and sees the other knights on the map.",
        'Du er med i rom {0}. Alle spiller sitt eget spill og ser de andre ridderne på kartet.':
            "You're in room {0}. Everyone plays their own game and sees the other knights on the map.",
        'Du er vert for rom {0}. Send lenken til opptil tre gjester.': "You're hosting room {0}. Send the link to up to three guests.",
        'Du er med i rom {0}. Verten kjører spillet og lagrer.': "You're in room {0}. The host runs the game and saves it.",
        'I et rom gjelder lagringene bare ditt eget spill.': 'In a room, saves only cover your own game.',
        'Laster du en lagring, får gjestene den også.': 'If you load a save, your guests get it too.',
        '{0} (vert)': '{0} (host)',
        '{0} (deg)': '{0} (you)',
        '{0} (kobler til ...)': '{0} (connecting ...)',
        'På kartet': 'On the map',
        'Ikke på kartet': 'Not on the map',
        'Hver for seg: alle styrer sin egen ridder i sitt eget spill. De andre ridderne står på kartet ditt der de er i sine spill, i stedet for datamaskinens riddere.':
            "Separate: everyone controls their own knight in their own game. The other knights stand on your map where they are in their games, instead of the computer's knights.",
        'Følger turen i spillet': 'Follows the turn in the game',
        'Faste porter': 'Fixed ports',
        'Begge': 'Both',
        'Ser på': 'Watching',
        'Spiller {0}': 'Player {0}',
        'Spiller 1 velger ridder først i spillet, så spiller 2 osv., og bare den som skal velge, kan styre da. Joysticken går automatisk til den som har turen på kartet, og i kamp mellom to riddere får begge sin joystick. I menyene kan alle styre.':
            'Player 1 picks a knight first, then player 2 and so on, and only the one picking is in control then. The joystick goes to whoever has the turn on the map, and in a fight between two knights both get their own. Everyone can use the menus.',
        'Moonstone har to joystickporter. Joystick 1 (port 2) brukes på kartet og i menyene, i kamp mellom to riddere brukes begge.':
            'Moonstone has two joystick ports. Joystick 1 (port 2) is used on the map and in the menus; in a fight between two knights both are used.',
        '{0} velger ridder': '{0} is picking a knight',
        '{0} har turen': "It's {0}'s turn",

        /* ---------------- app.js: kontrollene i Options */
        'Kontrollene er som standard igjen': 'Controls are back to the defaults',
        'Trykk en knapp på spillkontrolleren (Esc avbryter)': 'Press a button on the gamepad (Esc cancels)',
        'Trykk tasten du vil bruke (Esc avbryter)': 'Press the key you want to use (Esc cancels)',
        'Ingenting valgt': 'Nothing chosen',
        'Avbrutt': 'Cancelled',
        'Knappen er lagret': 'Button saved',
        'Tasten er lagret': 'Key saved',

        /* ---------------- app.js: dueller i Hver for seg */
        'den andre': 'the other player',
        'Utfordrer {0} ...': 'Challenging {0} ...',
        '{0} svarte ikke.': "{0} didn't answer.",
        'Forbindelsen til {0} ble brutt.': 'Lost the connection to {0}.',
        'Fikk ikke kontakt med {0}.': "Couldn't reach {0}.",
        'Datamaskinen styrer ridderen i kampen.': 'The computer controls the knight in the battle.',
        '{0} tar imot. Sender spillet ...': '{0} accepted. Sending the game ...',
        'Kamp mot {0}!': 'Fighting {0}!',
        '{0} kan ikke kjempe nå.': "{0} can't fight right now.",
        'Kampen mot {0} er over.': 'The fight with {0} is over.',
        'Forbindelsen ble brutt. Tilbake i ditt eget spill.': 'Connection lost. Back in your own game.',
        '{0} utfordrer deg til kamp!': '{0} challenges you to a fight!',
        'Kunne ikke laste kampen.': "Couldn't load the fight.",
        'Kamp mot {0}! Du styrer ridderen din.': 'Fighting {0}! You control your knight.',
        'Ute av takt, henter kampen på nytt ...': 'Out of sync, reloading the fight ...',
        'Kunne ikke hente ditt eget spill tilbake.': "Couldn't bring back your own game.",
        'Kampen er over. Tilbake i ditt eget spill.': 'The fight is over. Back in your own game.',
        'Ute av takt, henter spillet på nytt ...': 'Out of sync, reloading the game ...',
        '{0} svarer ikke lenger.': '{0} stopped responding.',
        '{0} svarer ikke lenger. Tilbake i ditt eget spill.': '{0} stopped responding. Back in your own game.',

        /* ---------------- app.js: lagring */
        'kl. {0}': 'at {0}',
        'Sist lagret automatisk {0}.': 'Last autosaved {0}.',
        'Ingenting å laste ned ennå': 'Nothing to download yet',
        'Ikke under en duell': 'Not during a fight',
        'Kunne ikke lagre.': "Couldn't save.",
        'Lagringen er lastet ned': 'Save downloaded',
        'Lagret på plass {0}': 'Saved to slot {0}',
        'Nettleseren tillater ikke fullskjerm her': "This browser doesn't allow fullscreen here",
        'Grafikken ble borte (vanlig på mobil).': 'The graphics were lost (common on phones).',
        'Grafikken ble borte (vanlig på mobil). Spillet er lagret.': 'The graphics were lost (common on phones). Your game is saved.',
        'Grafikken er tilbake': 'The graphics are back',
        '{0} har byttet fane eller app': '{0} switched to another tab or app',
        '{0} har vært borte i ett minutt': '{0} has been away for a minute',
        'Fullskjerm': 'Fullscreen',
        'På iPhone og iPad: Del og Legg til på Hjem-skjerm gir spillet hele skjermen.': 'On iPhone and iPad: Share, then Add to Home Screen gives the game the whole screen.',
        'Nettleseren tillater ikke lagring': "This browser doesn't allow saving",
        'plass {0}': 'slot {0}',
        'den automatiske lagringen': 'the autosave',
        'Lagringer kan lastes når du spiller selv eller er vert': 'Saves can be loaded when you play on your own or host',
        'Ingenting lagret på {0}': 'Nothing saved in {0}',
        'Kunne ikke laste {0}: {1}': "Couldn't load {0}: {1}",
        'ukjent feil': 'unknown error',
        'Lastet {0}': 'Loaded {0}',
        'Gjelder fra neste start': 'Takes effect the next time the game starts',
        'Pause': 'Paused',
        'Fortsetter': 'Resumed',

        /* ---------------- app.js og hd.js: HD-grafikk */
        'Denne skjermen har ingen bakgrunn spillet holder for seg selv': 'This screen has no separate background to save',
        'Lagret {0}. Legg den i mappen bg i HD-pakken.': 'Saved {0}. Put it in the bg folder of the HD pack.',
        '{0} bilder i HD-pakken, av dem {1} bakgrunner.': '{0} images in the HD pack, {1} of them backgrounds.',
        '{0} bilder i HD-pakken.': '{0} images in the HD pack.',
        '{0} HD-bilder lastet': '{0} HD images loaded',
        'HD-grafikken er fjernet.': 'HD graphics removed.',
        'Original grafikk': 'Original graphics',
        'HD-grafikk der den finnes': 'HD graphics where available',
        'HD-grafikken lastes automatisk': 'HD graphics load automatically',
        'HD er av. Velg «HD der den finnes» for å laste standardgrafikken.':
            'HD is off. Choose “HD where available” to load the standard graphics.',
        'HD er av. Velg «HD der den finnes» for å slå den på igjen.':
            'HD is off. Choose “HD where available” to turn it back on.',
        'HD kunne ikke lastes. Originalgrafikken brukes der bilder mangler.':
            "HD couldn't be loaded. The original graphics are used where images are missing.",
        'Standard-HD: {0} bilder lastet. Bakgrunner lastes ved behov.': 'Standard HD: {0} images loaded. Backgrounds load as needed.',
        'Laster standardgrafikken ...': 'Loading the standard graphics ...',
        'Originalgrafikk. Åpne nettversjonen for standard-HD, eller velg en lokal HD-mappe.':
            'Original graphics. Open the web version for standard HD, or choose a local HD folder.',

        /* ---------------- net.js og rooms.js */
        '{0} svarer ikke lenger': '{0} stopped responding',
        '{0} koblet fra': '{0} disconnected',
        '{0} er tilbake': '{0} is back',
        '{0} koblet seg til': '{0} joined',
        'Fikk ikke kontakt med PeerJS-serveren. Sjekk nettforbindelsen og prøv igjen.':
            "Couldn't reach the PeerJS server. Check your connection and try again.",
        'Nettverksfeil: {0}': 'Network error: {0}',
        'Verten har en annen versjon av Moonstone. Last siden på nytt (begge to) og prøv igjen.':
            'The host has a different version of Moonstone. Reload the page (both of you) and try again.',
        'Rommet er fullt (fire spillere).': 'The room is full (four players).',
        '{0} kom ut av takt, sender tilstanden på nytt': '{0} fell out of sync, sending the game again',
        'Verten svarer ikke lenger.': 'The host stopped responding.',
        'Forbindelsen til verten ble brutt.': 'Lost the connection to the host.',
        'Fant ikke rommet {0}. Sjekk koden, eller om verten fortsatt er der.':
            "Couldn't find room {0}. Check the code, or whether the host is still there.",
        'Fikk ikke kontakt med verten.': "Couldn't reach the host.",
        'Henter spillet fra verten ... {0} %': 'Fetching the game from the host ... {0}%',
        'Verten avsluttet spillet.': 'The host ended the game.',
        'ikke i et rom': 'not in a room',
        'ikke koblet til signalserveren': 'not connected to the signalling server',
        'svarer ikke': 'not responding',
        'MQTT er ikke lastet': "MQTT isn't loaded",

        /* ---------------- core.js og kjernen (C) */
        'Den innebygde spillfilen kan ikke leses.': "The built-in game file can't be read.",
        'Oppstart feilet': 'Startup failed',
        'Lagringen er skadet (for kort).': 'The save is damaged (too short).',
        'Lagringen er laget med en nyere utgave av Moonstone.': 'The save was made with a newer version of Moonstone.',
        'Lagringen er laget med andre spillfiler.': 'The save was made with different game files.',
        'Lagringen er skadet (slutter for tidlig).': 'The save is damaged (it ends too early).',
        'Lagringen er skadet.': 'The save is damaged.',
        'Lagringen er laget paa en annen maskintype (PC eller nett) med en eldre utgave.':
            'The save was made on the other platform (PC or web) with an older version.',
        'Fant ikke Moonstone.Slave i filene.': "Couldn't find Moonstone.Slave in the files.",
        'Mappen data med program og mog mangler.': 'The data folder with program and mog is missing.',
        'Klarte ikke pakke ut ISO-filen fra zip-filen.': "Couldn't unpack the ISO file from the zip file.",
        'ISO-filen i zip-filen kan ikke leses.': "The ISO file in the zip file can't be read.",
        'Filen er verken zip eller ISO.': 'The file is neither zip nor ISO.',
        'Filen kunne ikke leses.': "The file couldn't be read.",
        'Spillet er avsluttet (F10).': 'The game was stopped (F10).',
        'Spillet er avsluttet.': 'The game was stopped.',
        'Slaven krever registrert WHDLoad.': 'The slave needs a registered WHDLoad.',
        'Feil versjon av spillfilene.': 'Wrong version of the game files.',
        'Filen er ikke en lagring fra Moonstone.': "That file isn't a Moonstone save.",
        'Ikke nok minne til aa laste.': 'Not enough memory to load it.',
        'Filen er tom.': 'The file is empty.',
        'Kunne ikke lese filen.': "Couldn't read the file.",
        'Fant ikke filen.': "Couldn't find the file.",
        'Fant ikke Moonstone.Slave.': "Couldn't find Moonstone.Slave.",
        'Moonstone.Slave kan ikke leses.': "Moonstone.Slave can't be read.",
        'Moonstone.Slave er ikke en WHDLoad-slave.': "Moonstone.Slave isn't a WHDLoad slave.",
        'Slaven returnerte.': 'The slave quit unexpectedly.',
        'Denne versjonen av spillfilene trenger resload_Delta, som ikke er med.':
            "This version of the game files needs resload_Delta, which isn't supported.",

        /* ---------------- net.js: feil fra PeerJS (e.type) */
        'Nettleseren kan ikke spille på nett (WebRTC mangler).': "This browser can't play online (no WebRTC).",
        'Forbindelsen til nettspilltjenesten ble brutt.': 'Lost the connection to the online game service.',
        'Fikk ikke satt opp forbindelsen mellom spillerne.': "Couldn't set up the connection between the players.",
        'Ugyldig romkode.': "That room code isn't valid.",
    };

    /* navnene paa delene i en lagring (deler[] i port/src/state.c) */
    const DELER = {
        'minnet': 'the memory', 'maskinen': 'the machine', 'brikkene': 'the chips',
        'CIA-brikkene': 'the CIA chips', '68000': 'the 68000', 'lyden': 'the sound',
        'WHDLoad': 'WHDLoad', 'moetet mellom to riddere': 'fights between two knights',
        'tegnelisten': 'the drawing list', 'tekstene': 'the texts',
        'nettspillmenyen': 'the online game menu', 'ridderne som er tatt over': 'the knights taken over',
        'Hver for seg': 'Separate mode', 'Blitteren': 'the blitter',
    };

    /* meldinger fra kjernen med tall eller navn i (port/src/state.c, files.c, whdload.c).
     * Det engelske kan vaere en funksjon som faar treffene. */
    const MOENSTRE = [
        [/^Lagringen er fra en utgave der (.+) er lagret annerledes, og kan ikke brukes\.$/,
            (m, del) => "The save is from a version that stores " + (DELER[del] || del) + " differently, and can't be used."],
        [/^Slaven stoppet \(aarsak (.+)\)$/, 'The slave stopped (reason $1)'],
        [/^Kunne ikke relokere filen paa (\S+)$/, "Couldn't relocate the file at $1"],
        [/^Ukjent kommando (\S+) i patchlisten paa (\S+)$/, 'Unknown command $1 in the patch list at $2'],
        [/^Ukjent resload-funksjon (\S+)$/, 'Unknown resload function $1'],
        [/^Lagringen er fra en eldre utgave \(versjon (\d+)\) som ikke kan leses\.$/,
            "The save is from an older version ($1) that can't be read."],
        [/^Fant ikke filen (\S+)$/, "Couldn't find the file $1"],
        [/^Fant ikke (\S+)\.$/, "Couldn't find $1."],
    ];

    let sprak = 'en';
    /* elementer med kjent kildetekst: el -> { tekst: kilde eller null, attrs: { navn: kilde } },
     * der en kilde er { tekst, verdier, html, attr } */
    const kjente = new Map();

    function T(tekst, ...verdier) {
        tekst = String(tekst == null ? '' : tekst);
        let t = tekst;
        if (sprak === 'en') {
            if (Object.prototype.hasOwnProperty.call(EN, tekst)) t = EN[tekst];
            else for (const [re, en] of MOENSTRE) if (re.test(tekst)) { t = tekst.replace(re, en); break; }
        }
        if (!verdier.length) return t;
        return t.replace(/\{(\d+)\}/g, (m, i) => {
            let v = verdier[+i];
            if (typeof v === 'function') v = v();
            return v === undefined || v === null ? m : String(v);
        });
    }

    /* tegner et element fra kilden; tekst i spillets font gaar gjennom Spillgrafikk */
    function tegn(el, k) {
        const t = T(k.tekst, ...k.verdier);
        if (k.attr) el.setAttribute(k.attr, t);
        else if (k.html) el.innerHTML = t;
        else if (el.classList && (el.classList.contains('pt') || el.classList.contains('pt2')) && typeof Spillgrafikk !== 'undefined')
            Spillgrafikk.sett(el, t, el.classList.contains('pt2') ? 2 : 1);
        else el.textContent = t;
    }

    function husk(el, k) {
        let e = kjente.get(el);
        if (!e) { e = { tekst: null, attrs: {} }; kjente.set(el, e); }
        if (k.attr) e.attrs[k.attr] = k;
        else e.tekst = k;
        tegn(el, k);
    }

    function sett(el, tekst, ...verdier) { if (el) husk(el, { tekst, verdier, html: false }); }
    function settHtml(el, tekst, ...verdier) { if (el) husk(el, { tekst, verdier, html: true }); }
    function settAttr(el, attr, tekst, ...verdier) { if (el) husk(el, { tekst, verdier, attr }); }

    const normal = (s) => s.replace(/\s+/g, ' ').trim();

    /* engelsk -> norsk kilde, for de faste tekstene i index.html */
    const NO = new Map(Object.entries(EN).map(([no, en]) => [en, no]));
    const kilde = (t) => { t = normal(t); return NO.has(t) ? NO.get(t) : t; };

    /* de faste tekstene i index.html: husk den norske kilden og tegn paa valgt spraak */
    function start(valgt) {
        sprak = valgt === 'no' ? 'no' : 'en';
        document.documentElement.lang = sprak;
        for (const el of document.querySelectorAll('.pt, .pt2')) if (el.textContent.trim()) sett(el, kilde(el.textContent));
        for (const el of document.querySelectorAll('option')) if (el.textContent.trim()) sett(el, kilde(el.textContent));
        for (const el of document.querySelectorAll('p.hjelp, .taster li, p.smaa, #lasting-tekst')) if (el.textContent.trim()) settHtml(el, kilde(el.innerHTML));
        for (const attr of ['placeholder', 'title', 'aria-label']) {
            for (const el of document.querySelectorAll('[' + attr + ']')) settAttr(el, attr, kilde(el.getAttribute(attr)));
        }
        const beskrivelse = document.querySelector('meta[name="description"]');
        if (beskrivelse) settAttr(beskrivelse, 'content', kilde(beskrivelse.getAttribute('content')));
    }

    function bytt(valgt) {
        sprak = valgt === 'no' ? 'no' : 'en';
        document.documentElement.lang = sprak;
        for (const [el, k] of kjente) {
            if (!el.isConnected) { kjente.delete(el); continue; }
            if (k.tekst) tegn(el, k.tekst);
            for (const a of Object.values(k.attrs)) tegn(el, a);
        }
    }

    return { T, sett, settHtml, settAttr, start, bytt, sprak: () => sprak };
})();
const T = Sprak.T;
