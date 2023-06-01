# MAGI

MAGI is an autonomous agent leveraging the LLaMA model, providing streamlined and professional AI assistance for various tasks. Each time a query is made, MAGI decides autonomously whether to access the Internet for up-to-date information. Prime Directives allow you to customize the behavior of the model to suit your needs. Mission mode analyzes your query and generates an enhanced response based on a list of tasks that it automatically solves.

## Prime Directives

MAGI never forgets its Prime Directives. You can use popular prompts to enhance the behavior of the model. 

You can set your Prime Directives in the file **prime_directives.txt**. 

## Mission mode

MAGI features a Mission mode that analyzes your query and generates an enhanced response based on a list of tasks that it automatically solves. To enable Mission mode, type the letter **m** and press enter. The mission log will be saved in the file **mission_log.txt**.

You can add useful information in the file **mission_data.txt**. This information will only be used if it is related to the current mission.

## Model 

You can use any LLaMA model that is compatible with llama.cpp and has the Vicuna v1.1 prompt format:

```
USER: Who was Sun Tzu?
ASSISTANT: 
```

After cloning the repository, save the .bin file in the root folder. This one is working fine:

https://huggingface.co/TheBloke/wizard-vicuna-13B-GGML/resolve/main/wizard-vicuna-13B.ggmlv3.q4_0.bin

## Installation

- Clone this repository.

- Save a LLaMA model in the root folder.

- Install Python 3.10 or later.

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

You can install Docker from the official repositories of your Linux system:

```
$ sudo apt install docker.io
```

Save a LLaMA model in the root folder and create a Docker image:

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

