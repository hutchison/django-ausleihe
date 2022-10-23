# Ausleihe

Ein Verleihsystem.

## Problembeschreibung

Es existieren Medien (Bücher, Untersuchungsgeräte, etc.) die von Nutzern ausgeliehen werden können.

Ein Medium hat einen eindeutigen Identifier (anfangs z.B. eine fünfstellige Nummer, aber diese kann sich noch ändern).
Ein Buch ist ein Medium mit zusätzlichen Informationen (ISBN, Titel, Beschreibung, Verlag, [Sprache], Ausgabe).
Ein Buch wurde von einem oder mehreren Autoren geschrieben.

Ein Nutzer existiert schon über Django. Er wird erweitert und erhält zusätzliche Kontaktinformationen (Telefonnummer, Adresse).

Ein Nutzer leiht ein Medium von einem bestimmten Anfangsdatum bis zu einem Enddatum aus. Eine Ausleihe wurde zurückgegeben oder nicht.
