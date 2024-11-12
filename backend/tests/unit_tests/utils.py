class AIModel:
    MISTRALAI = "mistralai/Mistral-7B-Instruct-v0.2"
    PERPLEXITY = "perplexity/Perplexity-7B-Instruct-v0.2"

    @classmethod
    def all(cls):
        return [cls.MISTRALAI, cls.PERPLEXITY]


def make_test_llm_config():
    return {
        AIModel.MISTRALAI: 'http://mock-mistralai/complete',
        AIModel.PERPLEXITY: 'http://mock-perplexity/complete',
    }
