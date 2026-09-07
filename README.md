# Vortex Menu - NUI

Diese Seite ist die Oberflaeche des FiveM-Menues. Sie wird nicht im
Browser bedient, sondern von FiveM als NUI geladen und ueber die
`client.lua` gesteuert.

## Was hier liegt

```
index.html      komplette Oberflaeche (CSS + JS inline)
img/logo.png    Banner- und Notification-Logo
CNAME           Custom Domain fuer GitHub Pages
.nojekyll       damit GitHub die Dateien unveraendert ausliefert
```

## Hochladen

1. Den **Inhalt** dieses Ordners ins Repository legen (nicht den Ordner
   selbst) - `index.html` muss im Wurzelverzeichnis liegen.
2. Repository -> Settings -> Pages -> Source: `main` / `/ (root)`.
3. Unter *Custom domain* `bkamt.xyz` eintragen (die `CNAME`-Datei setzt
   das bereits) und *Enforce HTTPS* aktivieren.
4. Beim Domain-Anbieter auf GitHub Pages zeigen:

   ```
   A     @    185.199.108.153
   A     @    185.199.109.153
   A     @    185.199.110.153
   A     @    185.199.111.153
   ```

Danach ist die Seite unter `https://bkamt.xyz/` erreichbar, das Logo
unter `https://bkamt.xyz/img/logo.png`.

## Wichtig fuer die Lua-Seite

* In `index.html` muss `RESOURCE_NAME` dem Ordnernamen der FiveM-Resource
  entsprechen. Bei externen Seiten stellt FiveM `GetParentResourceName()`
  nicht bereit, deshalb steht der Name fest im Script.
* Nach jeder Aenderung an dieser Seite in der `fxmanifest.lua` die
  Version hochzaehlen (`?v=2`), sonst laedt FiveM die alte Fassung
  aus dem Cache.

## Im Browser testen

`index.html` laesst sich direkt oeffnen. Erkennt sie, dass sie nicht in
FiveM laeuft, simuliert sie die Nachrichten der `client.lua` und legt
die Steuerung auf die Tastatur:

| Taste | Funktion |
|---|---|
| F5 | Menue auf/zu |
| Pfeiltasten | navigieren / Werte aendern |
| Enter, Backspace, Esc | auswaehlen, zurueck, schliessen |
| Mausrad | FreeCam-Leiste, wenn sie offen ist |
| N | Notification |
| S | Spectator-Namen |
