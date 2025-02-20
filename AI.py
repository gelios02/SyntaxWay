import os
import json
import time
import re
import random
import functools
from dotenv import load_dotenv
from gigachat import GigaChat
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Загрузка переменных окружения
load_dotenv()
GIGACHAT_API_KEY = os.getenv("GIGACHAT_API_KEY")
if not GIGACHAT_API_KEY:
    raise ValueError("GIGACHAT_API_KEY не найден. Проверьте файл .env и переменную GIGACHAT_API_KEY.")


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, timeout, *args, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        if "timeout" not in kwargs or kwargs["timeout"] is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


# Инициализация клиента GigaChat
giga = GigaChat(
    credentials=GIGACHAT_API_KEY,
    model="GigaChat-Max",
    verify_ssl_certs=False
)

if hasattr(giga, "_session"):
    giga._session.mount("https://", TimeoutHTTPAdapter(timeout=300))


def generate_material(language, difficulty):
    # 10 вариантов промтов с одинаковым смыслом, но разными формулировками:
    prompt_variants = [
        f"Ты опытный преподаватель программирования. Создай подробный обучающий материал по синтаксису языка {language} для дня {difficulty}. Ответ должен содержать только текст обучающего материала без лишних комментариев. Заключение писать не надо. Писать, какой день тоже не надо.",
        f"Будучи экспертом в программировании, составь детальный материал по синтаксису языка {language} для дня {difficulty}. Выдай только необходимый текст без излишеств, без упоминания дня и заключения.",
        f"Ты профессиональный преподаватель по программированию. Сформируй подробный обучающий материал по синтаксису {language} для дня {difficulty}. Твой ответ должен состоять исключительно из текста материала, без лишних комментариев и без указания дня.",
        f"Составь, как опытный преподаватель, детальный обучающий материал по синтаксису языка {language} для дня {difficulty}. Ответ должен быть только текстом материала без дополнительных пояснений, без заключения и без указания дня.",
        f"Ты отлично разбираешься в синтаксисе языка {language}. Подготовь подробный обучающий материал для дня {difficulty}. Текст должен быть информативным и лаконичным, без излишеств, без заключения и без упоминания дня.",
        f"Как опытный преподаватель программирования, создай детальный обучающий материал по синтаксису языка {language} для дня {difficulty}. Не добавляй лишних комментариев и заключения, ответ должен содержать только основной текст материала.",
        f"Ты опытный учитель программирования. Составь подробный материал по синтаксису языка {language} для дня {difficulty}. Ответ должен включать только текст обучающего материала без лишних пояснений, без заключения и без указания дня.",
        f"В роли эксперта по программированию сформируй детальный обучающий материал по синтаксису {language} для дня {difficulty}. Твой ответ должен быть лаконичным и содержать только текст материала, без упоминания дня и без заключения.",
        f"Как опытный преподаватель, напиши подробный обучающий материал по синтаксису языка {language} для дня {difficulty}. Ответ должен быть исключительно текстом материала, без дополнительных комментариев, заключения и указания дня.",
        f"Будучи профессионалом в программировании, составь детальный материал по синтаксису {language} для дня {difficulty}. Твой ответ должен содержать только текст обучающего материала, без излишеств, без заключения и без упоминания номера дня."
    ]

    # Выбираем один случайный вариант
    prompt = random.choice(prompt_variants)
    # print(prompt)
    max_attempts = 30
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = giga.chat(prompt)
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            error_str = str(e)
            print(f"Попытка {attempt} для generate_material не удалась: {error_str}")
            if "429" in error_str:
                wait_time = 60
                match = re.search(r"Retry-After:\s*(\d+)", error_str)
                if match:
                    wait_time = int(match.group(1))
                print(f"Получен статус 429. Ждем {wait_time} секунд перед следующей попыткой...")
                time.sleep(wait_time)
            else:
                time.sleep(10)
    return f"Ошибка при генерации обучающего материала после {max_attempts} попыток: {last_error}"


def generate_questions(language, material, difficulty):
    prompt = (
        f"Ты опытный преподаватель программирования. "
        f"Составь тест из 15 вопросов для изучения синтаксиса языка {language} на основе материала {material} для дня {difficulty}. "
        "Первые 10 вопросов должны быть с 4 вариантами ответа (A, B, C, D) в формате:\n"
        "1. Вопрос\n"
        "   A) Вариант A\n"
        "   B) Вариант B\n"
        "   C) Вариант C\n"
        "   D) Вариант D\n\n"
        "Последние 5 вопросов с 11 по 15 должны быть практическими заданиями без вариантов ответа, "
        "где требуется написать небольшой фрагмент кода. "
        "Ответ должен содержать только текст теста без дополнительных комментариев."
    )
    max_attempts = 10
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = giga.chat(prompt)
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            error_str = str(e)
            print(f"Попытка {attempt} для generate_questions не удалась: {error_str}")
            if "429" in error_str:
                wait_time = 60
                match = re.search(r"Retry-After:\s*(\d+)", error_str)
                if match:
                    wait_time = int(match.group(1))
                print(f"Получен статус 429. Ждем {wait_time} секунд перед следующей попыткой...")
                time.sleep(wait_time)
            else:
                time.sleep(10)
    return f"Ошибка при генерации тестовых вопросов после {max_attempts} попыток: {last_error}"


