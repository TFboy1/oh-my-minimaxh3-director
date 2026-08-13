<p align="center">
  <img src="../banner.svg" alt="oh-my-minimaxh3-director Banner" width="100%"/>
</p>

[![Skills.sh](https://img.shields.io/badge/Skills.sh-Install%20Skill-00C853?style=for-the-badge&logo=hackthebox&logoColor=white)](https://skills.sh/tfboy1/oh-my-minimaxh3-director/oh-my-minimaxh3-director) [![爱发电](https://img.shields.io/badge/爱发电-Support%20Me-FF69B4?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://www.ifdian.net/item/1a20ed042f0711f1865a52540025c377) [![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-☕-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.creem.io/payment/prod_1yc40mIhKwwrc7iqFOG9G2) [![GitHub Stars](https://img.shields.io/github/stars/tfboy1/oh-my-minimaxh3-director?style=for-the-badge&logo=github&color=yellow)](https://github.com/TFboy1/oh-my-minimaxh3-director/stargazers) [![License](https://img.shields.io/github/license/tfboy1/oh-my-minimaxh3-director?style=for-the-badge&color=blue)](LICENSE)

[![简体中文](https://img.shields.io/badge/简体中文-README-blue?style=flat-square)](../README.md) [![English](https://img.shields.io/badge/English-README-blue?style=flat-square)](README_EN.md) [![日本語](https://img.shields.io/badge/日本語-README-blue?style=flat-square)](README_JA.md) [![Français](https://img.shields.io/badge/Français-Current-red?style=flat-square)](#) [![Deutsch](https://img.shields.io/badge/Deutsch-README-blue?style=flat-square)](README_DE.md)

<p align="center">
Votre réalisateur IA. Donnez-moi un script, je vous rends le montage final —
un pipeline automatisé : storyboard → génération MiniMax H3 → assemblage JianYing en un clic.
</p>

## Fonctionnalités

- 🎬 **Storyboard automatique** : découpe un script en segments (10 s par défaut, 2-3 plans
  chacun) et génère `storyboard.md`, `storyboard.json` et les prompts H3 en six parties.
- 🎞️ **Routage de workflows MiniMax H3** : choisit automatiquement Ref2VA (images de
  référence), T2V (texte seul) ou I2V (première/dernière image) et patche les paramètres par
  `class_type` — jamais d'IDs de nœuds codés en dur.
- ✅ **Confirmation des paramètres** : un tableau récapitulatif avant soumission ; les valeurs
  invalides (durée 5-15 s, steps 4-40…) sont rejetées côté backend.
- ☁️ **Tunnel Cloudflare** : détecte le 8188 local, les tunnels existants et AutoDL, puis
  démarre/réutilise un tunnel TryCloudflare quand l'accès distant est nécessaire.
- 📥 **Soumission par lots et monitoring reprisable** : upload des références, soumission,
  polling et téléchargement avec reprises automatiques et état persistant.
- ✂️ **Assemblage JianYing** : crée un brouillon JianYing (clips ordonnés + fondus) via
  jianying-editor, avec export MP4 optionnel.
- 🖥️ **Onboarding première utilisation** : auto-update, détection ComfyUI, évaluation du
  matériel, téléchargement des modèles depuis ModelScope, et installation des dépendances
  optionnelles — chaque question expliquée avant d'être posée.

## Installation

Depuis skills.sh (recommandé) :

```bash
npx skills add TFboy1/oh-my-minimaxh3-director --skill oh-my-minimaxh3-director
```

Ou par clonage :

```bash
git clone https://github.com/TFboy1/oh-my-minimaxh3-director.git
```

## Première utilisation

À la première invocation, le skill confirme avec vous, en expliquant l'utilité de chacun :

1. Activer la **mise à jour automatique** ? (recommandé) ;
2. **ComfyUI** est-il installé ? (sinon, tutoriel de téléchargement du desktop) ;
3. **Détection matérielle** pour savoir si la machine peut faire tourner MiniMax H3 ;
4. Les **modèles MiniMax H3** sont-ils téléchargés ? (sinon, tutoriel ModelScope) ;
5. Dépendances optionnelles : `h3-prompt-writing` (prompts), `jianying-editor`
   (assemblage), `comfy-mcp` (gestion ComfyUI).

Tutoriel complet : [references/setup-guide.md](../references/setup-guide.md)

## Utilisation

Dans Codex, dites simplement :

> Utilise $oh-my-minimaxh3-director pour transformer ce script en vidéo

Pipeline :

```text
script → storyboard → workflows H3 → confirmation paramètres → génération
→ téléchargement des clips → brouillon JianYing → (option) export auto
```

Manuel :

```bash
python scripts/probe_comfy.py --workspace <racine> --write
python scripts/ensure_cloudflared.py --workspace <racine>
python scripts/build_workflows.py --project <projet> --workspace <racine>
python scripts/submit_jobs.py --project <projet> --workspace <racine>
python scripts/monitor_jobs.py --project <projet> --workspace <racine>
python scripts/generate_assembly.py --project <projet> --title <titre>
```

## Configuration matérielle requise

`python scripts/check_hardware.py` (ou `--remote-url <URL>` pour un GPU distant) :

| VRAM | Verdict | Suggestion |
|---|---:|---|
| < 12 Go | Non recommandé en local | GPU cloud (AutoDL 24 Go+) ou Comfy Cloud |
| 12-16 Go | Entrée de gamme | Quantification int8/nvfp4 + Turbo 4 pas, 0.4 MP court |
| 16-24 Go | Recommandé | 0.4-0.6 MP, clips de 10 s |
| 24 Go+ | Haut de gamme | 0.6-1 MP, 10-15 s |

Modèles ~40 Go au total ; GPU NVIDIA + CUDA requis ; 60 Go+ de disque conseillés.

## Licence

Poids du modèle sous licence communautaire MiniMax H3 ; code du skill sous MIT.
