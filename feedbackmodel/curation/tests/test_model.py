import pytest
from curation.model.base_model import BaseModel

def test_base_model_is_abstract():
    with pytest.raises(TypeError):
        BaseModel()
