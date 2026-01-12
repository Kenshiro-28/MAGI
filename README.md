# MAGI

[![MAGI intro video](https://ipfs.io/ipfs/bafybeicplzuyad3stsfd5nz4l6s4df7czyocfmqgxujruugyxby7pmmkpm)](https://ipfs.io/ipfs/bafybeihhurksv4whiocfumnqxl4we7y4baonkj4ryami4nx2jhvvvpg2oa)

<p align="center">
  <a href="https://github.com/Kenshiro-28/MAGI/actions"><img src="https://img.shields.io/github/actions/workflow/status/Kenshiro-28/MAGI/lint.yml?branch=main&style=for-the-badge&label=Lint" alt="Lint Status"></a>
  <a href="https://github.com/Kenshiro-28/MAGI/actions"><img src="https://img.shields.io/github/actions/workflow/status/Kenshiro-28/MAGI/test.yml?branch=main&style=for-the-badge&label=Test" alt="Test Status"></a>
  <a href="https://github.com/Kenshiro-28/MAGI/actions"><img src="https://img.shields.io/github/actions/workflow/status/Kenshiro-28/MAGI/docker.yml?branch=main&style=for-the-badge&label=Docker" alt="Docker Status"></a>
  <a href="https://github.com/Kenshiro-28/MAGI/releases"><img src="https://img.shields.io/github/v/release/Kenshiro-28/MAGI?include_prereleases&style=for-the-badge" alt="GitHub release"></a>
  <a href="https://github.com/Kenshiro-28/MAGI/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Kenshiro-28/MAGI?style=for-the-badge&color=blue" alt="License"></a>
</p>

**MAGI (マギ)** is an advanced AI system powered by open-source large language models. It operates through a conversational interface and is designed to run efficiently on consumer-grade hardware.

Key features include a customizable Core Protocol for enhanced reasoning, a modular Toolchain for dynamic tool chaining (code execution, web browsing, and image generation), and teleoperation via Telegram for remote access.

Built and tested on **Debian stable** (recommended). On other OSes, use the Docker setup.

## Configuration

You can customize MAGI by editing the file **config.cfg**.

The main options are:

TEMPERATURE: model temperature (default: 0.6)

CONTEXT_SIZE: number of tokens in the context window (default: 65536)

ENABLE_CODE_RUNNER_PLUGIN: enable or disable the Code Runner plugin (default: YES)

ENABLE_IMAGE_GENERATION_PLUGIN: enable or disable the image generation plugin (default: YES)

ENABLE_TELEGRAM_PLUGIN: enable or disable the Telegram plugin (default: NO)

ENABLE_WEB_PLUGIN: enable or disable the web plugin (default: YES)

DISPLAY_EXTENDED_REASONING: display the extended reasoning between `<think>...</think>` tags (default: NO)

ENABLE_LOG: enable or disable logging to the file **mission_log.txt** (default: NO)

## Prime Directives

Prime Directives serve as the system prompt or behavioral guidelines, defining MAGI's personality, rules, and operational ethos. This is where you imprint MAGI with a specific identity—whether as a helpful assistant, a fictional character, or a specialized agent.

You can set your Prime Directives in the file **prime_directives.txt**. 

## Core Protocol

The Core Protocol boosts MAGI's reasoning by guiding its internal thought process with a customizable reasoning framework.

You can tailor it to different techniques such as Chain-of-Thought, Chain of Draft, or other variants.

You can set your Core Protocol in the file **core_protocol.txt**.

The default protocol includes:

- Foundational Deconstruction: Classify the problem, list assumptions, define boundaries.
- Hypothesis Generation & Inversion: Create diverse approaches, stress-test via premortem.
- Multi-Method Derivation & Triangulation: Solve via orthogonal methods, reconcile discrepancies.
- Epistemic Rigor Loop: Annotate claims, test counterfactuals and edges.
- Metacognitive Consolidation: Synthesize, critique, calibrate confidence, rebut objections.

To revert to the default model reasoning without applying any custom protocol, simply remove all contents from the file **core_protocol.txt** or delete the file.

## Toolchain

MAGI's toolchain acts as a modular system for registering and calling tools, similar to frameworks like Langchain. It allows MAGI to dynamically select and execute tools based on task needs, chaining their outputs into responses. Tools are enabled through the plugin system by editing the file **config.cfg**.

The plugin system includes the following tools:

- Code Runner plugin: adds a tool to generate and execute Python code.
- Image generation plugin: adds a tool to generate images.
- Web plugin: adds a tool to browse the web.

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

The Captain will evaluate each Soldier's response and provide additional guidance when necessary.

Each agent has its own memory and remembers the ongoing conversation.

The system will extract useful information from the file **mission_data.txt**.

### MAGI mode

This is a fully autonomous mode.

After receiving your initial prompt, MAGI will work autonomously to accomplish its mission.

Optionally, you can include the main objective and any critical mission data in the file **prime_directives.txt** to help ensure that MAGI remains aligned with its main objective during long-running operations. For example:

```
You are MAGI, a friendly AI assistant.

Your primary mission is to research tech stocks focused on robotics and AI automation, and identify the most promising options for long-term growth.
```

MAGI will run continuously until you manually stop it by pressing Ctrl + C.

## Plugins

### Code Runner plugin

This plugin adds a tool to generate and execute Python code to solve specific tasks, such as mathematical operations, accessing resources on the internet, simulations, or complex logic.

MAGI will install the required Python packages in an isolated virtual environment.

Linting is performed using Ruff to ensure clean code, and the execution times out after 30 minutes for safety.

The generated code will run non-interactively, printing all results to the console.

Moreover, the generated code will also print its relevant internal state at the end of each execution for reuse in multi-step tasks.

MAGI will review and refine the generated code and its output up to 10 times to ensure it functions correctly and fully completes the task.

### Image generation plugin

This plugin adds a tool to generate images.

Only Stable Diffusion 3 checkpoints are supported.

It automatically downloads the specified image generation model from Hugging Face.

MAGI will use the model to generate context-related images and save them in the folder **workspace**.

If the folder contains images from previous sessions, they will be overwritten.

*System requirements:*

CPU-only: 64GB of system RAM (due to float32 usage instead of float16).

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

IMAGE_GENERATION_SPECS: these are the general features of the images you want to generate. This text will be prepended to the prompt used to generate each image (default: 4K RAW photo, 50mm lens, f/8 aperture, high-end commercial photography, razor-sharp focus, highly detailed, intricate details, realistic textures, volumetric lighting, cinematic color grading)

IMAGE_GENERATION_NEGATIVE_PROMPT: these are the unwanted features of the images you want to generate (default: worst quality, low quality, lowres, muddy textures, blurry, out of focus, soft focus, jpeg artifacts, deformed, bad proportions, gross proportions, bad anatomy, poorly drawn face, asymmetrical eyes, lifeless eyes, colored sclera)

IMAGE_GENERATION_WIDTH: width of generated images in pixels (default: 896)

IMAGE_GENERATION_HEIGHT: height of generated images in pixels (default: 1344)

### Telegram plugin

This plugin enables you to teleoperate MAGI via Telegram, allowing you to have AI support on the go. When the Telegram plugin is enabled, MAGI only accepts commands via Telegram and ignores keyboard input.

If you have both the Telegram plugin and the image generation plugin enabled, you will receive the generated images via Telegram.

To use this plugin you have to create a Telegram bot with BotFather (username: @BotFather) and save the token assigned to your bot. 

You must also write to userinfobot (username: @userinfobot) to get your user ID. MAGI will only communicate with your Telegram user and will ignore other users.

#### Configuration

TELEGRAM_BOT_TOKEN: the token you received from BotFather.

TELEGRAM_USER_ID: your Telegram user ID, you can get it from userinfobot.

### Web plugin

This plugin adds a tool to browse the internet for up-to-date information.

MAGI will search, scrape, and summarize relevant pages with automatic early stopping on success.

It uses Dux Distributed Global Search (DDGS), a metasearch library that aggregates results from diverse web search services.

It only scrapes websites that explicitly authorize it in robots.txt.

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
Sun Tzu was the author of The Art of War.
<|im_end|>
```

The model must enclose its extended reasoning between `<think>` tags:

```
<think>Okay, so I need to explain who was Sun Tzu.</think>
```

### Recommended models

Hint: As a rule of thumb, your combined RAM + VRAM should be at least 50% larger than the GGUF file size.

#### Qwen3-Deckard-Large-Almost-Human-6B-III-Final-OMEGA-GGUF

![Qwen3-Deckard-Large](https://ipfs.io/ipfs/bafybeifhmkvn2idrf2v343eq3aflxcwzut3dhfwjj4y7pgqb7ckwy25avm)

Qwen3-Deckard-Large-Almost-Human-6B-III-Final-OMEGA is a 6-billion parameter model created by DavidAU, based on the Qwen3 architecture.

This model is good for general usage and basic coding.

The "Deckard" series (named after the Blade Runner protagonist) features training on an in-house dataset derived from Philip K. Dick's writings. The "Almost Human" variant adds biographical data, letters, and notes from the author, resulting in enhanced tone, thinking patterns, and prose quality.

https://huggingface.co/mradermacher/Qwen3-Deckard-Large-Almost-Human-6B-III-Final-OMEGA-GGUF/blob/main/Qwen3-Deckard-Large-Almost-Human-6B-III-Final-OMEGA.Q8_0.gguf

*System requirements:*

CPU-only: 32GB of system RAM.

GPU: NVIDIA GPU with at least 8GB VRAM. Aim for a combined RAM + VRAM of at least 32GB.

#### Qwen3-42B-A3B-2507-Thinking-TOTAL-RECALL-v2-Medium-MASTER-CODER-GGUF

![Qwen3-TOTAL-RECALL](https://ipfs.io/ipfs/bafybeic3p7ux4lqk64xcvaynxxewsnljmkycl4xaz46hr3cdxnxunv3dty)

Qwen3-42B-A3B-2507-Thinking-TOTAL-RECALL-v2-Medium-MASTER-CODER-GGUF is a 42-billion parameter model created by DavidAU, based on Qwen3-30B-A3B-2507-Thinking from Alibaba Cloud's Qwen series.

This model is recommended for use cases that require high reasoning skills.

https://huggingface.co/mradermacher/Qwen3-42B-A3B-2507-Thinking-TOTAL-RECALL-v2-Medium-MASTER-CODER-GGUF/blob/main/Qwen3-42B-A3B-2507-Thinking-TOTAL-RECALL-v2-Medium-MASTER-CODER.Q8_0.gguf

*System requirements:*

CPU-only: 64GB of system RAM.

GPU: NVIDIA GPU with at least 16GB VRAM. Aim for a combined RAM + VRAM of at least 64GB.

## Debian installation

### Prerequisites

Install the following packages:

```
$ sudo apt install build-essential apparmor-utils git pkg-config libopenblas-dev python3-venv python3-pip python3-requests python3-pycurl python3-protego antiword python3-bs4 python3-docx python3-odf python3-pypdf python3-python-telegram-bot
```

To use your NVIDIA graphics card, you need to install CUDA:

```
$ sudo apt install nvidia-cuda-toolkit
```

### Security

Since MAGI installs third-party Python packages and generates and executes code, running it under your personal user account poses a security risk.

I strongly advise running MAGI as a dedicated, unprivileged user to isolate these processes.

After installing prerequisites, create a new user, for example `magi`:

```
$ sudo adduser magi
```

When you want to install or run MAGI, switch to the new user:

```
$ su - magi
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

## Disclaimer

MAGI is a non-commercial, open-source project created for educational and research purposes.

This project is a fan tribute. All references to characters, organizations, terminology, and visual assets from existing media are used solely as a homage. All original media and intellectual property belong to their respective owners.

This software is provided "as is", without warranty of any kind. The user assumes full responsibility for any code execution or system modifications performed by the AI.

