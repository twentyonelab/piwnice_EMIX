#!/usr/bin/env python3
"""
Buduje index.html: bramka na haslo + zaszyfrowana tresc strony.

Cala tresc merytoryczna trafia do repozytorium WYLACZNIE jako szyfrogram
(AES-256-GCM, klucz wyprowadzony z hasla przez PBKDF2-HMAC-SHA256). Bez hasla
z opublikowanego pliku nie da sie odzyskac tresci — nie jest to ukrywanie
w JavaScripcie, lecz rzeczywiste szyfrowanie.

Zastrzezenie: szyfrogram jest publiczny, wiec haslo mozna atakowac offline.
Uzywaj wylacznie hasel o wysokiej entropii.

    # zaszyfruj katalog zrodlowy do index.html
    PIWNICE_PW='...' python3 tools/build.py encrypt --src ../src --out index.html

    # odzyskaj tresc z opublikowanego pliku
    PIWNICE_PW='...' python3 tools/build.py decrypt --in index.html --out odszyfrowane.html
"""

import argparse, base64, getpass, json, mimetypes, os, re, sys

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 310_000
PAYLOAD_RE = re.compile(
    r'<script id="payload" type="application/json">(.*?)</script>', re.S
)


# --------------------------------------------------------------------------- #
#  Kryptografia
# --------------------------------------------------------------------------- #

def derive(password: str, salt: bytes, iterations: int) -> bytes:
    return PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations
    ).derive(password.encode("utf-8"))


def encrypt(plaintext: bytes, password: str) -> dict:
    salt, iv = os.urandom(16), os.urandom(12)
    ct = AESGCM(derive(password, salt, ITERATIONS)).encrypt(iv, plaintext, None)
    return {
        "v": 1,
        "kdf": "PBKDF2-SHA256",
        "iterations": ITERATIONS,
        "salt": base64.b64encode(salt).decode(),
        "iv": base64.b64encode(iv).decode(),
        "ct": base64.b64encode(ct).decode(),
    }


def decrypt(blob: dict, password: str) -> bytes:
    key = derive(password, base64.b64decode(blob["salt"]), blob["iterations"])
    return AESGCM(key).decrypt(
        base64.b64decode(blob["iv"]), base64.b64decode(blob["ct"]), None
    )


def ask_password(confirm: bool = False) -> str:
    pw = os.environ.get("PIWNICE_PW")
    if pw:
        return pw
    pw = getpass.getpass("Haslo: ")
    if confirm and pw != getpass.getpass("Powtorz haslo: "):
        sys.exit("Hasla sie roznia.")
    if not pw:
        sys.exit("Puste haslo.")
    return pw


# --------------------------------------------------------------------------- #
#  Zlozenie strony jednoplikowej z katalogu zrodlowego
# --------------------------------------------------------------------------- #

ROUTER_JS = r"""
/* ---------- router widokow ---------- */
(function () {
  var views = [].slice.call(document.querySelectorAll('.view'));
  var io = null;
  function reveal(root) {
    var t = [].slice.call(root.querySelectorAll('.rv, .rv-split, .fade'));
    if (io) io.disconnect();
    if (!('IntersectionObserver' in window) ||
        window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      t.forEach(function (e) { e.classList.add('in'); });
      return;
    }
    io = new IntersectionObserver(function (en) {
      en.forEach(function (e) {
        if (!e.isIntersecting) return;
        var d = parseInt(e.target.getAttribute('data-delay') || '0', 10);
        setTimeout(function () { e.target.classList.add('in'); }, d);
        io.unobserve(e.target);
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -5% 0px' });
    t.forEach(function (e) { io.observe(e); });
  }
  function route() {
    var m = /^#\/(a|b|c)$/.exec(location.hash);
    var id = 'view-' + (m ? m[1] : 'index');
    views.forEach(function (v) { v.hidden = (v.id !== id); });
    window.scrollTo(0, 0);
    reveal(document.getElementById(id));
  }
  window.addEventListener('hashchange', route);
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[data-jump]');
    if (!a) return;
    var id = a.getAttribute('data-jump');
    setTimeout(function () {
      var t = document.getElementById(id);
      if (t) t.scrollIntoView({ behavior: 'smooth' });
    }, 90);
  });
  route();
})();
"""


