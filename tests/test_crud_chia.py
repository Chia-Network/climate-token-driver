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
        test_response = [{
            "correspondingAdjustmentDeclaration": "Committed",
            "correspondingAdjustmentStatus": "Not Started",
            "countryJurisdictionOfOwner": "Algeria",
            "createdAt": "2022-10-24T06:25:13.440Z",
            "inCountryJurisdictionOfOwner": None,
            "issuance": {
                "createdAt": "2022-10-24T06:25:13.438Z",
                "endDate": "2022-08-05T00:00:00.000Z",
                "id": "18cfe2ba-faea-4f26-a69d-07ab6a6e886e",
                "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                "startDate": "2022-08-03T00:00:00.000Z",
                "timeStaged": None,
                "updatedAt": "2022-10-24T06:25:13.438Z",
                "verificationApproach": "seer",
                "verificationBody": "tea",
                "verificationReportDate": "2022-08-06T00:00:00.000Z",
                "warehouseProjectId": "c9b98579-debb-49f3-b417-0adbae4ed5c7"
            },
            "issuanceId": '18cfe2ba-faea-4f26-a69d-07ab6a6e886e',
            "labels": [],
            "marketplace": None,
            "marketplaceIdentifier": '8df0a9aa3739e24467b8a6409b49efe355dd4999a51215aed1f944314af07c60',
            "marketplaceLink": None,
            "orgUid": 'cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd',
            "organization": {
                "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                "name": "Hashgreen",
                "icon": "",
                "isHome": True,
                "subscribed": True,
                "fileStoreSubscribed": "0",
                "xchAddress": "txch1ejkmz95p0xngy5uf3mqjpy9ndlr6rxe324dwlhl2rdlyegmwqmeqrz9uvn",
                "balance": 106.489099999996
            },
            "projectLocationId": None,
            "serialNumberBlock": "ABC100-ABC200",
            "timeStaged": "1666592541",
            "token": {},
            "unitBlockEnd": "ABC200",
            "unitBlockStart": "ABC100",
            "unitCount": 100,
            "unitOwner": None,
            "unitRegistryLink": "http://example.example",
            "unitStatus": "Held",
            "unitStatusReason": None,
            "unitTags": None,
            "unitType": "Reduction - nature",
            "updatedAt": "2022-10-24T06:25:13.440Z",
            "vintageYear": 2099,
            "warehouseUnitId": "a9fbe47e-d308-4c4c-8eb5-c06dd09b0716",
            "project": {
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
        }]

        mock_units = mock.MagicMock()
        mock_projects = mock.MagicMock()
        mock_orgs = mock.MagicMock()
        mock_org_metadata = mock.MagicMock()
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
        mock_orgs.return_value = {
            "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd": {
                "orgUid": "cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd",
                "name": "Hashgreen",
                "icon": "",
                "isHome": True,
                "subscribed": True,
                "fileStoreSubscribed": "0",
                "xchAddress": "txch1ejkmz95p0xngy5uf3mqjpy9ndlr6rxe324dwlhl2rdlyegmwqmeqrz9uvn",
                "balance": 106.489099999996
            }
        }
        mock_org_metadata.return_value = {
            "0x8df0a9aa3739e24467b8a6409b49efe355dd4999a51215aed1f944314af07c60": "{\"org_uid\": \"cf7af8da584b6c115ba8247c5cdd05506c3b3c5c632ed975cc2b16262493e2bd\",\"warehouse_project_id\": \"c9b98579-debb-49f3-b417-0adbae4ed5c7\",        \"vintage_year\": 2099,\"sequence_num\": 0,\"index\": \"0x8b0aa9633464b5437f4b980b864a3ab5dda49e6a754ef2b1cde6d30fb28a9330\",\"public_key\": \"0x9650dc15356ba1fe3a48e50daa55ac3dfde5323226922c9bf09aae1bd9612105f323e573cfa0778c681467a0c62bc315\",        \"asset_id\": \"0x8df0a9aa3739e24467b8a6409b49efe355dd4999a51215aed1f944314af07c60\",\"tokenization\": {            \"mod_hash\": \"0xbe97af91e9833541c4c5dd0ab08bad1b0653cccd96e56ae43b7314469e458f5b\",\"public_key\": \"0x8cba9cb11eed6e2a04843d94c9cabecc3f8eb3118f3a4c1dd5260684f462a8c886db5963f2dcac03f54a745a42777e7c\"},        \"detokenization\": {\"mod_hash\": \"0xed13201cb8b52b4c7ef851e220a3d2bddd57120e6e6afde2aabe3fcc400765ea\",   \"public_key\": \"0xb431835fe9fa64e9bea1bbab1d4bffd15d17d997f3754b2f97c8db43ea173a8b9fa79ac3a7d58c80111fbfdd4e485f0d\",            \"signature\": \"0xa627c8779c2d8096444d44879294c7d963180c166564e9c9569c23c3a744af514aae03aeaa5e2d5fd12d0c008c1630410e9d4516b58863658f7ac5b35d09d8810fb28ed43b3f6243c645f0bd934b434aac87cd5718dafd87b51d8bf9c821ba24\"},\"permissionless_retirement\": {\"mod_hash\": \"0x36ab0a0666149598070b7c40ab10c3aaff51384d4ad4544a1c301636e917c039\",\"signature\": \"0xaa1f6b71999333761fbd9eb914ce5ab1c3acb83e7fa7eb5b59c226f20b644c835f8238edbe3ddfeed1a916f0307fe1200174a211b8169ace5afcd9162f88b46565f3ffbbf6dfdf8d154e6337e30829c23ab3f6796d9a319bf0d9168685541d62\"}}"
        }

        monkeypatch.setattr(crud.ClimateWareHouseCrud, "get_climate_projects", mock_projects)
        monkeypatch.setattr(crud.ClimateWareHouseCrud, "get_climate_units", mock_units)
        monkeypatch.setattr(crud.ClimateWareHouseCrud, "get_climate_organizations", mock_orgs)
        monkeypatch.setattr(crud.ClimateWareHouseCrud, "get_climate_organizations_metadata", mock_org_metadata)

        response = crud.ClimateWareHouseCrud(url=mock.MagicMock()).combine_climate_units_and_metadata(
            search=test_request)

        assert response == test_response

