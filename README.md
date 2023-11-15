# MAGI

MAGI is an autonomous agent based on open-source large language models, offering an AI solution accessible to everyone. MAGI is designed to run efficiently on consumer-grade hardware and features a plugin system that enables Internet browsing, remote operation through Telegram and image generation with Stable Diffusion.

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

You can use any model supported by llama-cpp-python, as long as it has a context size of at least 8K tokens and adheres to the ChatML prompt format:

```
<|im_start|>system
{system_message}<|im_end|>
<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant
```

After cloning the repository, save the .gguf file in the root folder. 

### Recommended model

Dolphin 2.2.1 Mistral 7B is a very good general-purpose model that only requires 16 GB of RAM to operate.

This model is not censored, proceed with caution.

https://huggingface.co/TheBloke/dolphin-2.2.1-mistral-7B-GGUF/blob/main/dolphin-2.2.1-mistral-7b.Q8_0.gguf

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

- Save a model in the root folder.

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
$ sudo apt install build-essential pkg-config libopenblas-dev python3-venv python3-pip apparmor-utils
```

#### Other systems

- Install Python 3.11 or later.

- Install a C++ compiler.

- Install OpenBLAS.

### Installation

- Clone this repository.

- Save a model in the root folder.

- Install Python packages:

```
$ CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip install --no-cache-dir -r requirements.txt
```

### Running

Run this command in the root folder to start MAGI:

```
$ python magi.py
```

To exit MAGI, type the command **exit** or press Ctrl + C.


