# MAGI

This program is an autonomous agent that uses the GPT-4 model to respond to user requests. Prime directives allow you to alter the behavior of the model, making it behave in the desired way. MAGI has a Mission mode that allows it to generate a task list based on the user's request to generate a more elaborate response. In the future it will be able to surf the Internet and work continuously.

## Prime directives

Edit the file **prime_directives.txt** to set your prime directives.

## Mission mode

To enable mission mode, type the letter **m** and press enter. The mission data will be saved in **mission.txt**.

## API key 

Save your OpenAI API key in an environment variable called **OPENAI_API_KEY**.

## Installation

- Clone this repository.

- Install Python 3.10 or later.

- Install OpenAI package:

```
$ pip3 install openai
```

## Running

Run this command in the root folder to start the program:

```
$ python3 magi.py
```

Press Ctrl + C to exit

----- Work in progress -----
