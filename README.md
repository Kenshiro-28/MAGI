# MAGI

MAGI (マギ) is an advanced AI system powered by open-source large language models. It operates through a conversational interface and is designed to run efficiently on consumer-grade hardware. It also features a plugin system that enables Internet browsing, remote operation through Telegram and image generation.

## Configuration

You can customize MAGI by editing the file **config.cfg**.

The main options are:

CONTEXT_SIZE: number of tokens in the context window (default: 32768)

ENABLE_WEB_PLUGIN: enable or disable the web plugin (default: YES)

ENABLE_TELEGRAM_PLUGIN: enable or disable the Telegram plugin (default: NO)

ENABLE_IMAGE_GENERATION_PLUGIN: enable or disable the image generation plugin (default: NO)

DISPLAY_EXTENDED_REASONING: display the extended reasoning between `<think>...</think>` tags (default: NO)

ENABLE_LOG: enable or disable logging to the file **mission_log.txt** (default: NO)

## Prime Directives

You can set MAGI to behave like a fictional character or follow a set of rules. You just have to describe what you want and MAGI will follow your instructions.

You can set your Prime Directives in the file **prime_directives.txt**. 

## AI modes

To toggle between the different AI modes, type the letter **m** and press enter.

### Normal mode

MAGI will hold a conversation with you in a similar way to other chatbots.

This is the default mode when the program starts.

### Mission mode

MAGI will generate a more elaborate response based on an action list.

The system will extract useful information from the file **mission_data.txt**.

### NERV mode

NERV is a virtual organization composed of AI agents.

The agents are organized following a military structure. The Captain receives the user's prompt, analyzes it, and issues orders to each Soldier.

The Captain will evaluate each Soldier's response and will provide additional guidance when necessary.

Each agent has its own memory and remembers the ongoing conversation.

The system will extract useful information from the file **mission_data.txt**.

### MAGI mode

This is a fully autonomous mode.

Following your initial prompt, MAGI will explore new solutions.

It will run continuously until you manually stop the program by pressing Ctrl + C.

## Plugins

### Web plugin

This plugin allows MAGI to browse the internet for up-to-date information. Even when the plugin is active, MAGI decides when to use it.

### Telegram plugin

This plugin enables you to teleoperate MAGI via Telegram, allowing you to have AI support on the go. When the Telegram plugin is enabled, MAGI only accepts commands via Telegram and ignores keyboard input.

If you have both the Telegram plugin and the image generation plugin enabled, you will receive the generated images via Telegram.

To use this plugin you have to create a Telegram bot with BotFather (username: @BotFather) and save the token assigned to your bot. 

You must also write to userinfobot (username: @userinfobot) to get your user ID. MAGI will only communicate with your Telegram user and will ignore other users.

#### Configuration

TELEGRAM_BOT_TOKEN: the token you received from BotFather.

TELEGRAM_USER_ID: your Telegram user ID, you can get it from userinfobot.

### Image generation plugin

This plugin allows MAGI to download an image generation model from Hugging Face.

Only Stable Diffusion 3 checkpoints are supported.

MAGI will use the model to generate context-related images and save them in the folder **workspace**.

If the folder contains images from previous sessions, they will be overwritten.

*System requirements:*

CPU-only: 64GB of system RAM.

GPU: NVIDIA GPU with at least 8GB VRAM. Aim for a combined RAM + VRAM of at least 32GB.

#### Model Access

Some models require authentication. To access these gated models:

- Visit the model's page on Hugging Face (e.g., https://huggingface.co/black-forest-labs/FLUX.1-dev).
- Complete the required access agreement.
- Generate an access token in your Hugging Face account settings.
- Authenticate your local environment by running the following command in the project directory (with your Python environment activated):

```
$ huggingface-cli login
```

#### Configuration

IMAGE_GENERATION_MODEL: this is the model used to generate images (default: stabilityai/stable-diffusion-3.5-large)

IMAGE_GENERATION_LORA: this is the LoRA used to enhance image quality, it must be compatible with the selected model. Leave empty if not using a LoRA (default: None)

IMAGE_GENERATION_SPECS: these are the general features of the images you want to generate. This text will be prepended to the prompt used to generate each image (default: 4K RAW photo, shot on Sony A7R V with 50mm prime lens at f/11, ISO 100, 32-bit HDR, razor-sharp focus, award-winning photo, highly detailed, vibrant colors)

