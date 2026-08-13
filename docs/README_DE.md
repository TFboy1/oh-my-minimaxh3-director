<p align="center">
  <img src="../banner.svg" alt="oh-my-minimaxh3-director Banner" width="100%"/>
</p>

[![Skills.sh](https://img.shields.io/badge/Skills.sh-Install%20Skill-00C853?style=for-the-badge&logo=hackthebox&logoColor=white)](https://skills.sh/tfboy1/oh-my-minimaxh3-director/oh-my-minimaxh3-director) [![爱发电](https://img.shields.io/badge/爱发电-Support%20Me-FF69B4?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://www.ifdian.net/item/1a20ed042f0711f1865a52540025c377) [![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-☕-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.creem.io/payment/prod_1yc40mIhKwwrc7iqFOG9G2) [![GitHub Stars](https://img.shields.io/github/stars/tfboy1/oh-my-minimaxh3-director?style=for-the-badge&logo=github&color=yellow)](https://github.com/TFboy1/oh-my-minimaxh3-director/stargazers) [![License](https://img.shields.io/github/license/tfboy1/oh-my-minimaxh3-director?style=for-the-badge&color=blue)](LICENSE)

[![简体中文](https://img.shields.io/badge/简体中文-README-blue?style=flat-square)](../README.md) [![English](https://img.shields.io/badge/English-README-blue?style=flat-square)](README_EN.md) [![日本語](https://img.shields.io/badge/日本語-README-blue?style=flat-square)](README_JA.md) [![Français](https://img.shields.io/badge/Français-README-blue?style=flat-square)](README_FR.md) [![Deutsch](https://img.shields.io/badge/Deutsch-Current-red?style=flat-square)](#)

<p align="center">
Dein KI-Filmregisseur. Gib mir ein Drehbuch, ich liefere den Final Cut —
eine automatisierte Pipeline: Storyboard → MiniMax H3 Generierung → JianYing-Schnitt mit einem Klick.
</p>

## Funktionen

- 🎬 **Automatisches Storyboard**: zerlegt ein Skript in Segmente (Standard 10 s, 2-3
  Einstellungen pro Segment) und erzeugt `storyboard.md`, `storyboard.json` und H3-Prompts
  in sechs Teilen.
- 🎞️ **MiniMax-H3-Workflow-Routing**: wählt automatisch Ref2VA (Referenzbilder), T2V
  (reiner Text) oder I2V (erstes/letztes Bild) und überschreibt Parameter pro `class_type` —
  keine hartkodierten Node-IDs.
- ✅ **Parameterbestätigung**: alle Parameter als Tabelle vor der Einreichung; ungültige
  Werte (Dauer 5-15 s, Steps 4-40 usw.) werden serverseitig abgelehnt.
- ☁️ **Cloudflare-Tunnel**: erkennt lokalen 8188 / bestehende Tunnel / AutoDL und startet
  bzw. nutzt einen TryCloudflare-Tunnel, wenn Fernzugriff nötig ist.
- 📥 **Batch-Einreichung & fortsetzbares Monitoring**: Referenzbilder hochladen, Segmente
  einreichen, pollen und herunterladen — mit automatischen Wiederholungen und dauerhaftem
  Status.
- ✂️ **JianYing-Automontage**: erstellt eine JianYing-Entwurfsfassung (Clips + Überblendungen)
  über jianying-editor, optional mit automatischem MP4-Export.
- 🖥️ **Onboarding beim ersten Start**: fragt Auto-Update, erkennt ComfyUI, bewertet die
  Hardware, leitet den ModelScope-Modell-Download an und fragt optional nach Hilfs-Skills
  und MCP — jede Frage erst nach Erklärung ihres Zwecks.

## Installation

Von skills.sh (empfohlen):

```bash
npx skills add TFboy1/oh-my-minimaxh3-director --skill oh-my-minimaxh3-director
```

Oder klonen:

```bash
git clone https://github.com/TFboy1/oh-my-minimaxh3-director.git
```

## Erste Verwendung

Beim ersten Aufruf fragt das Skill Folgendes ab (mit Zweckangabe):

1. **Auto-Update** aktivieren? (empfohlen);
2. Ist **ComfyUI** installiert? (sonst Download-Anleitung für die Desktop-Version);
3. **Hardware-Erkennung**, ob die Maschine MiniMax H3 ausführen kann;
4. Sind die **MiniMax-H3-Modelle** heruntergeladen? (sonst ModelScope-Anleitung);
5. Optionale Abhängigkeiten: `h3-prompt-writing` (Prompts), `jianying-editor` (Schnitt),
   `comfy-mcp` (ComfyUI-Verwaltung).

Vollständige Anleitung: [references/setup-guide.md](../references/setup-guide.md)

## Verwendung

In Codex einfach sagen:

> Verwende $oh-my-minimaxh3-director, um dieses Skript in ein Video zu verwandeln

Pipeline:

```text
Skript → Storyboard → H3-Workflows → Parameterbestätigung → Generierung
→ Clip-Download → JianYing-Entwurf → (optional) Auto-Export
```

Manuell:

```bash
python scripts/probe_comfy.py --workspace <Wurzel> --write
python scripts/ensure_cloudflared.py --workspace <Wurzel>
python scripts/build_workflows.py --project <Projekt> --workspace <Wurzel>
python scripts/submit_jobs.py --project <Projekt> --workspace <Wurzel>
python scripts/monitor_jobs.py --project <Projekt> --workspace <Wurzel>
python scripts/generate_assembly.py --project <Projekt> --title <Titel>
```

## Hardware-Anforderungen

`python scripts/check_hardware.py` (bzw. `--remote-url <URL>` für eine entfernte GPU):

| VRAM | Bewertung | Empfehlung |
|---|---:|---|
| < 12 GB | Lokal nicht empfohlen | Cloud-GPU (AutoDL 24 GB+) oder Comfy Cloud |
| 12-16 GB | Einstieg | int8/nvfp4 quantisiert + 4-Step Turbo, 0.4 MP kurz |
| 16-24 GB | Empfohlen | 0.4-0.6 MP, 10-s-Clips |
| 24 GB+ | High-End | 0.6-1 MP, 10-15 s |

Modelle insgesamt ~40 GB; NVIDIA-GPU + CUDA erforderlich; 60 GB+ freier Speicher empfohlen.

## Lizenz

Modellgewichte unter der MiniMax-H3-Community-Lizenz; der Skill-Code unter MIT.
