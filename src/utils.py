import yaml

#читает YAML-файл и возвращает его содержимое в виде словаря Python,
#чтобы не дублировать код для чтения конфигурации в каждом файле

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)