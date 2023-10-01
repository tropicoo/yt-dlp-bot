from typing import Type

from ytdl_opts.per_host._base import AbstractHostConfig


class HostConfRegistry(type):
    REGISTRY: dict[str, type[AbstractHostConfig]] = {}
    HOST_TO_CLS_MAP = {}

    def __new__(
        mcs: Type['HostConfRegistry'],
        name: str,
        bases: tuple[type[AbstractHostConfig]],
        attrs: dict,
    ) -> type[AbstractHostConfig]:
        host_cls: type[AbstractHostConfig] = type.__new__(mcs, name, bases, attrs)
        mcs.REGISTRY[host_cls.__name__] = host_cls

        mcs._build_host_to_cls_map(host_cls=host_cls, hostnames=attrs['HOSTNAMES'])
        return host_cls

    @classmethod
    def get_registry(mcs) -> dict[str, type[AbstractHostConfig]]:
        return mcs.REGISTRY.copy()

    @classmethod
    def get_host_to_cls_map(mcs) -> dict[str | None, type[AbstractHostConfig]]:
        return mcs.HOST_TO_CLS_MAP.copy()

    @classmethod
    def _build_host_to_cls_map(
        mcs, host_cls: type[AbstractHostConfig], hostnames: tuple[str, ...] | None
    ) -> None:
        if hostnames is None:
            mcs.HOST_TO_CLS_MAP[None] = host_cls
        else:
            for host in hostnames:
                mcs.HOST_TO_CLS_MAP[host] = host_cls
