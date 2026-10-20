"""Image generation node for Qwen-Image 2.1 on the AMD gateway.

The gateway issues one API key per registered user, so the key must never become part of a
workflow: widget values are serialized into workflow JSON and embedded into output file metadata,
which would leak every user's key as soon as they share a workflow or a generated image. The key
and the gateway URL are therefore read from the environment or from a file in the ComfyUI user
directory, leaving only the creative parameters in the graph.
"""

import os

import folder_paths
from comfy_api.latest import IO
from comfy_api_nodes.util import (
    ApiEndpoint,
    download_url_to_image_tensor,
    poll_op,
    sync_op,
    validate_string,
)
from pydantic import BaseModel

DEFAULT_BASE_URL = "https://h3.oneclickamd.ai"
BASE_URL_ENV_VAR = "H3_GATEWAY_BASE_URL"
API_KEY_ENV_VAR = "H3_GATEWAY_API_KEY"
API_KEY_FILENAME = "h3_gateway_api_key.txt"
REGISTRATION_URL = "https://h3.oneclickamd.ai"
BASE_MODEL = "Qwen-Image-2.1"
TURBO_MODEL = "Qwen-Image-2.1-Turbo"
FAILED_STATUSES = ["failed", "cancelled"]


class TextContent(BaseModel):
    type: str = "text"
    text: str


class TaskCreationRequest(BaseModel):
    model: str
    content: list[TextContent]
    aspect_ratio: str
    steps: int | None = None


class TaskCreationResponse(BaseModel):
    task_id: str


class TaskContent(BaseModel):
    url: str | None = None


class Task(BaseModel):
    status: str
    content: TaskContent | None = None


class TaskQueryResponse(BaseModel):
    task: Task


def api_key_file() -> str:
    return os.path.join(folder_paths.get_user_directory(), API_KEY_FILENAME)


def resolve_api_key() -> str:
    key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if not key and os.path.isfile(api_key_file()):
        with open(api_key_file(), encoding="utf-8") as f:
            key = f.read().strip()
    if not key:
        raise Exception(
            f"No API key configured. Register at {REGISTRATION_URL} to get one, then either set the "
            f"{API_KEY_ENV_VAR} environment variable or save the key to {api_key_file()}."
        )
    return key


def resolve_base_url() -> str:
    return os.environ.get(BASE_URL_ENV_VAR, DEFAULT_BASE_URL).rstrip("/")


class AMDQwenImage21TextToImage(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="AMDQwenImage21TextToImage",
            display_name="AMD Qwen Image 2.1 Text to Image",
            category="image/Qwen",
            description="Generate an image from a text prompt with Qwen-Image 2.1 on the AMD gateway. "
            f"Requires an account: register at {REGISTRATION_URL}, then set the {API_KEY_ENV_VAR} "
            f"environment variable or save your key to {API_KEY_FILENAME} in the ComfyUI user directory.",
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Text prompt for image generation.",
                ),
                IO.Combo.Input(
                    "aspect_ratio",
                    options=["1:1", "16:9", "9:16", "4:3", "3:4", "21:9"],
                    default="1:1",
                    tooltip="Aspect ratio of the output image.",
                ),
                IO.DynamicCombo.Input(
                    "model",
                    options=[
                        IO.DynamicCombo.Option(
                            BASE_MODEL,
                            [
                                IO.Int.Input(
                                    "steps",
                                    default=30,
                                    min=10,
                                    max=50,
                                    step=1,
                                    display_mode=IO.NumberDisplay.slider,
                                    tooltip="Denoising steps (10-50). Credits are charged in proportion to steps, "
                                    "with 30 steps costing one credit.",
                                )
                            ],
                        ),
                        IO.DynamicCombo.Option(TURBO_MODEL, []),
                    ],
                    tooltip="Turbo is about twice as fast for the same price, at a step count fixed by the gateway.",
                ),
            ],
            outputs=[IO.Image.Output()],
            hidden=[IO.Hidden.unique_id],
        )

    @classmethod
    async def execute(cls, prompt: str, aspect_ratio: str, model: dict) -> IO.NodeOutput:
        validate_string(prompt, min_length=1)
        root = resolve_base_url()
        headers = {"Authorization": f"Bearer {resolve_api_key()}"}
        # Images go through the video paths: the gateway is wire-compatible with the MiniMax API,
        # where "video" in the path is fixed. The model field decides what comes back.
        response = await sync_op(
            cls,
            ApiEndpoint(path=f"{root}/v2/video_generation", method="POST", headers=headers),
            response_model=TaskCreationResponse,
            data=TaskCreationRequest(
                model=model["model"],
                content=[TextContent(text=prompt)],
                aspect_ratio=aspect_ratio,
                # Turbo runs at a step count the gateway pins, so the field is left out entirely.
                steps=model.get("steps"),
            ),
        )
        task_result = await poll_op(
            cls,
            ApiEndpoint(path=f"{root}/v2/query/video_generation/{response.task_id}", headers=headers),
            response_model=TaskQueryResponse,
            status_extractor=lambda r: r.task.status,
            failed_statuses=FAILED_STATUSES,
            poll_interval=2,
        )
        image_url = task_result.task.content.url if task_result.task.content else None
        if not image_url:
            raise Exception(f"No image URL in the response: {task_result.model_dump()}")
        return IO.NodeOutput(await download_url_to_image_tensor(image_url))