def evaluate_answers(language, questions_with_answers):
    prompt = (
        f"Ты опытный преподаватель {language}. Проанализируй следующие ответы пользователя по тесту:\n\n"
        f"{questions_with_answers}\n\n"
        "Верни ответ строго в следующем формате (без лишних слов или комментариев):\n\n"
        "Количество правильных: <число> из 15\n"
        "Рекомендации: <текст рекомендаций>\n\n"
        "Где <число> – это целое число, отражающее количество правильных ответов, а <текст рекомендаций> – подробные рекомендации по вопросам, вежливо напиши и подбодри от первого лица, которые стоит доучить на основе неверных ответов."
    )
    max_attempts = 10
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = giga.chat(prompt)
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            error_str = str(e)
            print(f"Попытка {attempt} для evaluate_answers не удалась: {error_str}")
            if "429" in error_str:
                wait_time = 60
                match = re.search(r"Retry-After:\s*(\d+)", error_str)
                if match:
                    wait_time = int(match.group(1))
                print(f"Получен статус 429. Ждем {wait_time} секунд перед следующей попыткой...")
                time.sleep(wait_time)
            else:
                time.sleep(10)
    return f"Ошибка при проверке ответов после {max_attempts} попыток: {last_error}"


def evaluate_result(language, correct_percentage, incorrect_percentage):
    prompt_variants = [
        f"Ты опытный преподаватель {language}. Пользователь завершил тест по изучению синтаксиса {language} с результатом: {correct_percentage}% правильных ответов и {incorrect_percentage}% неправильных ответов. Поздравь его с завершением обучения, похвали за проделанную работу, даже если результат не идеален, и подбодри его. Дай подробные рекомендации по улучшению знаний. Верни ответ строго в следующем формате:\n\nКоличество правильных: <число>%\nРекомендации: <текст рекомендаций>.",
        f"Выполняй роль опытного преподавателя {language}. Пользователь завершил тест по синтаксису {language} и получил {correct_percentage}% правильных и {incorrect_percentage}% неправильных ответов. Пожалуйста, поздравь его, похвали за усилия, подбодри для дальнейшего обучения и дай рекомендации по темам, которые нужно доработать. Выведи ответ строго в следующем формате:\n\nКоличество правильных: <число>%\nРекомендации: <текст рекомендаций>.",
        f"Ты эксперт в преподавании {language}. Пользователь прошёл тест по синтаксису {language} с результатом: {correct_percentage}% правильных ответов и {incorrect_percentage}% неправильных ответов. Поздравь его с окончанием теста, похвали за проделанную работу даже если результат не идеален, и подбодри для дальнейшего изучения, предоставив рекомендации по улучшению знаний. Ответ должен быть выдан в формате:\n\nКоличество правильных: <число>%\nРекомендации: <текст рекомендаций>.",
        f"Представь, что ты опытный преподаватель {language}. Пользователь завершил тест по синтаксису {language} с результатом {correct_percentage}% правильных ответов и {incorrect_percentage}% ошибок. Поздравь его с окончанием теста, похвали за проделанную работу и подбодри для дальнейшего обучения, указав рекомендации по темам, требующим доработки. Верни ответ в следующем формате:\n\nКоличество правильных: <число>%\nРекомендации: <текст рекомендаций>.",
        f"Как опытный преподаватель {language}, проанализируй результаты теста пользователя по синтаксису {language}: {correct_percentage}% правильных ответов и {incorrect_percentage}% неправильных. Поздравь его с завершением обучения, отметь его усилия, даже если результат не совершенен, и предложи рекомендации по улучшению знаний. Ответ должен быть строго в формате:\n\nКоличество правильных: <число>%\nРекомендации: <текст рекомендаций>."
    ]

    # Выбираем один из пяти вариантов промта случайным образом
    prompt = random.choice(prompt_variants)

    max_attempts = 10
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = giga.chat(prompt)
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            error_str = str(e)
            print(f"Попытка {attempt} для evaluate_answers не удалась: {error_str}")
            if "429" in error_str:
                wait_time = 60
                match = re.search(r"Retry-After:\s*(\d+)", error_str)
                if match:
                    wait_time = int(match.group(1))
                print(f"Получен статус 429. Ждем {wait_time} секунд перед следующей попыткой...")
                time.sleep(wait_time)
            else:
                time.sleep(10)
    return f"Ошибка при проверке ответов после {max_attempts} попыток: {last_error}"

