from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model
from pathlib import Path
import argparse
import torch
import json
from preprocess import tokenize_json


def prepare_model_and_tokenizer(model_id):
    """
    Возвращает модель и токенизатор к ней

    Args:
        model_id (str) : ID модели
    
    Returns:
        (AutoModelForCausalLM, AutoTokenizer) : Модель и токенайзер
    """

    base_model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(base_model, lora_config)
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    return model, tokenizer


if __name__ == '__main__':
    project_dir = Path(__file__).parent.parent
    parser = argparse.ArgumentParser(
        description='Обучает TinyLLama'
    )
    parser.add_argument(
        '--lr', type=float, default=5e-4,
        help='Learning Rate'
    )
    parser.add_argument(
        '--epochs', type=int, default=6,
        help='Количество эпох'
    )
    parser.add_argument(
        '--dataset_path', type=str, default=project_dir / 'data/clean/dataset.json',
        help='Путь к датасету'
    )
    args = parser.parse_args()

    model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    model, tokenizer = prepare_model_and_tokenizer(model_id)
    model.train()

    with open(args.dataset_path, 'r') as f:
        dataset_json = json.load(f)
    tokenized_dataset = tokenize_json(dataset_json, tokenizer)

    training_args = TrainingArguments(
        output_dir="./tinyllama-lora-finetuned",
        overwrite_output_dir=True,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=args.lr,
        lr_scheduler_type='cosine',
        num_train_epochs=args.epochs,
        logging_steps=10,
        save_steps=200,
        save_total_limit=2,
        bf16=True,
        label_names=["labels"],
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset
    )

    trainer.train()
    trainer.save_model(project_dir / "tinyllama/lora-final")
    merged_model = model.merge_and_unload()
    merged_model.save_pretrained(project_dir / "tinyllama/merged")
