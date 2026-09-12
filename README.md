# Utility Discord bot

A clean starting point for a custom community bot, built with `discord.py` 2.x and modern **slash commands**.

| Command | What it does |
|---|---|
| `/ping` | latency check |
| `/poll question options` | reaction poll, 2–10 options separated by `\|` |
| `/remind minutes message` | sends you a DM after N minutes |
| `/serverinfo` | members, channels, roles, owner, creation date |
| `/userinfo [member]` | account age, join date, roles |
| `/clear amount` | bulk delete (requires *Manage Messages*) |
| *welcome* | greets new members with an embed in a chosen channel |

Also included: permission errors handled gracefully, logging, config via `.env`.

## Setup (5 minutes)
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) → *New Application* → *Bot* → *Reset Token* and copy it.
2. In *Bot*, enable **Server Members Intent** (needed for welcome messages).
3. In *OAuth2 → URL Generator*, tick `bot` + `applications.commands`, give it *Send Messages*, *Manage Messages*, *Embed Links*, *Add Reactions*, then open the generated URL to invite the bot.
4. Copy `.env.example` to `.env`, paste the token, optionally set `WELCOME_CHANNEL_ID` (right-click a channel → *Copy Channel ID*).
5. `pip install -r requirements.txt` then `python bot.py`.

## What I can build on top of this
Moderation (auto-mod, warnings, mute/ban logs), ticket systems, role menus, leveling/XP, scheduled announcements, game/API integrations, music, custom embeds, database-backed features (SQLite/Postgres), 24/7 hosting setup.

---

*FR — Bot Discord utilitaire (commandes slash) : sondages, rappels, infos serveur/membre, nettoyage, message de bienvenue. Base saine pour un bot sur mesure : modération, tickets, rôles, XP, intégrations d'API.*
