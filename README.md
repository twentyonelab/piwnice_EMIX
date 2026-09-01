# EMIX · Piwnice 5500 m² — trzy koncepcje

Strona prezentująca trzy koncepcje zagospodarowania 5500 m² piwnic dawnej mleczarni.
Materiał wewnętrzny, przygotowany do zapoznania się i dyskusji.

**Publikowana treść jest zaszyfrowana.** W repozytorium nie ma tekstu jawnego —
`index.html` zawiera bramkę na hasło oraz szyfrogram całej strony.

## Pliki

| Plik | Zawartość |
|---|---|
| `index.html` | Bramka na hasło + zaszyfrowana treść (AES-256-GCM) |
| `tools/build.py` | Szyfrowanie i odszyfrowywanie |
| `tools/gate.template.html` | Szablon bramki (jawny — bezpieczeństwo opiera się na kluczu, nie na kodzie) |
| `robots.txt` | Zakaz indeksowania dla robotów |

## Jak to działa

Klucz AES-256 jest wyprowadzany z hasła przez PBKDF2-HMAC-SHA256, 310 000 iteracji,
z 16-bajtową losową solą. Treść szyfruje AES-256-GCM z 12-bajtowym losowym IV.
Odszyfrowanie zachodzi w przeglądarce przez Web Crypto API.

To **nie jest** ukrywanie hasła w JavaScripcie — w opublikowanym pliku nie ma ani
hasła, ani jego skrótu, ani treści w postaci czytelnej. Bez hasła nie da się
odzyskać dokumentu z kodu źródłowego strony.

### Co to zabezpiecza, a czego nie

Zabezpiecza przed przypadkowym trafieniem na adres, przed indeksowaniem
i przed odczytaniem treści ze źródła strony.

Nie zabezpiecza przed **atakiem słownikowym offline**: szyfrogram jest publiczny,
więc hasło można łamać lokalnie, bez ograniczeń liczby prób. Dlatego hasło musi mieć
wysoką entropię — nie należy zastępować wygenerowanego hasła własnym, łatwym
do zapamiętania. Po ujawnieniu hasła należy przebudować stronę z nowym: szyfrogram
raz opublikowany pozostaje w cudzych kopiach.

Repozytorium jest publiczne. Gdyby materiał wymagał mocniejszej ochrony, właściwą
drogą jest repozytorium prywatne i dystrybucja pliku poza GitHub Pages.

## Aktualizacja treści

Pliki źródłowe (jawne) **celowo nie znajdują się w repozytorium** — ich obecność
tutaj unieważniłaby całe szyfrowanie. Są przekazywane osobno i tam należy je edytować.

```bash
# odszyfruj opublikowaną wersję do jednego pliku HTML (do wglądu)
PIWNICE_PW='...' python3 tools/build.py decrypt --in index.html --out odszyfrowane.html

# zbuduj ponownie z katalogu źródłowego
PIWNICE_PW='...' python3 tools/build.py encrypt --src /sciezka/do/src --out index.html
```

Katalog źródłowy zawiera `index.html`, `koncepcja-a.html`, `koncepcja-b.html`,
`koncepcja-c.html` oraz `assets/` (CSS, JS, obrazy). Skrypt składa je w jedną stronę
z routingiem po kotwicach (`#/a`, `#/b`, `#/c`), wbudowuje obrazy jako data URI
i szyfruje całość. Wymaga pakietu `cryptography` (`pip install cryptography`).

Hasło podawane jest przez zmienną środowiskową `PIWNICE_PW` albo interaktywnie.
**Nigdy nie zapisuj hasła w repozytorium.**

## Publikacja na GitHub Pages

Repozytorium → **Settings → Pages → Build and deployment**:
`Source: Deploy from a branch`, `Branch: claude/emix-three-concepts-page-27g6xs`,
`Folder: / (root)`. Adres: `https://twentyonelab.github.io/piwnice_EMIX/`

## System wizualny

- **Paleta** — `#FFFFFF` tło, `#000000` tekst, `#525252` tekst drugorzędny, `#0A0A0A` stopka; obramowania `#000000` przy 10% krycia.
- **Typografia** — Inter. Nagłówki: `700`, `letter-spacing: -.05em`, `line-height: .9`. Metadane: monospace, wersaliki, `letter-spacing: .1em`.
- **Ruch** — wyłącznie `cubic-bezier(.16, 1, .3, 1)`, minimum 500 ms dla stanów `hover`. Marquee: 30 s liniowo, pauza przy `hover`.
- **Kursor** — 32 px okrąg, `mix-blend-mode: difference`, interpolacja pozycji przez `requestAnimationFrame`, `scale(2.5)` nad linkiem.
- **Zdjęcia** — domyślnie `grayscale(100%)`, na `hover` pełny kolor i `scale(1.05)` w 700 ms.
- Respektowane jest `prefers-reduced-motion`; na urządzeniach dotykowych kursor systemowy pozostaje standardowy. Stany animacji są bramkowane klasą `html.js`, więc bez JavaScriptu treść pozostaje widoczna.

## Zdjęcia

Zdjęcia użyte na stronie są **poglądowe** i nie przedstawiają obiektu. Wszystkie
pochodzą z Wikimedia Commons na licencjach dopuszczających takie użycie
(CC0, CC BY-SA, OGL v1.0, domena publiczna). Pełna lista autorów i licencji
znajduje się w stopce samej strony — czyli tam, gdzie zdjęcia są widoczne.

Logo EMIX pochodzi z emix.com.pl i pozostaje własnością EMIX.
