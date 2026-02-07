# screen2edit

Script that takes a screenshot of any active window using a hotkey and sends it to comfyUI+klein-9b API. Displays an image in the next window.

It works very fast - 7 seconds (checkpoint klein-9b-int8) with 3090

## Examples of prompts:
1. Improve graphics in visual novels or other turn-based games: `Turn this into a photo, soft dim lighting. Add film grain, bokeh, shallow depth of field, retro photo, soft focus, low contrast. Add blur, motion blur. face swap woman with Emm4w woman, dark brown lose hair.`
2. Colorize manga in the browser: `Colorize manga. Woman has a light pink jacket with white shirt and with a red ribbon, white high socks and dark brown hair. Man has grey jacket and short black hair`
3. Character replacement: `face swap woman with Emm4w woman, lose brown hair` (need laura or a second attached face picture)
4. Changing clothes: `now she is wearing a bikini`
5. Anime photo: `change style to Ghibli studio style`


## Installing screen2edit

```cmd in any folder
git clone https://github.com/Mozer/screen2edit
cd screen2edit
pip install -r requirements.txt
```

inside screen2edit.py edit your paths to comfyui
```
Configuration
SAVE_PATH = r'C:\DATA\SD\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\ComfyUI\input\screenshot.jpg'
PROMPT_URL = 'http://127.0.0.1:8188/prompt'
HISTORY_URL = 'http://127.0.0.1:8188/history?max_items=64'
VIEW_URL_BASE = 'http://127.0.0.1:8188/view'

CROP_TOP = 50       #REMOVE PX FROM TOP
CROP_BOTTOM = 10    #REMOVE PX FROM BOTTOM
CROP_LEFT = 10      #REMOVE PX FROM LEFT
CROP_RIGHT = 10     #REMOVE PX FROM RIGHT
```

- import workflow/workflow.json in comfy (it's for fp8). Or workflow_klein_9b_int8.json
- check the functionality
- comfyUI - File - Export (API) - put workflow/workflow.json in the same place

## Launching screen2edit
- double click on screen2edit.py
- open the desired window with the game or browser, press Alt+x to make a screenshot and send it to comfy (I have not tested full-screen mode with complex 3D games on unity or directx. xs, whether it will take screenshots. There shouldn't be any problems with games in windowed mode)
- the window with the finished picture will appear by itself after some time.

Notes:
- if the small text is hard to read, remove the lore, increase the screenshot crop on top and sides. Increasing the resolution of the output image helps, but not always. Optimal 1.1 - 1.2 Mpx.


## Klein inference speed-up (INT8 checkpoint, optional)
To speed up inference of the klein-9b, I recommend using the int8 version. On the 3000 series, it is 2 times faster than FP8 and 3-4 times faster than gguf. There is also an speed-up on the 4000 series, but not so much (4000 is already fast with fp8).

1024x1024, 4 steps, at 3090:
text2image int8 - 3.31 seconds
image2image int8 - 6.41 seconds
image2image fp8 - 12.84 seconds

The increase is achieved through the use of int8 cuda cores. Applicable for 3000 series and later. On the 4000 series, there is also an increase relative to fp8, but not so much.

Optionally, you need: triton-windows (it will be a little faster, but int8 will speed-up even without it. My model compile node didn't work, maybe I need a newer torch/cuda. I have torch2.6.0+cu126)
You need a comfy kitchen:
`C:\DATA\SD\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\python_embeded>python.exe -m pip install comfy-kitchen`

Install node via Manager - install via git url 
https://github.com/BobJohnson24/ComfyUI-Flux2-INT8

int8 model (put inside diffusion_models): https://huggingface.co/bertbobson/FLUX.2-klein-9B-INT8-Comfy/blob/main/flux-2-klein-schnell-9b-INT8V2.safetensors

To load the INT8 model, you need the node 'Load Diffusion Model INT8 (W8A8)', it is inside Flux2-INT8 nodes. There may be some problems with some loras. There are no problems with my loras from onetrainer.