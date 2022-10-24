from blspy import PrivateKey
from chia.wallet.derive_keys import _derive_path_unhardened

from app.core.types import CLIMATE_WALLET_INDEX, GatewayMode


def master_sk_to_root_sk(master: PrivateKey) -> PrivateKey:
    return _derive_path_unhardened(master, [12381, 8444, CLIMATE_WALLET_INDEX])


def root_sk_to_gateway_sk(root: PrivateKey, mode: GatewayMode) -> PrivateKey:
    return _derive_path_unhardened(root, [mode.to_int()])
