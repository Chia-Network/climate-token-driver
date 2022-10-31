from unittest import mock
from app import crud


class TestClimateWareHouseCrud:
    def test_combine_climate_units_and_metadata_empty_units_then_success(self, monkeypatch):
        test_request = {}
        test_response = []

        mock_units = mock.MagicMock()
        mock_units.return_value = []

        monkeypatch.setattr(crud.ClimateWareHouseCrud, "get_climate_units", mock_units)

        response = crud.ClimateWareHouseCrud(url=mock.MagicMock()).combine_climate_units_and_metadata(
            search=test_request)

        assert response == test_response

    def test_combine_climate_units_and_metadata_empty_projects_then_success(self, monkeypatch):
        test_request = {}
        test_response = []

        mock_units = mock.MagicMock()
        mock_projects = mock.MagicMock()
        mock_units.return_value = [
            {
                "warehouseUnitId": "a9fbe47e-d308-4c4c-8eb5-c06dd09b0716",
                "issuanceId": "18cfe2ba-faea-4f26-a69d-07ab6a6e886e",
                "projectLocationId": None,
                "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                "unitOwner": None,
                "countryJurisdictionOfOwner": "Algeria",
                "inCountryJurisdictionOfOwner": None,
                "serialNumberBlock": "ABC100-ABC200",
                "unitBlockStart": "ABC100",
                "unitBlockEnd": "ABC200",
                "unitCount": 100,
                "vintageYear": 2099,
                "unitType": "Reduction - nature",
                "marketplace": None,
                "marketplaceLink": None,
                "marketplaceIdentifier": "8df0a9aa3739e24467b8a6409b49efe355dd4999a51215aed1f944314af07c60",
                "unitTags": None,
                "unitStatus": "Held",
                "unitStatusReason": None,
                "unitRegistryLink": "http://example.example",
                "correspondingAdjustmentDeclaration": "Committed",
                "correspondingAdjustmentStatus": "Not Started",
                "timeStaged": "1666592541",
                "createdAt": "2022-10-24T06:25:13.440Z",
                "updatedAt": "2022-10-24T06:25:13.440Z",
                "labels": [],
                "issuance": {
                    "id": "18cfe2ba-faea-4f26-a69d-07ab6a6e886e",
                    "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                    "warehouseProjectId": "c9b98579-debb-49f3-b417-0adbae4ed5c7",
                    "startDate": "2022-08-03T00:00:00.000Z",
                    "endDate": "2022-08-05T00:00:00.000Z",
                    "verificationApproach": "seer",
                    "verificationReportDate": "2022-08-06T00:00:00.000Z",
                    "verificationBody": "tea",
                    "timeStaged": None,
                    "createdAt": "2022-10-24T06:25:13.438Z",
                    "updatedAt": "2022-10-24T06:25:13.438Z",
                }
            }
        ]
        mock_projects.return_value = []

        monkeypatch.setattr(crud.ClimateWareHouseCrud, "get_climate_projects", mock_projects)
        monkeypatch.setattr(crud.ClimateWareHouseCrud, "get_climate_units", mock_units)

        response = crud.ClimateWareHouseCrud(url=mock.MagicMock()).combine_climate_units_and_metadata(
            search=test_request)

        assert response == test_response

    def test_combine_climate_units_and_metadata_empty_orgs_then_success(self, monkeypatch):
        test_request = {}
        test_response = []

        mock_units = mock.MagicMock()
        mock_projects = mock.MagicMock()
        mock_orgs = mock.MagicMock()
        mock_units.return_value = [
            {
                "warehouseUnitId": "a9fbe47e-d308-4c4c-8eb5-c06dd09b0716",
                "issuanceId": "18cfe2ba-faea-4f26-a69d-07ab6a6e886e",
                "projectLocationId": None,
                "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                "unitOwner": None,
                "countryJurisdictionOfOwner": "Algeria",
                "inCountryJurisdictionOfOwner": None,
                "serialNumberBlock": "ABC100-ABC200",
                "unitBlockStart": "ABC100",
                "unitBlockEnd": "ABC200",
                "unitCount": 100,
                "vintageYear": 2099,
                "unitType": "Reduction - nature",
                "marketplace": None,
                "marketplaceLink": None,
                "marketplaceIdentifier": "8df0a9aa3739e24467b8a6409b49efe355dd4999a51215aed1f944314af07c60",
                "unitTags": None,
                "unitStatus": "Held",
                "unitStatusReason": None,
                "unitRegistryLink": "http://example.example",
                "correspondingAdjustmentDeclaration": "Committed",
                "correspondingAdjustmentStatus": "Not Started",
                "timeStaged": "1666592541",
                "createdAt": "2022-10-24T06:25:13.440Z",
                "updatedAt": "2022-10-24T06:25:13.440Z",
                "labels": [],
                "issuance": {
                    "id": "18cfe2ba-faea-4f26-a69d-07ab6a6e886e",
                    "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                    "warehouseProjectId": "c9b98579-debb-49f3-b417-0adbae4ed5c7",
                    "startDate": "2022-08-03T00:00:00.000Z",
                    "endDate": "2022-08-05T00:00:00.000Z",
                    "verificationApproach": "seer",
                    "verificationReportDate": "2022-08-06T00:00:00.000Z",
                    "verificationBody": "tea",
                    "timeStaged": None,
                    "createdAt": "2022-10-24T06:25:13.438Z",
                    "updatedAt": "2022-10-24T06:25:13.438Z",
                }
            }
        ]
        mock_projects.return_value = [
            {
                "warehouseProjectId": "fce35ee2-bdf1-47d8-9397-345334ff804b",
                "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                "currentRegistry": None,
                "projectId": "c9d147e2-bc07-4e68-a76d-43424fa8cd4e",
                "originProjectId": "TEST PROJECT ID",
                "registryOfOrigin": "Singapore National Registry",
                "program": "TEST",
                "projectName": "Sungei Buloh Wetlands Conservation",
                "projectLink": "https://www.nature.com/articles/s41467-021-21560-2",
                "projectDeveloper": "NParks' National Biodiversity Centre, National Parks Board, Ridgeview Residential College",
                "sector": "Transport",
                "projectType": "Organic Waste Composting",
                "projectTags": None,
                "coveredByNDC": "Inside NDC",
                "ndcInformation": "The restoration and conservation project directly aligns to the Singaporean NDC goals to capture 1,000,000 tons of carbon by 2050. This project represents an estimated contribution of 27% towards the NDC.",
                "projectStatus": "Registered",
                "projectStatusDate": "2022-01-31T00:05:45.701Z",
                "unitMetric": "tCO2e",
                "methodology": "Recovery and utilization of gas from oil fields that would otherwise be flared or vented --- Version 7.0",
                "methodology2": None,
                "validationBody": "SCS Global Services",
                "validationDate": "2021-06-01T17:00:45.701Z",
                "timeStaged": "1666138010",
                "description": None,
                "createdAt": "2022-10-24T05:56:12.935Z",
                "updatedAt": "2022-10-24T05:56:12.935Z",
                "projectLocations": [],
                "labels": [],
                "issuances": [],
                "coBenefits": [],
                "relatedProjects": [],
                "projectRatings": [],
                "estimations": [],
            }
        ]
        mock_orgs.return_value = []

        monkeypatch.setattr(crud.ClimateWareHouseCrud, "get_climate_projects", mock_projects)
        monkeypatch.setattr(crud.ClimateWareHouseCrud, "get_climate_units", mock_units)
        monkeypatch.setattr(crud.ClimateWareHouseCrud, "get_climate_organizations", mock_orgs)

        response = crud.ClimateWareHouseCrud(url=mock.MagicMock()).combine_climate_units_and_metadata(
            search=test_request)

        assert response == test_response

