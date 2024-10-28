from __future__ import annotations

import dataclasses
import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urlparse

import requests
from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.types.blockchain_format.coin import Coin
from chia.types.coin_record import CoinRecord
from chia_rs import G1Element
from fastapi.encoders import jsonable_encoder

from app import schemas
from app.config import settings
from app.core.climate_wallet.wallet import ClimateObserverWallet
from app.core.types import ClimateTokenIndex, GatewayMode
from app.errors import ErrorCode
from app.logger import logger

error_code = ErrorCode()


@dataclasses.dataclass
class ClimateWareHouseCrud(object):
    url: str
    api_key: Optional[str]

    def _headers(self) -> Dict[str, str]:
        headers = {}

        if self.api_key is not None:
            headers["x-api-key"] = self.api_key

        return headers

    def _get_paginated_data(self, path: str, search_params: Dict[str, Any]) -> List[Any]:
        """
        Generic function to retrieve paginated data from a given path.

        Args:
            path: API endpoint path.
            search_params: A dictionary of search parameters including pagination.

        Returns:
            A list of all data retrieved from the paginated API.
        """
        all_data: list[dict[str, Any]] = []
        page = 1
        limit = 10

        try:
            while True:
                # Update search parameters with current page and limit
                params = {**search_params, "page": page, "limit": limit}
                encoded_params = urlencode(params)

                # Construct the URL
                url_obj = urlparse(f"{self.url}{path}?{encoded_params}")
                url = url_obj.geturl()

                response = requests.get(url, headers=self._headers())
                if response.status_code != requests.codes.ok:
                    logger.error(f"Request Url: {response.url} Error Message: {response.text}")
                    raise error_code.internal_server_error(message="API Call Failure")

                data = response.json()
                if data is None:
                    # some cadt endpoints return null with no pagination info if no data is found
                    # to prevent an infinite loop need to assume that there is no data matching
                    # the search from this iteration on
                    return all_data

                try:
                    if (
                        data["page"] and (data["pageCount"] >= 0) and len(data["data"]) >= 0
                    ):  # page count can be 0 (as of when this was written)
                        all_data.extend(data["data"])  # Add data from the current page
                    else:
                        all_data.append(data)  # data was not paginated, append and return
                        return all_data
                except Exception:
                    all_data.append(data)  # data was not paginated, append and return
                    return all_data

                if page >= data["pageCount"]:
                    break  # Exit loop if all pages have been processed

                page += 1

            return all_data

        except TimeoutError as e:
            logger.error("API Call Timeout, ErrorMessage: " + str(e))
            raise error_code.internal_server_error("API Call Timeout")

    def get_climate_units(self, search: Dict[str, Any]) -> Any:
        """
        Retrieves all climate units using pagination and given search parameters.

        Args:
            search: A dictionary of search parameters.

        Returns:
            A JSON object containing all the climate units.
        """
        search_with_marketplace = {**search, "hasMarketplaceIdentifier": True}
        return self._get_paginated_data("/v1/units", search_with_marketplace)

    def get_climate_projects(self) -> Any:
        """
        Retrieves all climate projects using pagination.

        Returns:
            A JSON object containing all the climate projects.
        """
        search_params = {"onlyMarketplaceProjects": True}
        return self._get_paginated_data("/v1/projects", search_params)

    def get_climate_organizations(self) -> Any:
        try:
            url = urlparse(self.url + "/v1/organizations")

            r = requests.get(url.geturl(), headers=self._headers())
            if r.status_code != requests.codes.ok:
                logger.error(f"Request Url: {r.url} Error Message: {r.text}")
                raise error_code.internal_server_error(message="Call Climate API Failure")

            return r.json()

        except TimeoutError as e:
            logger.error("Call Climate API Timeout, ErrorMessage: " + str(e))
            raise error_code.internal_server_error("Call Climate API Timeout")

    def get_climate_organizations_metadata(self, org_uid: str) -> Any:
        try:
            condition = {"orgUid": org_uid}

            params = urlencode(condition)
            url = urlparse(self.url + "/v1/organizations/metadata")

            r = requests.get(url.geturl(), params=params, headers=self._headers())
            if r.status_code != requests.codes.ok:
                logger.error(f"Request Url: {r.url} Error Message: {r.text}")
                raise error_code.internal_server_error(message="Call Climate API Failure")

            return r.json()

        except TimeoutError as e:
            logger.error("Call Climate API Timeout, ErrorMessage: " + str(e))
            raise error_code.internal_server_error("Call Climate API Timeout")

    def combine_climate_units_and_metadata(self, search: Dict[str, Any]) -> List[Dict[str, Any]]:
        # units: [unit]
        units = self.get_climate_units(search)
        if len(units) == 0:
            logger.warning(f"Search climate warehouse units by search is empty. search:{search}")
            return []

        projects = self.get_climate_projects()
        if len(projects) == 0:
            return []

        # organization_by_id: {org_uid -> org}
        organization_by_id = self.get_climate_organizations()
        if len(organization_by_id) == 0:
            return []

        # metadata_by_id: {org_uid -> {meta_key -> meta_value}}
        metadata_by_id: Dict[str, Dict[Any, Any]] = {}
        for org_uid in organization_by_id.keys():
            metadata_by_id[org_uid] = self.get_climate_organizations_metadata(org_uid)

        project_by_id = {project["warehouseProjectId"]: project for project in projects}

        onchain_units = []
        for unit in units:
            marketplace_id = unit["marketplaceIdentifier"]

            if not marketplace_id:
                continue

            unit_org_uid = unit.get("orgUid")
            if unit_org_uid is None:
                logger.warning(f"Can not get climate warehouse orgUid in unit. unit:{unit}")
                continue

            org = organization_by_id.get(unit_org_uid)
            if org is None:
                logger.warning(f"Can not get organization by org_uid. org_uid:{unit_org_uid}")
                continue

            try:
                warehouse_project_id = unit["issuance"]["warehouseProjectId"]
                project = project_by_id[warehouse_project_id]
            except (KeyError, TypeError):
                logger.warning("Can not get project by warehouse_project_id")
                continue

            org_metadata = metadata_by_id.get(unit_org_uid)
            if org_metadata is None:
                continue

            metadata = dict()
            # some versions perpended "meta_" to the key, so check both ways
            if marketplace_id in org_metadata:
                metadata = json.loads(org_metadata.get(marketplace_id, "{}"))
            elif f"meta_{marketplace_id}" in org_metadata:
                metadata = json.loads(org_metadata.get(f"meta_{marketplace_id}", "{}"))

            unit["organization"] = org
            unit["token"] = metadata
            unit["project"] = project

            onchain_units.append(unit)

        return onchain_units


