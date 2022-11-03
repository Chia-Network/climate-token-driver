from unittest import mock

from app.crud.db import DBCrud


class TestUpdateBlockState:
    def test_with_block_height_then_success(self):
        mock_db = mock.MagicMock()
        actual = DBCrud(db=mock_db).update_block_state(peak_height=1)
        assert actual is True

    def test_with_current_height_then_success(self):
        mock_db = mock.MagicMock()
        actual = DBCrud(db=mock_db).update_block_state(current_height=1)
        assert actual is True
