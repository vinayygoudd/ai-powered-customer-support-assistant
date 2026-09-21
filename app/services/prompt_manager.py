from pathlib import Path

class PromptManager:
    VERSION = "v1.0"

    def __init__(self, prompt_dir):
        self.prompt_dir = Path(prompt_dir)

    def render(self, name, **context):
        path = self.prompt_dir / f"{name}.txt"
        template = path.read_text(encoding="utf-8")
        return template.format(**context)

    def response_prompt(self, **context):
        return self.render("response_prompt", **context)

    def summary_prompt(self, **context):
        return self.render("summary_prompt", **context)

    def escalation_prompt(self, **context):
        return self.render("escalation_prompt", **context)
