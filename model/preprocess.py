import argparse
import random
import json
import os
import tqdm
import requests
import time
from bs4 import BeautifulSoup
from pathlib import Path
from datasets import Dataset


SEED = 42


def parse_wishes(wishes_path, url, base_url):
    """
    Парсит пожелания с сайта Поздравок

    Args:
        wishes_path (pathlib.Path) : Путь к txt файлу для сохранения поздравлений
        url (str) : URL страницы для парсинга
        base_url (str) : URL главной страницы сайта
    """

    if os.path.exists(wishes_path):
        os.remove(wishes_path)

    f = open(wishes_path, 'w+')
    for _ in tqdm.tqdm(range(180), desc='Parsing'):
        time.sleep(random.uniform(0.5, 1))
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        data = soup.find('div', {'class': 'content'})
        data = data.find_all('p')

        for wish in data:
            f.write(wish.get_text() + '\n\n')

        next_url = soup.find('div', {'class': 'pages_next'})
        next_url = next_url.find('a', href=True)['href']
        url = base_url + next_url
        response.close()
    f.close()


def txt2list(txt_path):
    """
    Очищает строки от лишних символов и возвращает список поздравлений

    Args:
        txt_path (pathlib.Path) : Путь к txt файлу с пожеланиями

    Returns:
        list : список пожеланий
    """
    with open(txt_path, 'r') as f:
        data = f.read()
        data = data.replace('\xa0', ' ')
        result = data.split('\n\n')
    return result


def raw2json(wishes_path, prompts_path, json_path):
    """
    Создает датасет из поздравлений в формате json.
    Количество ответов (поздравлений) равномерно распределяется по промптам.

    Args:
        wishes_path (pathlib.Path) : Путь к txt файлу с сохраненными поздравлений
        promopts_path (pathlib.Path) : Путь к txt файлы с промптами для модели
        json_path (pathlib.Path) : Путь к датасету
    """

    wishes = txt2list(wishes_path)
    random.shuffle(wishes)

    prompts = txt2list(prompts_path)
    random.shuffle(prompts)

    json_data = dict()
    wishes_per_prompt = len(wishes) // len(prompts)
    for i, prompt in enumerate(prompts):
        for j in range(wishes_per_prompt):
            curr_example = i * wishes_per_prompt + j
            wish = wishes[curr_example]
            json_data[f'prompt_{curr_example}'] = \
                f"### Instruction: {prompt}\n" + \
                f"### Response: {wish}"

    with open(json_path, 'w', encoding='utf8') as f:
        json.dump(json_data, f, ensure_ascii=False)


def tokenize_json(dataset_json, tokenizer):
    """
    Токенизирует json датасет

    Args:
        dataset_json (dict) : Датасет
        tokenizer (transformers.AutoTokenizer) : Токенайзер

    Returns:
        datasets.Dataset : Токенизированный датасет
    """

    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            padding="max_length",
            max_length=512,
            return_special_tokens_mask=True
        )

    data = {'text': []}
    for key, value in dataset_json.items():
        data['text'].append(value)
    dataset = Dataset.from_dict(data)
    tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=["text"])
    tokenized_dataset = tokenized_dataset.shuffle(seed=SEED)
    tokenized_dataset = tokenized_dataset.map(lambda x: {"labels": x["input_ids"]})
    return tokenized_dataset


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Data preprocessing'
    )
    parser.add_argument('--parse', type=bool,
        default=False,
        help='Flag for parsing'
    )
    args = parser.parse_args()

    random.seed(SEED)
    project_dir = Path(__file__).parent.parent
    wishes_path = project_dir / 'data/raw/wishes.txt'
    prompts_path = project_dir / 'data/raw/prompts.txt'
    json_path = project_dir / 'data/clean/dataset.json'
    base_url = 'https://pozdravok.com'
    url = 'https://pozdravok.com/pozdravleniya/den-rozhdeniya/proza.htm'
    if args.parse:
        parse_wishes(wishes_path, url, base_url)
    raw2json(wishes_path, prompts_path, json_path)
