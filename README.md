# MAGI

MAGI is an autonomous agent that leverages the LLaMA model to offer streamlined and professional AI assistance across a wide range of tasks. Prime Directives allow you to customize the behavior of the model to suit your needs. Mission mode allows MAGI to work autonomously and browse the Internet for up-to-date information. MAGI can be teleoperated via Telegram, allowing you to have AI support on the go.

## Prime Directives

MAGI never forgets its Prime Directives. You can use popular prompts to enhance the behavior of the model. 

You can set your Prime Directives in the file **prime_directives.txt**. 

## Mission mode

MAGI features a mission mode that runs autonomously and browses the Internet for up-to-date information. To enable mission mode, type the letter **m** and press enter. The mission log will be saved in the file **mission_log.txt**.

You can add useful information in the file **mission_data.txt**. This information will only be used if it is related to the current mission.

## Plugins

You can configure MAGI plugins by editing the file **config.cfg**.

### Web plugin

This plugin allows mission mode to browse the Internet for up-to-date information.

#### Configuration

ENABLE_WEB_PLUGIN: enable or disable the web plugin (default: enabled).

### Telegram plugin

This plugin allows you to teleoperate MAGI via Telegram, allowing you to have AI support on the go. When the Telegram plugin is enabled, MAGI only accepts commands via Telegram and ignores keyboard input. To use this plugin you have to create a Telegram bot with BotFather (Username: @BotFather) and save the token assigned to your bot. You must also write to userinfobot (Username: @userinfobot) to get your user ID. MAGI will only communicate with your Telegram user and will ignore other users.

#### Configuration

ENABLE_TELEGRAM_PLUGIN: enable or disable the Telegram plugin (default: disabled).

TELEGRAM_BOT_TOKEN: the token you received from BotFather.

TELEGRAM_USER_ID: your Telegram user ID, you can get it from userinfobot.

## Model 

You can use any LLaMA model that is compatible with llama.cpp and has the Vicuna v1.1 prompt format:

```
USER: Who was Sun Tzu?
ASSISTANT: 
```

After cloning the repository, save the .bin file in the root folder. 

This model works fine on an average computer with 16 GB of RAM:

https://huggingface.co/TheBloke/Wizard-Vicuna-13B-Uncensored-GGML/resolve/main/Wizard-Vicuna-13B-Uncensored.ggmlv3.q4_K_M.bin

## Installation

- Install Firefox

- Install Python 3.11 or later.

- Install a C++ compiler.

- Clone this repository.

- Save a LLaMA model in the root folder.

- Install Python packages:

```
$ pip install -r requirements.txt
```

## Running

Run this command in the root folder to start MAGI:

```
$ python magi.py
```

To exit MAGI, type the command **exit** or press Ctrl + C.

## Docker

I strongly recommend running MAGI inside a Docker container. This method significantly mitigates potential risks by isolating the application from the host system. Continue with the following steps to set up your Docker environment:

### Installation

- Install Docker, you can do it from the official repositories of your Linux system:

```
$ sudo apt install docker.io
```

- Clone this repository.

- Save a LLaMA model in the root folder.

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

