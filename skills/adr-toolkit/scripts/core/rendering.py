"""Render deterministic ADR Markdown from localized structural strings."""
from scripts.core.locale import load_locale

PROMPT_KEYS = (
    "prompt.title", "prompt.problem", "prompt.options", "prompt.decision",
    "prompt.rationale", "prompt.good", "prompt.bad", "prompt.confirmation",
    "prompt.revisit",
)


def render_minimal(locale: str, values: dict) -> str:
    strings = load_locale(locale)
    options = "\n".join(f"* {option}" for option in values["options"])
    return (
        f"# {values['title']}\n\n"
        f"## {strings['heading.context']}\n\n{values['problem']}\n\n"
        f"## {strings['heading.considered_options']}\n\n{options}\n\n"
        f"## {strings['heading.decision_outcome']}\n\n"
        f"{strings['label.chosen_option']}: **{values['decision']}**, "
        f"{strings['label.because']} {values['rationale']}.\n\n"
        f"## {strings['heading.consequences']}\n\n"
        f"* {strings['label.good']}: {values['good']}\n"
        f"* {strings['label.bad']}: {values['bad']}\n\n"
        f"## {strings['heading.confirmation']}\n\n{values['confirmation']}\n\n"
        f"## {strings['heading.revisit_triggers']}\n\n* {values['revisit']}\n"
    )


def interactive_prompts(locale: str) -> tuple:
    strings = load_locale(locale)
    return tuple(strings[key] for key in PROMPT_KEYS)


def render_initial_adr(locale: str, adr_dir: str) -> tuple:
    strings = load_locale(locale)
    values = {
        "title": strings["init.title"],
        "problem": strings["init.problem"],
        "options": [strings["init.option.none"], strings["init.option.wiki"], strings["init.option.adr"]],
        "decision": strings["init.decision"],
        "rationale": strings["init.rationale"],
        "good": strings["init.good"],
        "bad": strings["init.bad"],
        "confirmation": strings["init.confirmation"].format(adr_dir=adr_dir),
        "revisit": strings["init.revisit"],
    }
    return values["title"], render_minimal(locale, values)


def render_template(locale: str, *, full: bool) -> str:
    if full:
        return _render_full_template(load_locale(locale))
    return render_minimal(locale, {
        "title": "{title}", "problem": "{problem and constraints}",
        "options": ["{option one}", "{option two}"],
        "decision": "{chosen option}", "rationale": "{rationale}",
        "good": "{positive consequence}", "bad": "{negative consequence}",
        "confirmation": "{how implementation will be verified}",
        "revisit": "{condition that should reopen the decision}",
    })


def _render_full_template(strings: dict) -> str:
    return (
        "# {title}\n\n"
        f"## {strings['heading.context']}\n\n{{problem and constraints}}\n\n"
        f"## {strings['heading.decision_drivers']}\n\n* {{driver one}}\n* {{driver two}}\n\n"
        f"## {strings['heading.considered_options']}\n\n* {{option one}}\n* {{option two}}\n* {{option three}}\n\n"
        f"## {strings['heading.decision_outcome']}\n\n"
        f"{strings['label.chosen_option']}: **{{chosen option}}**, {strings['label.because']} {{rationale}}.\n\n"
        f"### {strings['heading.consequences']}\n\n"
        f"* {strings['label.good']}: {{positive consequence}}\n* {strings['label.bad']}: {{negative consequence}}\n\n"
        f"### {strings['heading.confirmation']}\n\n{{how implementation will be verified}}\n\n"
        f"## {strings['heading.pros_cons']}\n\n### {{option one}}\n\n"
        f"* {strings['label.good']}, {strings['label.because']} {{argument}}\n"
        f"* {strings['label.bad']}, {strings['label.because']} {{argument}}\n\n"
        "### {option two}\n\n"
        f"* {strings['label.good']}, {strings['label.because']} {{argument}}\n"
        f"* {strings['label.bad']}, {strings['label.because']} {{argument}}\n\n"
        f"## {strings['heading.revisit_triggers']}\n\n* {{condition that should reopen the decision}}\n"
    )
