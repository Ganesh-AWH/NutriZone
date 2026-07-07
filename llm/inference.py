from llm.prompt_templates import explanation_prompt

class LLMInference:
    def __init__(self, llm_loader):
        self.llm = llm_loader

    def explain(self, profile, plan, feedback=None):
        prompt = explanation_prompt(profile, plan, feedback)
        return self.llm.generate(prompt)
