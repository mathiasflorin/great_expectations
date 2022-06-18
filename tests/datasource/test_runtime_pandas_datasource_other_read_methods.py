import datetime
import warnings

import pandas as pd
import pytest
import sqlalchemy as sa

from great_expectations.data_context.util import file_relative_path
from great_expectations.datasource.misc_types import BatchIdentifiers, NewConfiguredBatchRequest, PassthroughParameters
from great_expectations.datasource.runtime_pandas_datasource import (
    RuntimePandasDatasource,
)
from tests.test_utils import _get_batch_request_from_validator, _get_data_from_validator

### Tests of the read_* methods on RuntimePandasDatasource. Also from_dataframe.
### These don't go into edge cases, because we trust the decorators to cover them.

def test_RuntimePandasDatasource_read_json():
    my_datasource = RuntimePandasDatasource("my_datasource")
    my_validator = my_datasource.read_json(
        '{"a":[1,4], "b":[2,5], "c":[3,6]}',
        timestamp=0,
    )

    my_data = _get_data_from_validator(my_validator)
    assert isinstance(my_data, pd.DataFrame)
    assert my_data.to_dict() == {
        "a": {0: 1, 1: 4},
        "b": {0: 2, 1: 5},
        "c": {0: 3, 1: 6},
    }

    my_batch_request = _get_batch_request_from_validator(my_validator)
    assert my_batch_request.batch_identifiers == {
        "timestamp": 0,
        "id_": None,
    }


def test_RuntimePandasDatasource_read_table():
    my_datasource = RuntimePandasDatasource("my_datasource")
    my_validator = my_datasource.read_table(
        file_relative_path(__file__, "fixtures/example_3.tsv"),
        delimiter="|",
        skiprows=2,
    )

    my_data = _get_data_from_validator(my_validator)
    assert isinstance(my_data, pd.DataFrame)
    assert my_data.to_dict() == {
        "a": {0: 1, 1: 4},
        "b": {0: 2, 1: 5},
        "c": {0: 3, 1: 6},
    }

@pytest.mark.skip(
    "This test doesn't work on some headless infrastructure, including our CI setup."
)
def test_RuntimePandasDatasource_read_clipboard():
    import pyperclip

    old_clipboard_text = pyperclip.paste()

    pyperclip.copy(
        """
	a	b	c
0	1	2	3
1	4	5	6
"""
    )

    my_datasource = RuntimePandasDatasource("my_datasource")
    my_validator = my_datasource.read_clipboard(timestamp=0)

    my_data = _get_data_from_validator(my_validator)
    assert isinstance(my_data, pd.DataFrame)
    assert my_data.to_dict() == {
        "a": {0: 1, 1: 4},
        "b": {0: 2, 1: 5},
        "c": {0: 3, 1: 6},
    }

    my_batch_request = _get_batch_request_from_validator(my_validator)
    assert my_batch_request.batch_identifiers == {
        "timestamp": 0,
        "id_": None,
    }

    # Restore the old contents of the clipboard
    pyperclip.copy(old_clipboard_text)


@pytest.fixture
def sqlite_engine():
    engine = sa.create_engine("sqlite://")
    df = pd.DataFrame(
        {
            "a": [1, 4],
            "b": [2, 5],
            "c": [3, 6],
        }
    )
    df.to_sql(name="test_table", con=engine, index=False)
    return engine


def test_RuntimePandasDatasource_read_sql_table_with_con_as_keyword_arg(sqlite_engine):
    my_datasource = RuntimePandasDatasource("my_datasource")
    my_validator = my_datasource.read_sql_table(
        "test_table", con=sqlite_engine, timestamp=0
    )

    my_data = _get_data_from_validator(my_validator)
    assert isinstance(my_data, pd.DataFrame)
    assert my_data.to_dict() == {
        "a": {0: 1, 1: 4},
        "b": {0: 2, 1: 5},
        "c": {0: 3, 1: 6},
    }

    my_batch_request = _get_batch_request_from_validator(my_validator)
    assert my_batch_request.passthrough_parameters["args"] == []
    assert my_batch_request.passthrough_parameters["kwargs"] == {}
    assert my_batch_request.batch_identifiers == {
        "timestamp": 0,
        "id_": "test_table",
    }


def test_RuntimePandasDatasource_read_sql_table_with_con_as_positional_arg(
    sqlite_engine,
):
    my_datasource = RuntimePandasDatasource("my_datasource")
    my_validator = my_datasource.read_sql_table(
        "test_table", sqlite_engine, timestamp=0
    )

    my_data = _get_data_from_validator(my_validator)
    assert isinstance(my_data, pd.DataFrame)
    assert my_data.to_dict() == {
        "a": {0: 1, 1: 4},
        "b": {0: 2, 1: 5},
        "c": {0: 3, 1: 6},
    }

    my_batch_request = _get_batch_request_from_validator(my_validator)
    assert my_batch_request.passthrough_parameters["args"] == []
    assert my_batch_request.passthrough_parameters["kwargs"] == {}
    assert my_batch_request.batch_identifiers == {
        "timestamp": 0,
        "id_": "test_table",
    }


