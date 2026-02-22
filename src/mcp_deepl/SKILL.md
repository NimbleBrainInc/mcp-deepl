# DeepL

## Tool Selection

| Intent | Tool |
|--------|------|
| Translate text | `translate_text(text, target_lang)` |
| Translate with glossary | `translate_with_glossary(text, target_lang, glossary_id)` |
| Detect language | `detect_language(text)` |
| List supported languages | `list_languages(language_type)` |
| Check API quota | `get_usage()` |
| List glossaries | `list_glossaries()` |
| Create glossary | `create_glossary(name, source_lang, target_lang, entries)` |
| Get glossary details | `get_glossary(glossary_id)` |
| Delete glossary | `delete_glossary(glossary_id)` |

## translate_text vs translate_with_glossary

- **Default**: Use `translate_text` for all translation requests.
- **With glossary**: Use `translate_with_glossary` only when the user explicitly mentions a glossary or wants domain-specific terminology enforced. Requires a `glossary_id` from `list_glossaries` or `create_glossary`.

## Language Codes

- **Target languages** use regional variants: `EN-US`, `EN-GB`, `PT-BR`, `PT-PT`, `ZH-HANS`, `ZH-HANT`
- **Source languages** use base codes: `EN`, `DE`, `FR`, `ES`, `PT`, `ZH`
- When unsure of region, default to `EN-US` for English, `PT-BR` for Portuguese, `ZH-HANS` for Chinese

## Formality

Only some languages support the `formality` parameter (e.g., DE, FR, ES, IT, PT, NL, PL, JA, RU).
Use `list_languages(language_type="target")` to check `supports_formality`.
Values: `default`, `more`, `less`, `prefer_more`, `prefer_less`.

## Glossary Workflow

1. `create_glossary(name, source_lang, target_lang, entries)` — entries is a dict of source→target pairs
2. `translate_with_glossary(text, target_lang, glossary_id)` — use the returned `glossary_id`
3. `delete_glossary(glossary_id)` — clean up when no longer needed