IMAGE_GENERATION_NEGATIVE_PROMPT: these are the unwanted features of the images you want to generate (default: lowres, blurry, out of focus, soft focus, shallow depth of field, jpeg artifacts, noisy, grainy, worst quality, low quality, deformed, disfigured, bad proportions, bad anatomy, malformed body, unnatural pose, unnatural face, asymmetrical eyes, lifeless eyes, unnatural skin)

IMAGE_GENERATION_WIDTH: width of generated images in pixels (default: 1024)

IMAGE_GENERATION_HEIGHT: height of generated images in pixels (default: 1024)

## Model 

You can use any GGUF model supported by llama-cpp-python, as long as it adheres to the ChatML prompt format:

```
<|im_start|>system
You are a friendly AI assistant.
<|im_end|>
<|im_start|>user
Who was Sun Tzu?
<|im_end|>
<|im_start|>assistant
Sun Tzu was the master strategist of ancient China, renowned as the author of The Art of War.
<|im_end|>
```

The model must enclose its extended reasoning between `<think>` tags:

```
<think>
Okay, so I need to explain who was Sun Tzu.
</think>
```

### Recommended models

Qwen3 is the latest generation of large language models from Alibaba Cloud's Qwen series. Built upon extensive training, Qwen3 delivers groundbreaking advancements in reasoning, instruction-following, agent capabilities, and multilingual support.

As a rule of thumb, the combined total of RAM and VRAM (if used) should be at least 50% larger than the GGUF file size.

#### Qwen3-14B-GGUF

For simple to moderate tasks (general conversation, basic coding).

https://huggingface.co/Qwen/Qwen3-14B-GGUF/blob/main/Qwen3-14B-Q8_0.gguf

*System requirements:*

CPU-only: 32GB of system RAM.

GPU: NVIDIA GPU with at least 8GB VRAM. Aim for a combined RAM + VRAM of at least 32GB.

#### Qwen3-32B-GGUF

For complex tasks (advanced reasoning, coding).

https://huggingface.co/Qwen/Qwen3-32B-GGUF/blob/main/Qwen3-32B-Q8_0.gguf

*System requirements:*

CPU-only: 64GB of system RAM.

GPU: NVIDIA GPU with at least 8GB VRAM. Aim for a combined RAM + VRAM of at least 64GB.

## Debian installation

### Prerequisites

Install the following packages:

```
$ sudo apt install build-essential pkg-config libopenblas-dev python3-venv python3-pip apparmor-utils chromium chromium-driver python3-selenium python3-bs4 python3-docx python3-odf python3-pypdf
```

To use your NVIDIA graphics card, you need to install CUDA:

```
$ sudo apt install nvidia-cuda-toolkit
```

### Install

- Clone this repository.

- Place a GGUF model in the root folder.

- Run the following commands in the root folder:

```
$ python3 -m venv venv --system-site-packages
$ source venv/bin/activate
```

- To use only the CPU, run the following command:

```
$ CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS" pip install --upgrade -r requirements.txt
```

- If you want to use your NVIDIA graphics card, run the following command:

```
$ CMAKE_ARGS="-DGGML_CUDA=on" pip install --upgrade -r requirements.txt
```

### Run

- Open a console and navigate to the project root folder.

- If the Python virtual environment is not already active, activate it with the following command:

```
$ source venv/bin/activate
```

- To start MAGI, run this command:

```
$ python magi.py
```

### Exit MAGI

- To exit MAGI, type the command **exit** or press Ctrl + C.

- After running MAGI, deactivate the Python virtual environment with the following command:

```
$ deactivate
```

## Docker installation (CPU-only)

### Prerequisites

#### Linux

Install the following packages:

```
$ sudo apt install docker.io apparmor-utils
```

#### Other systems

Install Docker.

### Install

- Clone this repository.

- Optional: place a model in the root folder to include it in the Docker image.

- To create the Docker image, run the following command in the root folder:

```
$ sudo docker build --no-cache -t magi .
```

### Run a Docker image with a model

If you have placed the model in the Docker image, run this command:

```
$ sudo docker run -it magi
```

### Run a Docker image without a model

If you have placed the model in a local folder, run this command, replacing MODEL_PATH with the full path to the model file and MODEL_FILE with the name of the model file:

```
$ sudo docker run -it -v MODEL_PATH:/app/MODEL_FILE magi
```

Example:

```
$ sudo docker run -it -v /home/user/models/Hermes-2-Pro-Mistral-7B.Q8_0.gguf:/app/Hermes-2-Pro-Mistral-7B.Q8_0.gguf magi
```

### Exit MAGI

To exit MAGI, type the command **exit** or press Ctrl + C.

If you want to print the log of the last run, use this command:

```
$ sudo docker logs $(sudo docker ps -l -q)
```

