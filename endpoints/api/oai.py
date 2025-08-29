import multiprocessing as mp
from tqdm.auto import tqdm

from openai import OpenAI, AzureOpenAI


def query_helper(
    client_cls,
    client_args,
    system_prompt: str,
    user_message: str,
    model: str,
    **sampling_args
) -> str:
    # OpenAI's client cannot be directly pickled because it has a thread lock
    # inside of it, so we have to create a new client for each query.
    client = client_cls(**client_args)
    messages = []
    sampling_args |= {"stream": False}
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})
    try:
        request = client.chat.completions.create(
            model=model,
            messages=messages,
            **sampling_args,
        )
    except Exception as e:
        print(str(e))
        raise
    completion = request.choices[0].message.content
    return completion


def batch_helper(kwargs):
    return query_helper(**kwargs)


class Queryable:
    def __init__(self, model, client_cls, **client_args):
        self.model = model
        self.client_cls = client_cls
        self.client_args = client_args
        self.client = self.client_cls(**self.client_args)

    def query(self, system_prompt: str, user_message: str, **sampling_args) -> str:
        """Query the given model using the chat template.

        system_prompt (str): The model's system message. Should be None or empty for reasoning models.
        user_message (str): The message passed to the model assuming the "user" role.
        sampling_args (dict): Arguments passed directly to the OpenAI Chat API. See https://platform.openai.com/docs/api-reference/chat/create for more information.

        Returns:
            str: The response of the model.
        """

        self.validate(system_prompt, user_message)

        return query_helper(
            self.client_cls,
            self.client_args,
            system_prompt,
            user_message,
            self.model,
            **sampling_args,
        )

    def query_batch(
        self,
        system_prompt: str,
        user_messages: list[str],
        num_threads=32,
        **sampling_args
    ) -> list[str]:
        """Query the given model using the chat template.

        system_prompt (str): The model's system message. Should be None or empty for reasoning models.
        user_message (str): The message passed to the model assuming the "user" role.
        num_threads (str): The number of requests to process concurrently from the given set of user_messages. Speed should scale linearly with num_threads.
        sampling_args (dict): Arguments passed directly to the OpenAI Chat API. See https://platform.openai.com/docs/api-reference/chat/create for more information.

        Returns:
            list[str]: The responses of the model.
        """

        for user in user_messages:
            self.validate(system_prompt, user)

        """
        A multithreaded version of get_completion. Scales linearly with the number of threads because the nvdev endpoint internally batches together requests. 
        """
        n = len(user_messages)
        if not n:
            return []
        kwargs = [
            {
                "client_cls": self.client_cls,
                "client_args": self.client_args,
                "system_prompt": system_prompt,
                "user_message": user_message,
                "model": self.model,
                **sampling_args,
            }
            for user_message in user_messages
        ]
        with mp.Pool(num_threads) as p:
            r = list(tqdm(p.imap(batch_helper, kwargs), total=len(user_messages)))
        return r

    def validate(self, system_prompt: str, user_message: str):
        return True


class Endpoint(Queryable):
    def __init__(self, base_url: str, api_key: str, model: str):
        super().__init__(model, OpenAI, base_url=base_url, api_key=api_key)


class Azure(Queryable):
    def __init__(self, azure_endpoint: str, api_version: str, api_key: str, model: str):
        super().__init__(
            model,
            AzureOpenAI,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            api_key=api_key,
        )
