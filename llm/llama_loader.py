import os


class LlamaLoader:
    """
    Online LLaMA-3 loader using Groq API.
    Used ONLY for explanation generation.
    """

    def __init__(self, model_name="llama-3.1-8b-instant"):
        api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        if api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=api_key)
            except Exception:
                # Fall back to no-op if Groq is unavailable
                self.client = None
        self.model = model_name

    def generate(self, prompt: str) -> str:
        if not self.client:
            return ""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a nutrition explanation assistant. "
                        "You only explain decisions already made. "
                        "You never suggest new meals or change calories."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4,
            max_tokens=500
        )
        return response.choices[0].message.content
