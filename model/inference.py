from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
import argparse
from pathlib import Path


def generate_response(model, tokenizer, prompt, max_new_tokens=250):
    """
    Генерирует ответ сети на промпт

    Args:
        model (AutoModelForCausalLM) : Модель
        tokenizer (AutoTokenizer) : Токенайзер
        prompt (str) : Промпт
        max_new_tokens (int) : Максимальное количество токенов ответа сети.
            По умолчанию : 250

    Returns:
        str : Ответ сети
    """

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.25,
        top_p=0.95,
        repetition_penalty=1.1,
        pad_token_id=tokenizer.eos_token_id
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response


def prepare_finetuned_model_and_tokenizer(model_id, finetuned_path):
    """
    Загружает обученную модель отдельно с LoRa

    Args:
        model_id (str) : ID модели
        finetuned_path (pathlib.Path) : Путь к обученной модели

    Returns:
        AutoModelForCausalLM, AutoTokenizer) : Модель и токенайзер
    """

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    base_model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="cpu"
    )
    model = PeftModel.from_pretrained(base_model, finetuned_path)
    return model, tokenizer


def prepare_merged_model_and_tokenizer(merged_path):
    """
    Загружает обученную модель, совмещенную с LoRa

    Args:
        merged_path (pathlib.Path) : Путь к обученной модели

    Returns:
        AutoModelForCausalLM, AutoTokenizer) : Модель и токенайзер
    """
    
    tokenizer = AutoTokenizer.from_pretrained(merged_path)
    model = AutoModelForCausalLM.from_pretrained(
        merged_path,
        torch_dtype=torch.bfloat16,
        device_map="cpu"
    )
    return model, tokenizer


if __name__ == '__main__':
    project_dir = Path(__file__).parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--prompt', type=str, default="Напиши подравление c Днем Рождения",
        help='Prompt'
    )
    args = parser.parse_args()

    merged_path = project_dir / "tinyllama/merged"
    model, tokenizer = prepare_merged_model_and_tokenizer(merged_path)
    model.eval() 

    response = generate_response(model, tokenizer, "### Instruction: " + args.prompt)
    print(response)