def bundle(src: str) -> dict:
    """Sklada 4 strony zrodlowe w jeden pakiet: {title, css, js, html}."""

    def read(rel):
        with open(os.path.join(src, rel), encoding="utf-8") as fh:
            return fh.read()

    images = {}
    img_dir = os.path.join(src, "assets/img")
    for fname in sorted(os.listdir(img_dir)):
        path = os.path.join(img_dir, fname)
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as fh:
            data = base64.b64encode(fh.read()).decode()
        images["assets/img/" + fname] = "data:%s;base64,%s" % (mime, data)

    def view(page):
        body = re.search(r"<body>(.*)</body>", read(page), re.S).group(1)
        body = re.sub(r'<script src="assets/js/app\.js"></script>\s*', "", body)
        for rel, uri in images.items():
            body = body.replace('"' + rel + '"', '"' + uri + '"')
        body = body.replace(
            'href="index.html#zestawienie"', 'href="#/" data-jump="zestawienie"'
        )
        body = body.replace('href="index.html"', 'href="#/"')
        for slug in "abc":
            body = body.replace(
                'href="koncepcja-%s.html"' % slug, 'href="#/%s"' % slug
            )
        return body

    html = "".join(
        '<div class="view" id="view-%s"%s>%s</div>'
        % (key, "" if key == "index" else " hidden", view(page))
        for key, page in [
            ("index", "index.html"),
            ("a", "koncepcja-a.html"),
            ("b", "koncepcja-b.html"),
            ("c", "koncepcja-c.html"),
        ]
    )

    return {
        "title": "EMIX · Piwnice 5500 m² — trzy koncepcje",
        "css": read("assets/css/style.css") + "\n.view[hidden]{display:none!important}\n",
        "js": read("assets/js/app.js") + ROUTER_JS,
        "html": html,
    }


# --------------------------------------------------------------------------- #
#  Szablon bramki
# --------------------------------------------------------------------------- #

def gate_html(payload: dict, logo_uri: str) -> str:
    tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate.template.html")
    with open(tpl, encoding="utf-8") as fh:
        page = fh.read()
    page = page.replace("__LOGO__", logo_uri)
    # "</" ucieka, by szyfrogram nie zamknal przedwczesnie znacznika <script>
    blob_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    page = page.replace("__PAYLOAD__", blob_json)
    return page


def logo_datauri(src: str) -> str:
    with open(os.path.join(src, "assets/img/emix-logo.png"), "rb") as fh:
        return "data:image/png;base64," + base64.b64encode(fh.read()).decode()


# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    enc = sub.add_parser("encrypt", help="zaszyfruj katalog zrodlowy do index.html")
    enc.add_argument("--src", required=True, help="katalog ze zrodlami (jawnymi)")
    enc.add_argument("--out", default="index.html")

    dec = sub.add_parser("decrypt", help="odzyskaj tresc z opublikowanego pliku")
    dec.add_argument("--in", dest="inp", default="index.html")
    dec.add_argument("--out", default="odszyfrowane.html")

    args = ap.parse_args()

    if args.cmd == "encrypt":
        pw = ask_password(confirm=True)
        data = bundle(args.src)
        blob = encrypt(json.dumps(data, separators=(",", ":")).encode("utf-8"), pw)
        page = gate_html(blob, logo_datauri(args.src))
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(page)
        print("Zapisano %s (%d KB), iteracje PBKDF2: %d"
              % (args.out, os.path.getsize(args.out) // 1024, ITERATIONS))
        return

    pw = ask_password()
    with open(args.inp, encoding="utf-8") as fh:
        blob = json.loads(PAYLOAD_RE.search(fh.read()).group(1))
    data = json.loads(decrypt(blob, pw))
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(
            '<!DOCTYPE html>\n<html lang="pl">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            "<title>%s</title>\n"
            '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">\n'
            "<style>%s</style>\n</head>\n<body>%s\n<script>%s</script>\n</body>\n</html>\n"
            % (data["title"], data["css"], data["html"], data["js"])
        )
    print("Zapisano", args.out)


if __name__ == "__main__":
    main()
