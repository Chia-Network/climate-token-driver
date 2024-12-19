from __future__ import annotations

from unittest import mock
from urllib.parse import urlencode

import anyio
import fastapi
import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

from app import crud, models, schemas


async def mock_get_challenge(x: crud.BlockChainCrud) -> str:
    return "testnet"


class TestActivities:
    def test_activities_with_search_by_then_error(
        self, fastapi_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with anyio.from_thread.start_blocking_portal() as portal, monkeypatch.context() as m:
            fastapi_client.portal = portal  # workaround anyio 4.0.0 incompat with TextClient
            m.setattr(crud.BlockChainCrud, "get_challenge", mock_get_challenge)
            test_request = {"search_by": "error", "search": ""}

            params = urlencode(test_request)
            response = fastapi_client.get("v1/activities/", params=params)

        assert response.status_code == fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_activities_with_empty_climate_warehouse_then_success(
        self, fastapi_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        test_response = schemas.activity.ActivitiesResponse()

        mock_climate_warehouse_data = mock.MagicMock()
        mock_climate_warehouse_data.return_value = []

        with anyio.from_thread.start_blocking_portal() as portal, monkeypatch.context() as m:
            fastapi_client.portal = portal  # workaround anyio 4.0.0 incompat with TextClient
            m.setattr(
                crud.ClimateWareHouseCrud,
                "combine_climate_units_and_metadata",
                mock_climate_warehouse_data,
            )
            m.setattr(crud.BlockChainCrud, "get_challenge", mock_get_challenge)

            params = urlencode({})
            response = fastapi_client.get("v1/activities/", params=params)

        assert response.status_code == fastapi.status.HTTP_200_OK
        assert response.json() == test_response.dict()

    def test_activities_with_empty_db_then_success(
        self, fastapi_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        test_response = schemas.activity.ActivitiesResponse()

        mock_db_data = mock.MagicMock()
        mock_db_data.return_value = ([], 0)

        with anyio.from_thread.start_blocking_portal() as portal, monkeypatch.context() as m:
            fastapi_client.portal = portal  # workaround anyio 4.0.0 incompat with TextClient
            m.setattr(crud.BlockChainCrud, "get_challenge", mock_get_challenge)
            m.setattr(crud.DBCrud, "select_activity_with_pagination", mock_db_data)
            m.setattr(crud.ClimateWareHouseCrud, "combine_climate_units_and_metadata", mock.MagicMock(return_value={}))

            params = urlencode({})
            response = fastapi_client.get("v1/activities/", params=params)

        assert response.status_code == fastapi.status.HTTP_200_OK
        assert response.json() == test_response.dict()

    def test_activities_then_success(self, fastapi_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        test_activity_data = models.activity.Activity(
            org_uid="cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
            amount=10000,
            asset_id="0x438f0630bebb927cbef0663b6b4bfb1820a754975e25a8ef20fb10b6c616c4de",
            coin_id="0x40fd5fec70b2e7e3ab110a0ac22feb67f24fe989d7f2c7018c694faeea41c40f",
            height=1720476,
            mode="PERMISSIONLESS_RETIREMENT",
            sequence_num=0,
            timestamp=1666843885,
            vintage_year=2096,
            warehouse_project_id="c9b98579-debb-49f3-b417-0adbae4ed5c7",
            beneficiary_puzzle_hash="0xe122763ec4076d3fa356fbff8bb63d1f9d78b52c3c577a01140cd4559ee32966",
            beneficiary_address="bls12381uy38v0kyqaknlg6kl0lchd3ar7wh3dfv83th5qg5pn29t8hr99nq2vsjek",
            beneficiary_name="",
            metadata_={
                "bn": "",
                "ba": "bls12381uy38v0kyqaknlg6kl0lchd3ar7wh3dfv83th5qg5pn29t8hr99nq2vsjek",
                "bp": "0xe122763ec4076d3fa356fbff8bb63d1f9d78b52c3c577a01140cd4559ee32966",
            },
        )

        test_response = schemas.activity.ActivitiesResponse(
            activities=[
                schemas.activity.ActivityWithCW(
                    **jsonable_encoder(test_activity_data),
                    cw_org={"orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd"},
                    cw_project={
                        "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                        "warehouseProjectId": "c9b98579-debb-49f3-b417-0adbae4ed5c7",
                    },
                    cw_unit={
                        "warehouseUnitId": "944c7726-db49-4cb2-adb5-7e5cff9095e2",
                        "issuanceId": "fc467985-93e9-4a63-9f00-69cdf5c86dd3",
                        "projectLocationId": None,
                        "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                        "unitOwner": None,
                        "countryJurisdictionOfOwner": "Algeria",
                        "inCountryJurisdictionOfOwner": None,
                        "serialNumberBlock": "ABC100-ABC200",
                        "unitBlockStart": "ABC100",
                        "unitBlockEnd": "ABC200",
                        "unitCount": 100,
                        "vintageYear": 2096,
                        "unitType": "Reduction - nature",
                        "marketplace": None,
                        "marketplaceLink": None,
                        "marketplaceIdentifier": "0x438f0630bebb927cbef0663b6b4bfb1820a754975e25a8ef20fb10b6c616c4de",
                        "unitTags": None,
                        "unitStatus": "Held",
                        "unitStatusReason": None,
                        "unitRegistryLink": "http://example.example",
                        "correspondingAdjustmentDeclaration": "Committed",
                        "correspondingAdjustmentStatus": "Not Started",
                        "timeStaged": "1666589844",
                        "createdAt": "2022-10-24T06:25:13.437Z",
                        "updatedAt": "2022-10-24T06:25:13.437Z",
                        "labels": [],
                        "issuance": {
                            "id": "fc467985-93e9-4a63-9f00-69cdf5c86dd3",
                            "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                            "warehouseProjectId": "c9b98579-debb-49f3-b417-0adbae4ed5c7",
                            "startDate": "2022-08-03T00:00:00.000Z",
                            "endDate": "2022-08-05T00:00:00.000Z",
                            "verificationApproach": "seer",
                            "verificationReportDate": "2022-08-06T00:00:00.000Z",
                            "verificationBody": "tea",
                            "timeStaged": None,
                            "createdAt": "2022-10-24T06:25:13.440Z",
                            "updatedAt": "2022-10-24T06:25:13.440Z",
                        },
                    },
                    metadata={
                        "bn": "",
                        "ba": "bls12381uy38v0kyqaknlg6kl0lchd3ar7wh3dfv83th5qg5pn29t8hr99nq2vsjek",
                        "bp": "0xe122763ec4076d3fa356fbff8bb63d1f9d78b52c3c577a01140cd4559ee32966",
                    },
                    token=schemas.TokenOnChain.parse_obj(
                        {
                            "org_uid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                            "warehouse_project_id": "c9b98579-debb-49f3-b417-0adbae4ed5c7",
                            "vintage_year": 2096,
                            "sequence_num": 0,
                            "index": "0x37f12cf05c5d5b254ac8019fc3b02a07f98526d57b65920a785980ad925273b7",
                            "public_key": "0x9650dc15356ba1fe3a48e50daa55ac3dfde5323226922c9bf09aae1bd9612105f323e573cfa0778c681467a0c62bc315",  # noqa: E501
                            "asset_id": "0x438f0630bebb927cbef0663b6b4bfb1820a754975e25a8ef20fb10b6c616c4de",
                            "tokenization": {
                                "mod_hash": "0x09bbb0ef739bdc4d37f0d0cec9c04453c40c264de8da8b2ce1edc3c1049406ce",
                                "public_key": "0x8cba9cb11eed6e2a04843d94c9cabecc3f8eb3118f3a4c1dd5260684f462a8c886db5963f2dcac03f54a745a42777e7c",  # noqa: E501
                            },
                            "detokenization": {
                                "mod_hash": "0x7d7fabdcf5c6cd7cae533490dfd5f98da622657cc760cb5d96891aa2a04323c9",
                                "public_key": "0xb431835fe9fa64e9bea1bbab1d4bffd15d17d997f3754b2f97c8db43ea173a8b9fa79ac3a7d58c80111fbfdd4e485f0d",  # noqa: E501
                                "signature": "0x842c093f865e2634099d321c4c9f5d540fb511012a9111929bec13c7e395cc6d9c3e68fc111763f13e9df50405e6eb2710bb553d7fa04097793bc327991d5d61584c4a10cdca304be5174d3778692ff2543f3bcc3a2c23db47704e6fc7399cc4",  # noqa: E501
                            },
                            "permissionless_retirement": {
                                "mod_hash": "0xb19c88b1b53f2db24bfb9385ddb5854327baf08bd0d50c0e1b33ccd3a4c5dbb0",
                                "signature": "0xacadbbdeffddbb8a7d43355c719c814ca18a731846cb7e67157dd1b6af7d269d264224a70b19197561c53f2a916742eb0ed21972af0bb77c74751d988733737da3b2f590a97f45f4a0beb81263936628c323d610cafc12528ea3ca0068037738",  # noqa: E501
                            },
                        }
                    ),
                )
            ],
            total=1,
        )

        mock_db_data = mock.MagicMock()
        mock_climate_warehouse_data = mock.MagicMock()
        mock_db_data.return_value = (
            [
                test_activity_data,
            ],
            1,
        )
        mock_climate_warehouse_data.return_value = [
            {
                "warehouseUnitId": "944c7726-db49-4cb2-adb5-7e5cff9095e2",
                "issuanceId": "fc467985-93e9-4a63-9f00-69cdf5c86dd3",
                "projectLocationId": None,
                "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                "unitOwner": None,
                "countryJurisdictionOfOwner": "Algeria",
                "inCountryJurisdictionOfOwner": None,
                "serialNumberBlock": "ABC100-ABC200",
                "unitBlockStart": "ABC100",
                "unitBlockEnd": "ABC200",
                "unitCount": 100,
                "vintageYear": 2096,
                "unitType": "Reduction - nature",
                "marketplace": None,
                "marketplaceLink": None,
                "marketplaceIdentifier": "0x438f0630bebb927cbef0663b6b4bfb1820a754975e25a8ef20fb10b6c616c4de",
                "unitTags": None,
                "unitStatus": "Held",
                "unitStatusReason": None,
                "unitRegistryLink": "http://example.example",
                "correspondingAdjustmentDeclaration": "Committed",
                "correspondingAdjustmentStatus": "Not Started",
                "timeStaged": "1666589844",
                "createdAt": "2022-10-24T06:25:13.437Z",
                "updatedAt": "2022-10-24T06:25:13.437Z",
                "labels": [],
                "issuance": {
                    "id": "fc467985-93e9-4a63-9f00-69cdf5c86dd3",
                    "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                    "warehouseProjectId": "c9b98579-debb-49f3-b417-0adbae4ed5c7",
                    "startDate": "2022-08-03T00:00:00.000Z",
                    "endDate": "2022-08-05T00:00:00.000Z",
                    "verificationApproach": "seer",
                    "verificationReportDate": "2022-08-06T00:00:00.000Z",
                    "verificationBody": "tea",
                    "timeStaged": None,
                    "createdAt": "2022-10-24T06:25:13.440Z",
                    "updatedAt": "2022-10-24T06:25:13.440Z",
                },
                "organization": {"orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd"},
                "token": {
                    "org_uid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                    "warehouse_project_id": "c9b98579-debb-49f3-b417-0adbae4ed5c7",
                    "vintage_year": 2096,
                    "sequence_num": 0,
                    "index": "0x37f12cf05c5d5b254ac8019fc3b02a07f98526d57b65920a785980ad925273b7",
                    "public_key": "0x9650dc15356ba1fe3a48e50daa55ac3dfde5323226922c9bf09aae1bd9612105f323e573cfa0778c681467a0c62bc315",  # noqa: E501
                    "asset_id": "0x438f0630bebb927cbef0663b6b4bfb1820a754975e25a8ef20fb10b6c616c4de",
                    "tokenization": {
                        "mod_hash": "0x09bbb0ef739bdc4d37f0d0cec9c04453c40c264de8da8b2ce1edc3c1049406ce",
                        "public_key": "0x8cba9cb11eed6e2a04843d94c9cabecc3f8eb3118f3a4c1dd5260684f462a8c886db5963f2dcac03f54a745a42777e7c",  # noqa: E501
                    },
                    "detokenization": {
                        "mod_hash": "0x7d7fabdcf5c6cd7cae533490dfd5f98da622657cc760cb5d96891aa2a04323c9",
                        "public_key": "0xb431835fe9fa64e9bea1bbab1d4bffd15d17d997f3754b2f97c8db43ea173a8b9fa79ac3a7d58c80111fbfdd4e485f0d",  # noqa: E501
                        "signature": "0x842c093f865e2634099d321c4c9f5d540fb511012a9111929bec13c7e395cc6d9c3e68fc111763f13e9df50405e6eb2710bb553d7fa04097793bc327991d5d61584c4a10cdca304be5174d3778692ff2543f3bcc3a2c23db47704e6fc7399cc4",  # noqa: E501
                    },
                    "permissionless_retirement": {
                        "mod_hash": "0xb19c88b1b53f2db24bfb9385ddb5854327baf08bd0d50c0e1b33ccd3a4c5dbb0",
                        "signature": "0xacadbbdeffddbb8a7d43355c719c814ca18a731846cb7e67157dd1b6af7d269d264224a70b19197561c53f2a916742eb0ed21972af0bb77c74751d988733737da3b2f590a97f45f4a0beb81263936628c323d610cafc12528ea3ca0068037738",  # noqa: E501
                    },
                },
                "project": {
                    "warehouseProjectId": "c9b98579-debb-49f3-b417-0adbae4ed5c7",
                    "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                },
            }
        ]
        with anyio.from_thread.start_blocking_portal() as portal, monkeypatch.context() as m:
            fastapi_client.portal = portal  # workaround anyio 4.0.0 incompat with TextClient
            m.setattr(crud.BlockChainCrud, "get_challenge", mock_get_challenge)
            m.setattr(crud.DBCrud, "select_activity_with_pagination", mock_db_data)
            m.setattr(
                crud.ClimateWareHouseCrud,
                "combine_climate_units_and_metadata",
                mock_climate_warehouse_data,
            )

            params = urlencode({})
            response = fastapi_client.get("v1/activities/", params=params)

        assert response.status_code == fastapi.status.HTTP_200_OK
        assert response.json() == jsonable_encoder(test_response)
        assert response.json()["total"] == test_response.total

    def test_activities_with_mode_search_search_by_then_success(
        self, fastapi_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        test_request = {
            "mode": "permissionless_retirement",
            "search_by": "onchain_metadata",
            "search": "0xe122763ec4076d3fa356fbff8bb63d1f9d78b52c3c577a01140cd4559ee32966",
        }

        test_activity_data = models.activity.Activity(
            org_uid="cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
            amount=10000,
            asset_id="0x438f0630bebb927cbef0663b6b4bfb1820a754975e25a8ef20fb10b6c616c4de",
            coin_id="0x40fd5fec70b2e7e3ab110a0ac22feb67f24fe989d7f2c7018c694faeea41c40f",
            height=1720476,
            mode="PERMISSIONLESS_RETIREMENT",
            sequence_num=0,
            timestamp=1666843885,
            vintage_year=2096,
            warehouse_project_id="c9b98579-debb-49f3-b417-0adbae4ed5c7",
            beneficiary_puzzle_hash="0xe122763ec4076d3fa356fbff8bb63d1f9d78b52c3c577a01140cd4559ee32966",
            beneficiary_address="bls12381uy38v0kyqaknlg6kl0lchd3ar7wh3dfv83th5qg5pn29t8hr99nq2vsjek",
            beneficiary_name="",
            metadata_={
                "bn": "",
                "ba": "bls12381uy38v0kyqaknlg6kl0lchd3ar7wh3dfv83th5qg5pn29t8hr99nq2vsjek",
                "bp": "0xe122763ec4076d3fa356fbff8bb63d1f9d78b52c3c577a01140cd4559ee32966",
            },
        )

        test_token_on_chain_dict = {
            "org_uid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
            "warehouse_project_id": "c9b98579-debb-49f3-b417-0adbae4ed5c7",
            "vintage_year": 2096,
            "sequence_num": 0,
            "index": "0x37f12cf05c5d5b254ac8019fc3b02a07f98526d57b65920a785980ad925273b7",
            "public_key": "0x9650dc15356ba1fe3a48e50daa55ac3dfde5323226922c9bf09aae1bd9612105f323e573cfa0778c681467a0c62bc315",  # noqa: E501
            "asset_id": "0x438f0630bebb927cbef0663b6b4bfb1820a754975e25a8ef20fb10b6c616c4de",
            "tokenization": {
                "mod_hash": "0x09bbb0ef739bdc4d37f0d0cec9c04453c40c264de8da8b2ce1edc3c1049406ce",
                "public_key": "0x8cba9cb11eed6e2a04843d94c9cabecc3f8eb3118f3a4c1dd5260684f462a8c886db5963f2dcac03f54a745a42777e7c",  # noqa: E501
            },
            "detokenization": {
                "mod_hash": "0x7d7fabdcf5c6cd7cae533490dfd5f98da622657cc760cb5d96891aa2a04323c9",
                "public_key": "0xb431835fe9fa64e9bea1bbab1d4bffd15d17d997f3754b2f97c8db43ea173a8b9fa79ac3a7d58c80111fbfdd4e485f0d",  # noqa: E501
                "signature": "0x842c093f865e2634099d321c4c9f5d540fb511012a9111929bec13c7e395cc6d9c3e68fc111763f13e9df50405e6eb2710bb553d7fa04097793bc327991d5d61584c4a10cdca304be5174d3778692ff2543f3bcc3a2c23db47704e6fc7399cc4",  # noqa: E501
            },
            "permissionless_retirement": {
                "mod_hash": "0xb19c88b1b53f2db24bfb9385ddb5854327baf08bd0d50c0e1b33ccd3a4c5dbb0",
                "signature": "0xacadbbdeffddbb8a7d43355c719c814ca18a731846cb7e67157dd1b6af7d269d264224a70b19197561c53f2a916742eb0ed21972af0bb77c74751d988733737da3b2f590a97f45f4a0beb81263936628c323d610cafc12528ea3ca0068037738",  # noqa: E501
            },
        }

        test_response = schemas.activity.ActivitiesResponse(
            activities=[
                schemas.activity.ActivityWithCW(
                    metadata={
                        "bn": "",
                        "ba": "bls12381uy38v0kyqaknlg6kl0lchd3ar7wh3dfv83th5qg5pn29t8hr99nq2vsjek",
                        "bp": "0xe122763ec4076d3fa356fbff8bb63d1f9d78b52c3c577a01140cd4559ee32966",
                    },
                    **jsonable_encoder(test_activity_data),
                    cw_org={"orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd"},
                    cw_project={
                        "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                        "warehouseProjectId": "c9b98579-debb-49f3-b417-0adbae4ed5c7",
                    },
                    cw_unit={
                        "warehouseUnitId": "944c7726-db49-4cb2-adb5-7e5cff9095e2",
                        "issuanceId": "fc467985-93e9-4a63-9f00-69cdf5c86dd3",
                        "projectLocationId": None,
                        "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                        "unitOwner": None,
                        "countryJurisdictionOfOwner": "Algeria",
                        "inCountryJurisdictionOfOwner": None,
                        "serialNumberBlock": "ABC100-ABC200",
                        "unitBlockStart": "ABC100",
                        "unitBlockEnd": "ABC200",
                        "unitCount": 100,
                        "vintageYear": 2096,
                        "unitType": "Reduction - nature",
                        "marketplace": None,
                        "marketplaceLink": None,
                        "marketplaceIdentifier": "0x438f0630bebb927cbef0663b6b4bfb1820a754975e25a8ef20fb10b6c616c4de",
                        "unitTags": None,
                        "unitStatus": "Held",
                        "unitStatusReason": None,
                        "unitRegistryLink": "http://example.example",
                        "correspondingAdjustmentDeclaration": "Committed",
                        "correspondingAdjustmentStatus": "Not Started",
                        "timeStaged": "1666589844",
                        "createdAt": "2022-10-24T06:25:13.437Z",
                        "updatedAt": "2022-10-24T06:25:13.437Z",
                        "labels": [],
                        "issuance": {
                            "id": "fc467985-93e9-4a63-9f00-69cdf5c86dd3",
                            "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                            "warehouseProjectId": "c9b98579-debb-49f3-b417-0adbae4ed5c7",
                            "startDate": "2022-08-03T00:00:00.000Z",
                            "endDate": "2022-08-05T00:00:00.000Z",
                            "verificationApproach": "seer",
                            "verificationReportDate": "2022-08-06T00:00:00.000Z",
                            "verificationBody": "tea",
                            "timeStaged": None,
                            "createdAt": "2022-10-24T06:25:13.440Z",
                            "updatedAt": "2022-10-24T06:25:13.440Z",
                        },
                    },
                    token=schemas.TokenOnChain.parse_obj(test_token_on_chain_dict),
                )
            ],
            total=1,
        )

        mock_db_data = mock.MagicMock()
        mock_climate_warehouse_data = mock.MagicMock()
        mock_db_data.return_value = (
            [
                test_activity_data,
            ],
            1,
        )
        mock_climate_warehouse_data.return_value = [
            {
                "warehouseUnitId": "944c7726-db49-4cb2-adb5-7e5cff9095e2",
                "issuanceId": "fc467985-93e9-4a63-9f00-69cdf5c86dd3",
                "projectLocationId": None,
                "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                "unitOwner": None,
                "countryJurisdictionOfOwner": "Algeria",
                "inCountryJurisdictionOfOwner": None,
                "serialNumberBlock": "ABC100-ABC200",
                "unitBlockStart": "ABC100",
                "unitBlockEnd": "ABC200",
                "unitCount": 100,
                "vintageYear": 2096,
                "unitType": "Reduction - nature",
                "marketplace": None,
                "marketplaceLink": None,
                "marketplaceIdentifier": "0x438f0630bebb927cbef0663b6b4bfb1820a754975e25a8ef20fb10b6c616c4de",
                "unitTags": None,
                "unitStatus": "Held",
                "unitStatusReason": None,
                "unitRegistryLink": "http://example.example",
                "correspondingAdjustmentDeclaration": "Committed",
                "correspondingAdjustmentStatus": "Not Started",
                "timeStaged": "1666589844",
                "createdAt": "2022-10-24T06:25:13.437Z",
                "updatedAt": "2022-10-24T06:25:13.437Z",
                "labels": [],
                "issuance": {
                    "id": "fc467985-93e9-4a63-9f00-69cdf5c86dd3",
                    "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                    "warehouseProjectId": "c9b98579-debb-49f3-b417-0adbae4ed5c7",
                    "startDate": "2022-08-03T00:00:00.000Z",
                    "endDate": "2022-08-05T00:00:00.000Z",
                    "verificationApproach": "seer",
                    "verificationReportDate": "2022-08-06T00:00:00.000Z",
                    "verificationBody": "tea",
                    "timeStaged": None,
                    "createdAt": "2022-10-24T06:25:13.440Z",
                    "updatedAt": "2022-10-24T06:25:13.440Z",
                },
                "organization": {"orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd"},
                "token": {
                    "org_uid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                    "warehouse_project_id": "c9b98579-debb-49f3-b417-0adbae4ed5c7",
                    "vintage_year": 2096,
                    "sequence_num": 0,
                    "index": "0x37f12cf05c5d5b254ac8019fc3b02a07f98526d57b65920a785980ad925273b7",
                    "public_key": "0x9650dc15356ba1fe3a48e50daa55ac3dfde5323226922c9bf09aae1bd9612105f323e573cfa0778c681467a0c62bc315",  # noqa: E501
                    "asset_id": "0x438f0630bebb927cbef0663b6b4bfb1820a754975e25a8ef20fb10b6c616c4de",
                    "tokenization": {
                        "mod_hash": "0x09bbb0ef739bdc4d37f0d0cec9c04453c40c264de8da8b2ce1edc3c1049406ce",
                        "public_key": "0x8cba9cb11eed6e2a04843d94c9cabecc3f8eb3118f3a4c1dd5260684f462a8c886db5963f2dcac03f54a745a42777e7c",  # noqa: E501
                    },
                    "detokenization": {
                        "mod_hash": "0x7d7fabdcf5c6cd7cae533490dfd5f98da622657cc760cb5d96891aa2a04323c9",
                        "public_key": "0xb431835fe9fa64e9bea1bbab1d4bffd15d17d997f3754b2f97c8db43ea173a8b9fa79ac3a7d58c80111fbfdd4e485f0d",  # noqa: E501
                        "signature": "0x842c093f865e2634099d321c4c9f5d540fb511012a9111929bec13c7e395cc6d9c3e68fc111763f13e9df50405e6eb2710bb553d7fa04097793bc327991d5d61584c4a10cdca304be5174d3778692ff2543f3bcc3a2c23db47704e6fc7399cc4",  # noqa: E501
                    },
                    "permissionless_retirement": {
                        "mod_hash": "0xb19c88b1b53f2db24bfb9385ddb5854327baf08bd0d50c0e1b33ccd3a4c5dbb0",
                        "signature": "0xacadbbdeffddbb8a7d43355c719c814ca18a731846cb7e67157dd1b6af7d269d264224a70b19197561c53f2a916742eb0ed21972af0bb77c74751d988733737da3b2f590a97f45f4a0beb81263936628c323d610cafc12528ea3ca0068037738",  # noqa: E501
                    },
                },
                "project": {
                    "warehouseProjectId": "c9b98579-debb-49f3-b417-0adbae4ed5c7",
                    "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                },
            }
        ]

        with anyio.from_thread.start_blocking_portal() as portal, monkeypatch.context() as m:
            fastapi_client.portal = portal  # workaround anyio 4.0.0 incompat with TextClient
            m.setattr(crud.BlockChainCrud, "get_challenge", mock_get_challenge)
            m.setattr(crud.DBCrud, "select_activity_with_pagination", mock_db_data)
            m.setattr(
                crud.ClimateWareHouseCrud,
                "combine_climate_units_and_metadata",
                mock_climate_warehouse_data,
            )

            params = urlencode(test_request)
            response = fastapi_client.get("v1/activities/", params=params)

        assert response.status_code == fastapi.status.HTTP_200_OK
        assert response.json() == jsonable_encoder(test_response)
        assert response.json()["total"] == test_response.total
