from unittest.mock import MagicMock, patch

import pytest

from library import DatabaseManager


@pytest.fixture
def manager():
    postgres = MagicMock()
    mongo = MagicMock()
    sqlite = MagicMock()
    return DatabaseManager(postgres, mongo, sqlite)


@patch("library.inspect")
def test_get_postgres_tables(mock_inspect, manager):
    mock_inspector = MagicMock()
    mock_inspector.get_table_names.return_value = ["table1", "table2"]
    mock_inspect.return_value = mock_inspector

    tables = manager.get_postgres_tables()

    assert tables == ["table1", "table2"]
    mock_inspect.assert_called_once_with(manager.postgres_engine)


@patch("library.inspect")
def test_get_sqlite_tables(mock_inspect, manager):
    mock_inspector = MagicMock()
    mock_inspector.get_table_names.return_value = ["sql_table1"]
    mock_inspect.return_value = mock_inspector

    tables = manager.get_sqlite_tables()

    assert tables == ["sql_table1"]
    mock_inspect.assert_called_once_with(manager.sqlite_engine)


def test_get_mongo_tables(manager):
    manager.mongo_db.list_collection_names.return_value = ["mongo_col1"]

    tables = manager.get_mongo_tables()

    assert tables == ["mongo_col1"]
    manager.mongo_db.list_collection_names.assert_called_once()
