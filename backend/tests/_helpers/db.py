from collections.abc import Sequence
from typing import Any
from unittest.mock import MagicMock


def setup_mock_execute(
    mock_db: MagicMock,
    return_all: Sequence[Any] | None = None,
    return_scalar: Any | None = None,
    return_one_or_none: Any | None = None,
    return_scalars_all: Sequence[Any] | None = None,
):
    execute_mock = MagicMock()
    scalars_mock = MagicMock()
    execute_mock.scalars.return_value = scalars_mock
    if return_scalars_all is not None:
        scalars_mock.all.return_value = return_scalars_all
    elif return_all is not None:
        scalars_mock.all.return_value = return_all
    if return_scalar is not None:
        scalars_mock.scalar.return_value = return_scalar
    if return_one_or_none is not None:
        scalars_mock.one_or_none.return_value = return_one_or_none
        execute_mock.scalar_one_or_none.return_value = return_one_or_none
    else:
        execute_mock.scalar_one_or_none.return_value = None
    execute_mock.scalar.return_value = return_scalar
    mock_db.execute.return_value = execute_mock
    # Support db.scalars(stmt) pattern (used by some sub-module CRUDs)
    scalars_direct_mock = MagicMock()
    if return_scalars_all is not None:
        scalars_direct_mock.all.return_value = return_scalars_all
    elif return_all is not None:
        scalars_direct_mock.all.return_value = return_all
    mock_db.scalars.return_value = scalars_direct_mock
    return execute_mock


def setup_mock_query(
    mock_db: MagicMock,
    model_class: type,
    return_all: Sequence[Any] | None = None,
    return_one: Any | None = None,
    return_first: Any | None = None,
    return_scalar: Any | None = None,
    return_count: int = 0,
):
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value = mock_query
    mock_query.filter_by.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = return_all if return_all is not None else []
    mock_query.first.return_value = return_first
    mock_query.one.return_value = return_one
    mock_query.one_or_none.return_value = return_one
    mock_query.scalar.return_value = return_scalar if return_scalar is not None else return_count
    mock_query.count.return_value = return_count
    return mock_query
