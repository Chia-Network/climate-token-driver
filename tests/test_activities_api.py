from unittest import mock
from urllib.parse import urlencode

import fastapi

from app.schemas import activity
from app import crud


class TestActivities:
    def test_activities_with_search_by_than_error(self, fastapi_client, monkeypatch):
        test_request = {"search_by": "error", "search": ""}

        params = urlencode(test_request)
        response = fastapi_client.get("v1/activities/", params=params)

        assert response.status_code == fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_activities_with_empty_climate_warehouse_than_success(self, fastapi_client, monkeypatch):
        test_request = {}
        test_response = activity.ActivitiesResponse()

        mock_climate_warehouse_data = mock.MagicMock()
        mock_climate_warehouse_data.return_value = []

        monkeypatch.setattr(crud.ClimateWareHouseCrud, "combine_climate_units_and_metadata",
                            mock_climate_warehouse_data)

        params = urlencode(test_request)
        response = fastapi_client.get("v1/activities/", params=params)

        assert response.status_code == fastapi.status.HTTP_200_OK
        assert response.json() == test_response

    def test_activities_with_empty_db_than_success(self, fastapi_client, monkeypatch):
        test_request = {}
        test_response = activity.ActivitiesResponse()

        mock_db_data = mock.MagicMock()
        mock_db_data.return_value = ([], 0)

        monkeypatch.setattr(crud.DBCrud, "select_activity_with_pagination", mock_db_data)

        params = urlencode(test_request)
        response = fastapi_client.get("v1/activities/", params=params)

        assert response.status_code == fastapi.status.HTTP_200_OK
        assert response.json() == test_response

