# MAGI

MAGI is an advanced chatbot powered by open-source large language models, offering an AI solution accessible to everyone. MAGI is designed to run efficiently on consumer-grade hardware and features a plugin system that enables Internet browsing, remote operation through Telegram and image generation with Stable Diffusion.

## Configuration

The web plugin is enabled by default.

You can customize MAGI by editing the file **config.cfg**.

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

It will save a log in the file **mission_log.txt**.

You can also add useful information in the file **mission_data.txt**.

### NERV mode

NERV is a virtual organization composed of AI agents.

Each agent has its own memory and remembers the ongoing conversation.

You can configure each agent to behave like a fictional character or follow a set of rules.

MAGI will save a log in the file **mission_log.txt**.

You can also add useful information in the file **mission_data.txt**.

## Plugins

### Web plugin

This plugin allows MAGI to browse the internet for up-to-date information. Even when the plugin is active, MAGI decides when to use it.

#### Configuration

ENABLE_WEB_PLUGIN: enable or disable the web plugin.

### Telegram plugin

This plugin enables you to teleoperate MAGI via Telegram, allowing you to have AI support on the go. When the Telegram plugin is enabled, MAGI only accepts commands via Telegram and ignores keyboard input.

If you have both the Telegram plugin and the Stable Diffusion plugin enabled, you will receive the generated images via Telegram.

To use this plugin you have to create a Telegram bot with BotFather (username: @BotFather) and save the token assigned to your bot. 

You must also write to userinfobot (username: @userinfobot) to get your user ID. MAGI will only communicate with your Telegram user and will ignore other users.

#### Configuration

ENABLE_TELEGRAM_PLUGIN: enable or disable the Telegram plugin.

TELEGRAM_BOT_TOKEN: the token you received from BotFather.

TELEGRAM_USER_ID: your Telegram user ID, you can get it from userinfobot.

### Stable Diffusion plugin

This plugin allows MAGI to download a Stable Diffusion model from Hugging Face.

MAGI will use the model to generate context-related images and save them in the folder **workspace**.

If the folder contains images from previous sessions, they will be overwritten.

#### Configuration

ENABLE_STABLE_DIFFUSION_PLUGIN: enable or disable the Stable Diffusion plugin.

STABLE_DIFFUSION_MODEL: this is the model used to generate images.

STABLE_DIFFUSION_IMAGE_SPECS: these are the general features of the images you want to generate. This text will be added to the prompt used to generate each image.

STABLE_DIFFUSION_NEGATIVE_PROMPT: these are the unwanted features of the images you want to generate. This text will be the negative prompt used to generate each image.

## Model 

You can use any GGUF model supported by llama-cpp-python, as long as it adheres to the ChatML prompt format:

```
<|im_start|>system
{system_message}<|im_end|>
<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant
```

### Recommended model

Qwen2.5-7B-Instruct is a very good general-purpose model that only requires 16 GB of RAM to operate.

Please download all parts into the project's root folder:

https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/blob/main/qwen2.5-7b-instruct-q8_0-00001-of-00003.gguf

https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/blob/main/qwen2.5-7b-instruct-q8_0-00002-of-00003.gguf

https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/blob/main/qwen2.5-7b-instruct-q8_0-00003-of-00003.gguf

You can use larger models to improve reasoning capabilities. As a rule of thumb, the combined total of RAM and VRAM (if used) should be larger than the size of the GGUF file.

## Docker installation (CPU only)

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

## Debian installation

### Prerequisites

Install the following packages:

```
$ sudo apt install build-essential pkg-config libopenblas-dev python3-venv python3-pip apparmor-utils chromium chromium-driver python3-selenium python3-bs4 python3-docx python3-odf python3-pypdf2
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

