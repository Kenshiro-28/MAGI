# MAGI

MAGI is an autonomous agent leveraging the GPT model, providing streamlined and professional AI assistance for various tasks. Prime Directives allow you to customize the behavior of the model to suit your needs. Mission mode analyzes your query and generates an enhanced response based on a list of tasks that it automatically solves. In the future it will be able to browse the Internet and work continuously.

## Prime Directives

MAGI never forgets its Prime Directives. You can use popular prompts to enhance the behavior of the model. 

You can set your Prime Directives in the file **prime_directives.txt**. 

## Mission mode

MAGI features a Mission mode that analyzes your query and generates an enhanced response based on a list of tasks that it automatically solves. To enable Mission mode, type the letter **m** and press enter. The mission data will be saved in the file **mission.txt**.

## API key 

Save your OpenAI API key in an environment variable called **OPENAI_API_KEY**.

## Installation

- Clone this repository.

- Install Python 3.10 or later.

- Install OpenAI package:

```
$ pip install openai
```

## Running

Run this command in the root folder to start the program:

```
$ python magi.py
```

Press Ctrl + C to exit


