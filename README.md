# ComfyUI-AMD-Qwen-Image-2.1

ComfyUI node for Qwen-Image 2.1 image generation and image editing through the AMD gateway. Both
`Qwen-Image-2.1` and `Qwen-Image-2.1-Turbo` are supported, and the node's `model` input picks
between them.

## Install

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/wangxunx/ComfyUI-AMD-Qwen-Image-2.1.git
```

Restart ComfyUI. No extra Python dependencies are required.

## Configure your API key

Register at https://h3.oneclickamd.ai to get a key, then use either method below. This is a one-time setup per machine and applies to every workflow:

- Set the `H3_GATEWAY_API_KEY` environment variable
- Or save the key to `h3_gateway_api_key.txt` in the ComfyUI user directory

If the key is missing, the node fails immediately and tells you the registration URL and the exact file path.

The gateway serves both its image and video models from one account, so a key already configured for [ComfyUI-AMD-MiniMaxH3](https://github.com/wangxunx/ComfyUI-AMD-MiniMaxH3) works here with no further setup.

To point the node at a different gateway, set `H3_GATEWAY_BASE_URL`.

## Node

| Node | Inputs |
|---|---|
| AMD Qwen Image 2.1 | `prompt`, `aspect_ratio` (six ratios), `model`, `steps` (10-50, base model only), `images` (0-3 reference images) |

One node covers both tasks. Connect nothing to `images` and it generates from the prompt alone;
connect one to three reference images and the same node edits them. A prompt is always required —
with reference images it describes the edit.

`aspect_ratio` applies to edits too: the output is reframed to it rather than keeping the shape of
the reference images. Extra `image_N` sockets appear as you fill the existing ones, up to three.

## Models

One node serves both models; pick one with the `model` input.

| Model | 1024x1024 | Steps |
|---|---|---|
| `Qwen-Image-2.1` | about 23 seconds | `steps` slider, 10-50 |
| `Qwen-Image-2.1-Turbo` | about 13 seconds | fixed by the gateway |

Both cost the same, and both do text-to-image and editing. Turbo runs at a step count the gateway pins, so the `steps` slider only appears for the base model.

On the base model, credits are charged in proportion to `steps`: 30 steps cost one credit, and more steps cost proportionally more.

The first request at a resolution the backend has not served before takes noticeably longer because it compiles convolution kernels on the spot; that path is slow, not failing.

## Upgrading from 1.0.0

The `model` input took the widget slot `steps` used to occupy, so a workflow saved with 1.0.0 loads its old step count into `model` and will not run. Open the node, pick a model again, and re-save. 2.0.0 also needs ComfyUI 0.4.0 or newer, which is when the dynamic input it uses was added.

The node is listed as `AMD Qwen Image 2.1` rather than `AMD Qwen Image 2.1 Text to Image`, since it no longer only does text to image.

## Example workflows

In ComfyUI, open the template browser from the left sidebar, scroll to the **EXTENSIONS** section, and pick `ComfyUI-AMD-Qwen-Image-2.1`. Both workflows run as-is once your key is configured, and each includes a note explaining the key setup.

| Workflow | What it does |
|---|---|
| `AMD Qwen Image 2.1 Text to Image` | Generates from a prompt |
| `AMD Qwen Image 2.1 Image Edit` | Edits the bundled `example.png` from a prompt |

## Your API key never enters a workflow

The node deliberately has no `api_key` widget. Widget values are serialized into workflow JSON and embedded into output image metadata, which would leak the key as soon as a workflow or a generated image is shared. Reading the key from the environment or from a file outside the graph keeps it out of both.

## License

MIT. See [LICENSE](LICENSE).