def clean_questions_text(text):
    """
    Очищает сгенерированный текст вопросов:
      - Удаляет строки-заголовки (начинающиеся с '#' или обрамлённые **).
      - Разбивает текст на блоки по двойному переносу строки.
      - Для каждого блока, если он начинается с номера вопроса:
          • Если номер вопроса ≤ 10, оставляет весь блок (вопрос и варианты ответов).
          • Если номер вопроса ≥ 11, оставляет только первую строку (текст вопроса).
    """
    # Удаляем строки, которые являются Markdown-заголовками или содержат только форматирование
    lines = text.splitlines()
    filtered_lines = []
    for line in lines:
        if re.match(r"^\s*#+\s*", line):  # строки, начинающиеся с #
            continue
        if re.match(r"^\*\*.*\*\*$", line.strip()):  # строки вида **...**
            continue
        filtered_lines.append(line)
    cleaned_text = "\n".join(filtered_lines).strip()

    # Разбиваем на блоки по двойному переносу строки
    blocks = re.split(r"\n\s*\n", cleaned_text)
    result_blocks = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Проверяем, что блок начинается с вопроса, например "1. ..."
        m = re.match(r"^(\d+)\.\s*(.*)", block, re.DOTALL)
        if not m:
            continue
        try:
            q_number = int(m.group(1))
        except ValueError:
            continue
        if q_number <= 10:
            # Для вопросов 1-10 оставляем весь блок (с вариантами)
            result_blocks.append(block)
        else:
            # Для вопросов 11-15 оставляем только первую строку
            first_line = block.splitlines()[0].strip()
            result_blocks.append(first_line)
    return "\n\n".join(result_blocks)


# Пример вызова функций
# if __name__ == "__main__":
    # print(evaluate_result('python','50','50'))
    # language = "Python"
    #     difficulty = 15
    #     material = generate_material(language, difficulty)
    #     print("=== Обучающий материал ===")
    #     print(material)
    #     questions = generate_questions(language, material, difficulty)
    #     questions = clean_questions_text(questions)
    # print("\n=== Тестовые вопросы ===")
    # # print(questions)
    # user_answers = """
    # {"1": {"question": "1. Какая директива препроцессора используется для подключения библиотеки ввода-вывода?", "answer": "A) `#import <iostream>`"}, "2": {"question": "2. Что делает функция `main()` в программе на C++?", "answer": "A) Возвращает результат вычислений"}, "3": {"question": "3. Какой оператор используется для вывода текста на экран?", "answer": "A) `cin`"}, "4": {"question": "4. Какой тип данных используется для хранения целых чисел?", "answer": "A) `string`"}, "5": {"question": "5. Какой оператор используется для сравнения двух значений на равенство?", "answer": "A) `==`"}, "6": {"question": "6. Какой цикл выполняется хотя бы один раз независимо от начального условия?", "answer": "A) `for`"}, "7": {"question": "7. Как правильно объявить переменную типа `float` и присвоить ей значение 3.14?", "answer": "B) `float pi = 3.14f;`"}, "8": {"question": "8. Как называется блок кода, который может быть вызван по имени и выполняет определенные задачи?", "answer": "B) Класс"}, "9": {"question": "9. Какой оператор используется для присваивания значения переменной?", "answer": "A) `:=`"}, "10": {"question": "10. Какой оператор используется для перевода строки после вывода текста?", "answer": "A) `\\n`"}, "11": {"question": "11. Напишите программу, которая выводит на экран числа от 1 до 10 с помощью цикла `for`.", "answer": "answers"}, "12": {"question": "12. Создайте функцию, которая принимает два целых числа и возвращает их сумму.", "answer": "answers"}, "13": {"question": "13. Напишите программу, которая запрашивает у пользователя его возраст и выводит сообщение \"Вы совершеннолетний\", если возраст больше или равен 18, иначе выводит \"Вы несовершеннолетний\".", "answer": "answers"}, "14": {"question": "14. Напишите программу, которая считает сумму всех четных чисел от 1 до 100.", "answer": "answers"}, "15": {"question": "15. Напишите программу, которая определяет, является ли введенное пользователем число простым.", "answer": "answers"}}
    # """
    # evaluation = evaluate_answers(language, user_answers)
    # print("\n=== Результаты теста ===")
    # print(evaluation)
