from llama_cpp import Llama
import os

class LocalLLM:
    def __init__(self):
        model_path = os.path.join("models", "llm", "mistral-7b-instruct-v0.1.Q4_K_M.gguf")
        self.model = Llama(model_path=model_path, n_ctx=2048, n_threads=4)

    def ask(self, prompt: str, stream=False, **kwargs):
        # kwargs can include max_tokens, temperature, etc.
        if stream:
            for output in self.model(prompt, stream=True, max_tokens=128, temperature=0.7, top_p=0.95, repeat_penalty=1.1):
                # output is a dict, extract text
                if "choices" in output and output["choices"]:
                    yield output["choices"][0].get("text", "")
                elif "text" in output:
                    yield output["text"]
                else:
                    yield str(output)
        else:
            output = self.model(prompt, max_tokens=128, temperature=0.7, top_p=0.95, repeat_penalty=1.1)
            return output["choices"][0]["text"].strip()