def test_RuntimePandasDatasource_read_sql_query(sqlite_engine):
    my_datasource = RuntimePandasDatasource("my_datasource")
    my_validator = my_datasource.read_sql_query(
        "SELECT * FROM test_table;", con=sqlite_engine, timestamp=0
    )

    my_data = _get_data_from_validator(my_validator)
    assert isinstance(my_data, pd.DataFrame)
    assert my_data.to_dict() == {
        "a": {0: 1, 1: 4},
        "b": {0: 2, 1: 5},
        "c": {0: 3, 1: 6},
    }

    my_batch_request = _get_batch_request_from_validator(my_validator)
    assert my_batch_request.passthrough_parameters["args"] == []
    assert my_batch_request.passthrough_parameters["kwargs"] == {}
    assert my_batch_request.batch_identifiers == {
        "timestamp": 0,
        "id_": None,
    }


def test_RuntimePandasDatasource_read_sql_with_query(sqlite_engine):
    my_datasource = RuntimePandasDatasource("my_datasource")
    my_validator = my_datasource.read_sql(
        "SELECT * FROM test_table;", con=sqlite_engine, timestamp=0
    )
    my_data = _get_data_from_validator(my_validator)
    assert isinstance(my_data, pd.DataFrame)
    assert my_data.to_dict() == {
        "a": {0: 1, 1: 4},
        "b": {0: 2, 1: 5},
        "c": {0: 3, 1: 6},
    }

    my_batch_request = _get_batch_request_from_validator(my_validator)
    assert isinstance(my_batch_request, NewConfiguredBatchRequest)
    assert my_batch_request.passthrough_parameters["args"] == []
    assert my_batch_request.passthrough_parameters["kwargs"] == {}
    assert my_batch_request.batch_identifiers == {
        "timestamp": 0,
        "id_": None,
    }


def test_RuntimePandasDatasource_read_sql_with_table(sqlite_engine):
    my_datasource = RuntimePandasDatasource("my_datasource")
    my_validator = my_datasource.read_sql("test_table", con=sqlite_engine, timestamp=0)

    my_data = _get_data_from_validator(my_validator)
    assert isinstance(my_data, pd.DataFrame)
    assert my_data.to_dict() == {
        "a": {0: 1, 1: 4},
        "b": {0: 2, 1: 5},
        "c": {0: 3, 1: 6},
    }

    my_batch_request: NewConfiguredBatchRequest = _get_batch_request_from_validator(
        my_validator
    )
    assert isinstance(my_batch_request, NewConfiguredBatchRequest)
    assert my_batch_request.passthrough_parameters["args"] == []
    assert my_batch_request.passthrough_parameters["kwargs"] == {}
    assert my_batch_request.batch_identifiers == {
        "timestamp": 0,
        "id_": "test_table",
    }


def test_RuntimePandasDatasource_read_dataframe():
    my_datasource = RuntimePandasDatasource("my_datasource")
    my_df = pd.DataFrame(
        {
            "a": [1, 4],
            "b": [2, 5],
            "c": [3, 6],
        }
    )

    my_validator = my_datasource.from_dataframe(
        my_df,
        timestamp=0,
    )
    
    my_data = _get_data_from_validator(my_validator)
    assert isinstance(my_data, pd.DataFrame)
    assert my_data.to_dict() == {
        "a": {0: 1, 1: 4},
        "b": {0: 2, 1: 5},
        "c": {0: 3, 1: 6},
    }

    my_batch_request = _get_batch_request_from_validator(my_validator)
    assert my_batch_request.passthrough_parameters["args"] == []
    assert my_batch_request.passthrough_parameters["kwargs"] == {}
    assert my_batch_request.batch_identifiers == {
        "timestamp": 0,
        "id_": None,
    }


# !!! Move this to a different file

def test_NewConfiguredBatchRequest__str__():
    assert NewConfiguredBatchRequest(
        datasource_name='runtime_pandas',
        data_asset_name='DEFAULT_DATA_ASSET',
        batch_identifiers=BatchIdentifiers(
            id_= None,
            timestamp= datetime.datetime(2022, 6, 18, 10, 1, 25, 294504)
        ),
        passthrough_parameters=PassthroughParameters(
            args= [],
            kwargs= {}
        )
    ).__str__() == """NewConfiguredBatchRequest(
    datasource_name='runtime_pandas',
    data_asset_name='DEFAULT_DATA_ASSET',
    batch_identifiers='{'id_': None, 'timestamp': datetime.datetime(2022, 6, 18, 10, 1, 25, 294504)}',
    passthrough_parameters='{'args': [], 'kwargs': {}}',
)
"""