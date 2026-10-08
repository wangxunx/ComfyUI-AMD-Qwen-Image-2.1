from typing_extensions import override

from comfy_api.latest import IO, ComfyExtension

from .nodes import AMDQwenImage21TextToImage


class AMDQwenImage21Extension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[IO.ComfyNode]]:
        return [AMDQwenImage21TextToImage]


async def comfy_entrypoint() -> AMDQwenImage21Extension:
    return AMDQwenImage21Extension()
