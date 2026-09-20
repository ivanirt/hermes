# owl-bot

Bot de Hermes Agent (perfil `pdf-obsidian`) para construir un vault de Obsidian
a partir de PDFs/libros: lee el PDF, hace un compendio de conceptos y los desarrolla
en notas del vault.

## Contenido

| Ruta | Que es |
|---|---|
| `SOUL.md` | Personalidad del bot |
| `profile.yaml` | Metadatos del perfil (nombre visible: owl-bot) |
| `config.yaml` | Configuracion del perfil |
| `memories/MEMORY.md` | Memoria persistente |
| `skills/pdf-to-vault/` | Skill: PDF -> notas del vault |
| `skills/literature-vault/` | Skill: convenciones y estructura del vault |
| `.env.example` | Claves necesarias (sin valores) |

## Instalacion

```bash
cp .env.example .env   # y rellena OPENROUTER_API_KEY, TELEGRAM_BOT_TOKEN, etc.
```

En Hermes, el perfil vive en `~/.hermes/profiles/<nombre>/`: copia `SOUL.md`, `memories/`,
`config.yaml` y las skills a `skills/note-taking/` de ese perfil.
