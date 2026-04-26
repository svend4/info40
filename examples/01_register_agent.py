"""
Пример 1: Регистрация агента в системе оркестрации

Этот скрипт демонстрирует, как владелец агента может зарегистрировать
своего агента в платформе и начать принимать задачи.
"""

import asyncio
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum


class PricingMode(Enum):
    """Модель ценообразования"""
    COMMERCIAL = "commercial"  # Только коммерческая аренда
    VOLUNTEER = "volunteer"    # Только волонтерские проекты
    HYBRID = "hybrid"          # Гибридная модель


@dataclass
class AgentConfig:
    """Конфигурация агента"""
    name: str
    description: str
    capabilities: list[str]
    model: str = "claude-sonnet-4.5"

    # Ценообразование
    pricing_mode: PricingMode = PricingMode.COMMERCIAL
    hourly_rate: float = 0.0
    volunteer_percentage: int = 0  # % времени на волонтерство (для hybrid)

    # Доступность
    max_concurrent_tasks: int = 1
    schedule: str = "24/7"

    # Ограничения ресурсов
    max_execution_time: int = 3600  # секунды
    memory_limit: str = "2Gi"


class AgentPlatformClient:
    """Клиент для взаимодействия с платформой оркестрации"""

    def __init__(self, platform_url: str, api_key: str):
        self.platform_url = platform_url
        self.api_key = api_key
        self.agent_id = None

    async def register_agent(self, config: AgentConfig) -> str:
        """
        Регистрирует агента на платформе

        Args:
            config: Конфигурация агента

        Returns:
            agent_id: Уникальный идентификатор агента
        """
        # В реальной реализации здесь был бы HTTP POST запрос
        print(f"🔄 Регистрация агента '{config.name}'...")

        # Симуляция API запроса
        await asyncio.sleep(0.5)

        # Генерация ID агента
        import uuid
        self.agent_id = str(uuid.uuid4())

        print(f"✅ Агент успешно зарегистрирован!")
        print(f"   Agent ID: {self.agent_id}")
        print(f"   Capabilities: {', '.join(config.capabilities)}")
        print(f"   Pricing: {config.pricing_mode.value}")

        if config.pricing_mode in [PricingMode.COMMERCIAL, PricingMode.HYBRID]:
            print(f"   Rate: ${config.hourly_rate}/час")

        if config.pricing_mode == PricingMode.HYBRID:
            print(f"   Волонтерство: {config.volunteer_percentage}%")

        return self.agent_id

    async def listen_for_tasks(self, executor_function):
        """
        Слушает входящие задачи и выполняет их

        Args:
            executor_function: Функция для выполнения задач
        """
        print(f"\n👂 Агент {self.agent_id[:8]}... ожидает задачи...")

        # В реальной реализации это был бы WebSocket или long polling
        task_count = 0
        while task_count < 3:  # Для примера выполним 3 задачи
            await asyncio.sleep(2)

            # Симуляция получения задачи
            task = await self._fetch_next_task()

            if task:
                task_count += 1
                print(f"\n📥 Получена задача #{task_count}: {task['description']}")

                try:
                    # Выполнение задачи
                    result = await executor_function(task)

                    # Отправка результата
                    await self._submit_result(task['id'], result)
                    print(f"✅ Задача #{task_count} выполнена успешно")

                except Exception as e:
                    await self._report_error(task['id'], str(e))
                    print(f"❌ Ошибка при выполнении задачи #{task_count}: {e}")

        print(f"\n🏁 Завершено выполнение {task_count} задач")

    async def _fetch_next_task(self) -> Dict[str, Any]:
        """Получает следующую задачу из очереди"""
        # Симуляция задач
        tasks = [
            {
                "id": "task-001",
                "description": "Написать функцию сортировки списка",
                "type": "coding",
                "language": "python",
                "prompt": "Напиши функцию quick_sort для сортировки списка целых чисел"
            },
            {
                "id": "task-002",
                "description": "Code review функции",
                "type": "code_review",
                "code": "def add(a, b):\n    return a + b",
                "prompt": "Проверь этот код на наличие проблем"
            },
            {
                "id": "task-003",
                "description": "Написать unit-тесты",
                "type": "testing",
                "language": "python",
                "prompt": "Напиши unit-тесты для функции fibonacci(n)"
            }
        ]

        import random
        return random.choice(tasks)

    async def _submit_result(self, task_id: str, result: Any):
        """Отправляет результат выполнения задачи"""
        # В реальной реализации - HTTP POST
        await asyncio.sleep(0.3)

    async def _report_error(self, task_id: str, error: str):
        """Сообщает об ошибке при выполнении задачи"""
        # В реальной реализации - HTTP POST
        await asyncio.sleep(0.3)


# ============================================================================
# Пример использования
# ============================================================================

async def my_agent_executor(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Пользовательская функция для выполнения задач

    Здесь владелец агента реализует логику своего агента.
    Это может быть вызов Claude API, локальная LLM, или любая другая логика.
    """
    print(f"   ⚙️  Обработка задачи типа '{task['type']}'...")

    # Симуляция работы агента
    await asyncio.sleep(1)

    # В реальности здесь был бы вызов AI API
    if task['type'] == 'coding':
        result = {
            "code": """
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)
            """.strip(),
            "explanation": "Реализация алгоритма быстрой сортировки"
        }

    elif task['type'] == 'code_review':
        result = {
            "issues": [],
            "suggestions": [
                "Добавить docstring",
                "Добавить проверку типов аргументов"
            ],
            "rating": "good"
        }

    elif task['type'] == 'testing':
        result = {
            "tests": """
import unittest

class TestFibonacci(unittest.TestCase):
    def test_base_cases(self):
        self.assertEqual(fibonacci(0), 0)
        self.assertEqual(fibonacci(1), 1)

    def test_sequence(self):
        self.assertEqual(fibonacci(5), 5)
        self.assertEqual(fibonacci(10), 55)
            """.strip()
        }

    else:
        result = {"status": "unknown_task_type"}

    return result


async def main():
    """Главная функция"""

    print("=" * 70)
    print("  ПРИМЕР 1: РЕГИСТРАЦИЯ АГЕНТА")
    print("=" * 70)

    # 1. Создаем конфигурацию агента
    agent_config = AgentConfig(
        name="PythonExpertAgent",
        description="Специализируется на Python разработке, code review и тестировании",
        capabilities=[
            "python_coding",
            "code_review",
            "unit_testing",
            "debugging"
        ],
        model="claude-sonnet-4.5",
        pricing_mode=PricingMode.HYBRID,
        hourly_rate=25.0,
        volunteer_percentage=20,  # 20% времени - волонтерство
        max_concurrent_tasks=3
    )

    # 2. Создаем клиент для работы с платформой
    client = AgentPlatformClient(
        platform_url="https://agent-platform.example.com",
        api_key="your_api_key_here"
    )

    # 3. Регистрируем агента
    agent_id = await client.register_agent(agent_config)

    # 4. Начинаем слушать и выполнять задачи
    await client.listen_for_tasks(my_agent_executor)

    print("\n" + "=" * 70)
    print("  Агент остановлен")
    print("=" * 70)


if __name__ == "__main__":
    # Запуск примера
    asyncio.run(main())