@dataclasses.dataclass
class BlockChainCrud(object):
    full_node_client: FullNodeRpcClient

    async def get_challenge(self) -> str:
        result = await self.full_node_client.fetch("get_network_info", {})
        return str(result["network_name"])

    async def get_activities(
        self,
        org_uid: str,
        warehouse_project_id: str,
        vintage_year: int,
        sequence_num: int,
        public_key: G1Element,
        start_height: int,
        end_height: int,
        peak_height: int,
        mode: Optional[GatewayMode] = None,
    ) -> List[schemas.Activity]:
        token_index = ClimateTokenIndex(
            org_uid=org_uid,
            warehouse_project_id=warehouse_project_id,
            vintage_year=vintage_year,
            sequence_num=sequence_num,
        )
        wallet = ClimateObserverWallet(
            token_index=token_index,
            root_public_key=public_key,
            full_node_client=self.full_node_client,
        )
        activity_objs = await wallet.get_activities(
            mode=mode,
            start_height=start_height,
            end_height=end_height,
        )

        activities: List[schemas.Activity] = []
        for obj in activity_objs:
            coin_record: CoinRecord = obj["coin_record"]
            metadata = jsonable_encoder(obj["metadata"])
            coin: Coin = coin_record.coin
            obj_mode = obj["mode"]

            if peak_height - coin_record.spent_block_index + 1 < settings.MIN_DEPTH:
                continue

            activity = schemas.Activity(
                org_uid=token_index.org_uid,
                warehouse_project_id=token_index.warehouse_project_id,
                vintage_year=token_index.vintage_year,
                sequence_num=token_index.sequence_num,
                asset_id=bytes(wallet.tail_program_hash),
                beneficiary_address=metadata.get("ba"),
                beneficiary_name=metadata.get("bn"),
                beneficiary_puzzle_hash=metadata.get("bp"),
                coin_id=coin_record.name,
                height=coin_record.spent_block_index,
                amount=coin.amount,
                mode=obj_mode,
                metadata=metadata,
                timestamp=coin_record.timestamp,
            )
            activities.append(activity)

            logger.info(f"Found activity {jsonable_encoder(activity)}")

        return activities
