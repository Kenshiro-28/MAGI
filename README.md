# MAGI

MAGI is an autonomous agent that leverages the Llama 2 model to offer an open-source AI accessible to everyone. MAGI is designed to run efficiently on consumer-grade hardware and features a plugin system that enables Internet browsing, remote operation through Telegram and image generation with Stable Diffusion.

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

MAGI will autonomously plan and execute strategies to complete its goal.

Once it receives a prompt, it will run continuously and accept no further prompts. To exit MAGI, press Ctrl + C.

It will save a log in the file **mission_log.txt**.

You can also add useful information in the file **mission_data.txt**.

## Plugins

You can configure MAGI plugins by editing the file **config.cfg**.

### Web plugin

This plugin allows MAGI to browse the Internet for up-to-date information.

#### Configuration

ENABLE_WEB_PLUGIN: enable or disable the web plugin (default: enabled).

### Telegram plugin

This plugin enables you to teleoperate MAGI via Telegram, allowing you to have AI support on the go. When the Telegram plugin is enabled, MAGI only accepts commands via Telegram and ignores keyboard input.

To use this plugin you have to create a Telegram bot with BotFather (username: @BotFather) and save the token assigned to your bot. 

You must also write to userinfobot (username: @userinfobot) to get your user ID. MAGI will only communicate with your Telegram user and will ignore other users.

#### Configuration

ENABLE_TELEGRAM_PLUGIN: enable or disable the Telegram plugin (default: disabled).

TELEGRAM_BOT_TOKEN: the token you received from BotFather.

TELEGRAM_USER_ID: your Telegram user ID, you can get it from userinfobot.

### Stable Diffusion plugin

This plugin allows MAGI to download a Stable Diffusion model from Hugging Face.

MAGI will use the model to generate context-related images and save them in the folder **workspace**.

If the folder contains images from previous sessions, they will be overwritten.

#### Configuration

ENABLE_STABLE_DIFFUSION_PLUGIN: enable or disable the Stable Diffusion plugin (default: disabled).

STABLE_DIFFUSION_MODEL: this is the model used to generate images. The text is a path to a Hugging Face model.

STABLE_DIFFUSION_IMAGE_SPECS: these are the general features of the images you want to generate. This text will be added to the prompt used to generate each image.

STABLE_DIFFUSION_NEGATIVE_PROMPT: these are the unwanted features of the images you want to generate. This text will be the negative prompt used to generate each image.

## Model 

You can use any Llama 2 model that is compatible with llama.cpp and has the Vicuna prompt format:

```
USER: Who was Sun Tzu?
ASSISTANT: 
```

After cloning the repository, save the .bin file in the root folder. 

### Recommended model

At the time of writing, WizardLM-13B-V1.2 is the best Llama 2 model:

https://huggingface.co/TheBloke/WizardLM-13B-V1.2-GGML/blob/main/wizardlm-13b-v1.2.ggmlv3.q5_K_M.bin

## Docker installation

I strongly recommend running MAGI inside a Docker container. This method significantly mitigates potential risks by isolating the application from the host system. 

### Prerequisites

#### Linux

- Install the following packages:

```
$ sudo apt install docker.io apparmor-utils
```

#### Other systems

- Install Docker

### Installation

- Clone this repository.

- Save a Llama 2 model in the root folder.

- Create a Docker image, you can do it by running this command in the root folder:

```
$ sudo docker build --no-cache -t magi .
```

### Running

Run this command to start MAGI:

```
$ sudo docker run -it magi
```

Print the log of the last run:

```
$ sudo docker logs $(sudo docker ps -l -q)
```

To exit MAGI, type the command **exit** or press Ctrl + C.

## Local installation

### Prerequisites

#### Linux

- Install the following packages:

```
$ sudo apt install build-essential python3-venv python3-pip apparmor-utils firefox-esr 
```

#### Other systems

- Install Firefox

- Install Python 3.11 or later.

- Install a C++ compiler.

### Installation

- Clone this repository.

- Save a Llama 2 model in the root folder.

- Install Python packages:

```
$ pip install -r requirements.txt
```

#### GPU acceleration (optional)

To enable GPU acceleration on a Linux system with an Nvidia graphics card, run the following commands:

```
$ sudo apt install nvidia-cuda-toolkit
$ export LLAMA_CUBLAS=1
$ CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir
```

For other systems you can check the project website:

https://pypi.org/project/llama-cpp-python/

### Running

Run this command in the root folder to start MAGI:

```
$ python magi.py
```

To exit MAGI, type the command **exit** or press Ctrl + C.


