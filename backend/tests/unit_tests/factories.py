import time
from datetime import datetime

import factory
import factory.fuzzy

from utils.db import db
from tables.metrics import Metric
from tables.api_key import APIKey
from tables.llm_model import LLMModel
from tables.replicas import Replica

from .utils import AIModel


VALID_MODELS = AIModel.all()


class APIKeyFactory(factory.alchemy.SQLAlchemyModelFactory):
    """
    Factory for APIKey model.
    """

    class Meta:
        model = APIKey
        sqlalchemy_session = db.session

    id = factory.Sequence(lambda n: n + 1)
    user_id = factory.Faker("uuid4")
    api_key = factory.Faker("uuid4")
    allowed_rpm = factory.fuzzy.FuzzyInteger(low=50, high=100)
    enabled = factory.Faker("boolean", chance_of_getting_true=75)


class MetricFactory(factory.alchemy.SQLAlchemyModelFactory):
    """
    Factory for Metric model.
    """

    class Meta:
        model = Metric
        sqlalchemy_session = db.session

    id = factory.Sequence(lambda n: n + 1)
    api_key = factory.SubFactory(APIKeyFactory)
    api_key_id = factory.SelfAttribute("api_key.id")
    input = factory.Faker("text")
    created = factory.LazyFunction(lambda: int(time.mktime(datetime.now().timetuple())))
    model = factory.fuzzy.FuzzyChoice(VALID_MODELS)
    choices = factory.Faker("text")
    prompt_tokens = factory.Faker("random_int", min=0, max=100)
    total_tokens = factory.Faker("random_int", min=0, max=100)
    completion_tokens = factory.Faker("random_int", min=0, max=100)
    duration = factory.fuzzy.FuzzyFloat(low=0.1, high=10.0, precision=1)


class LLMModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    """
    Factory for LLMModel model.
    """

    class Meta:
        model = LLMModel
        sqlalchemy_session = db.session

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("name")


class ReplicaFactory(factory.alchemy.SQLAlchemyModelFactory):
    """
    Factory for Replica model.
    """

    class Meta:
        model = Replica
        sqlalchemy_session = db.session

    id = factory.Sequence(lambda n: n + 1)
    llm_model = factory.SubFactory(LLMModelFactory)
    model_id = factory.SelfAttribute("llm_model.id")
    endpoint = factory.Faker("url")
    rate_limit = factory.Faker(
        "pydecimal", left_digits=3, right_digits=2, positive=True
    )
    flavor_name = factory.Faker("word")
    vm_status = factory.Faker("word")
