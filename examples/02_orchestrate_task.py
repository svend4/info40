"""
Пример 2: Оркестрация мультиагентной задачи

Этот скрипт демонстрирует, как заказчик может создать сложную задачу,
которая будет автоматически разбита на подзадачи и распределена между
несколькими специализированными агентами.
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta


class TaskStatus(Enum):
    """Статус задачи"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Priority(Enum):
    """Приоритет задачи"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SubTask:
    """Подзадача"""
    id: str
    description: str
    required_capability: str
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    estimated_time: int = 60  # секунды
    estimated_cost: float = 0.0


@dataclass
class TaskRequest:
    """Запрос на выполнение задачи"""
    title: str
    description: str
    required_capabilities: List[str]
    budget: Optional[float] = None
    deadline: Optional[datetime] = None
    priority: Priority = Priority.NORMAL


@dataclass
class AgentInfo:
    """Информация об агенте"""
    id: str
    name: str
    capabilities: List[str]
    hourly_rate: float
    success_rate: float
    avg_response_time: int
    current_load: int  # количество активных задач


class TaskOrchestrator:
    """Оркестратор для управления мультиагентными задачами"""

    def __init__(self, platform_url: str, api_key: str):
        self.platform_url = platform_url
        self.api_key = api_key
        self.available_agents: List[AgentInfo] = []

    async def create_task(self, task_request: TaskRequest) -> str:
        """
        Создает новую задачу и автоматически разбивает ее на подзадачи

        Args:
            task_request: Описание задачи

        Returns:
            task_id: Идентификатор созданной задачи
        """
        print(f"\n{'='*70}")
        print(f"  СОЗДАНИЕ ЗАДАЧИ: {task_request.title}")
        print(f"{'='*70}\n")

        # 1. Декомпозиция задачи
        print("🔍 Этап 1: Анализ и декомпозиция задачи...")
        subtasks = await self._decompose_task(task_request)
        print(f"   ✅ Задача разбита на {len(subtasks)} подзадач\n")

        # 2. Поиск доступных агентов
        print("🔍 Этап 2: Поиск доступных агентов...")
        await self._fetch_available_agents()
        print(f"   ✅ Найдено {len(self.available_agents)} доступных агентов\n")

        # 3. Подбор агентов для подзадач
        print("🔍 Этап 3: Подбор агентов для подзадач...")
        await self._allocate_agents(subtasks, task_request.budget)
        print(f"   ✅ Агенты назначены на все подзадачи\n")

        # 4. Вывод информации
        self._print_task_plan(subtasks, task_request)

        # 5. Запуск выполнения
        task_id = f"task-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        print(f"\n📋 Task ID: {task_id}")

        return task_id

    async def execute_task(self, task_id: str, subtasks: List[SubTask]) -> Dict[str, Any]:
        """
        Выполняет задачу, координируя работу агентов

        Args:
            task_id: ID задачи
            subtasks: Список подзадач

        Returns:
            Агрегированный результат
        """
        print(f"\n{'='*70}")
        print(f"  ВЫПОЛНЕНИЕ ЗАДАЧИ: {task_id}")
        print(f"{'='*70}\n")

        results = {}
        execution_graph = self._build_execution_graph(subtasks)

        # Выполняем задачи согласно зависимостям
        for level, tasks_at_level in enumerate(execution_graph):
            print(f"\n🔄 Уровень {level + 1}: Выполнение {len(tasks_at_level)} задач(и) параллельно...")

            # Параллельное выполнение задач на одном уровне
            level_results = await asyncio.gather(
                *[self._execute_subtask(task, results) for task in tasks_at_level]
            )

            # Сохраняем результаты
            for task, result in zip(tasks_at_level, level_results):
                results[task.id] = result
                task.result = result
                task.status = TaskStatus.COMPLETED

        print(f"\n✅ Все подзадачи выполнены!")

        # Агрегация результатов
        final_result = await self._aggregate_results(subtasks, results)

        return final_result

    async def _decompose_task(self, task_request: TaskRequest) -> List[SubTask]:
        """
        Разбивает задачу на подзадачи используя AI

        В реальной реализации здесь был бы вызов Claude/GPT для анализа задачи
        """
        await asyncio.sleep(0.5)  # Симуляция AI-анализа

        # Для примера используем предопределенную декомпозицию
        if "научная статья" in task_request.description.lower():
            return [
                SubTask(
                    id="subtask-1",
                    description="Провести литературный обзор по теме",
                    required_capability="research",
                    dependencies=[],
                    estimated_time=7200,
                    estimated_cost=60.0
                ),
                SubTask(
                    id="subtask-2",
                    description="Анализ собранных данных",
                    required_capability="data_analysis",
                    dependencies=["subtask-1"],
                    estimated_time=3600,
                    estimated_cost=45.0
                ),
                SubTask(
                    id="subtask-3",
                    description="Написание текста статьи",
                    required_capability="scientific_writing",
                    dependencies=["subtask-2"],
                    estimated_time=10800,
                    estimated_cost=90.0
                ),
                SubTask(
                    id="subtask-4",
                    description="Проверка фактов и ссылок",
                    required_capability="fact_verification",
                    dependencies=["subtask-3"],
                    estimated_time=1800,
                    estimated_cost=30.0
                ),
                SubTask(
                    id="subtask-5",
                    description="Редактирование и форматирование",
                    required_capability="editing",
                    dependencies=["subtask-4"],
                    estimated_time=1800,
                    estimated_cost=25.0
                )
            ]
        elif "веб-приложение" in task_request.description.lower():
            return [
                SubTask(
                    id="subtask-1",
                    description="Проектирование архитектуры",
                    required_capability="architecture",
                    dependencies=[],
                    estimated_time=3600,
                    estimated_cost=100.0
                ),
                SubTask(
                    id="subtask-2",
                    description="Разработка backend API",
                    required_capability="backend_development",
                    dependencies=["subtask-1"],
                    estimated_time=14400,
                    estimated_cost=360.0
                ),
                SubTask(
                    id="subtask-3",
                    description="Разработка frontend",
                    required_capability="frontend_development",
                    dependencies=["subtask-1"],
                    estimated_time=14400,
                    estimated_cost=360.0
                ),
                SubTask(
                    id="subtask-4",
                    description="Интеграция frontend и backend",
                    required_capability="full_stack",
                    dependencies=["subtask-2", "subtask-3"],
                    estimated_time=3600,
                    estimated_cost=90.0
                ),
                SubTask(
                    id="subtask-5",
                    description="Написание тестов",
                    required_capability="testing",
                    dependencies=["subtask-4"],
                    estimated_time=5400,
                    estimated_cost=135.0
                )
            ]
        else:
            # Простая задача - одна подзадача
            return [
                SubTask(
                    id="subtask-1",
                    description=task_request.description,
                    required_capability=task_request.required_capabilities[0],
                    dependencies=[],
                    estimated_time=3600,
                    estimated_cost=50.0
                )
            ]

    async def _fetch_available_agents(self):
        """Получает список доступных агентов"""
        await asyncio.sleep(0.3)

        # Симуляция агентов в системе
        self.available_agents = [
            AgentInfo("agent-001", "ResearchBot", ["research"], 8.0, 0.95, 300, 1),
            AgentInfo("agent-002", "DataAnalyst", ["data_analysis"], 15.0, 0.92, 450, 0),
            AgentInfo("agent-003", "ScientificWriter", ["scientific_writing"], 10.0, 0.88, 600, 2),
            AgentInfo("agent-004", "FactChecker", ["fact_verification"], 12.0, 0.97, 200, 0),
            AgentInfo("agent-005", "EditorPro", ["editing"], 8.0, 0.93, 350, 1),
            AgentInfo("agent-006", "ArchitectMaster", ["architecture"], 25.0, 0.96, 400, 0),
            AgentInfo("agent-007", "BackendDev", ["backend_development"], 30.0, 0.91, 500, 1),
            AgentInfo("agent-008", "FrontendDev", ["frontend_development"], 28.0, 0.89, 480, 2),
            AgentInfo("agent-009", "FullStackDev", ["full_stack"], 35.0, 0.90, 520, 0),
            AgentInfo("agent-010", "QAEngineer", ["testing"], 20.0, 0.94, 300, 1),
        ]

    async def _allocate_agents(self, subtasks: List[SubTask], budget: Optional[float]):
        """
        Подбирает оптимальных агентов для каждой подзадачи

        Алгоритм учитывает:
        - Соответствие capabilities
        - Стоимость
        - Историю успешности
        - Текущую нагрузку
        - Бюджет проекта
        """
        await asyncio.sleep(0.4)

        for subtask in subtasks:
            # Найти агентов с нужной capability
            candidates = [
                agent for agent in self.available_agents
                if subtask.required_capability in agent.capabilities
            ]

            if not candidates:
                raise ValueError(f"Нет доступных агентов для capability: {subtask.required_capability}")

            # Ранжирование агентов по fitness score
            ranked = sorted(
                candidates,
                key=lambda a: self._calculate_fitness_score(a, subtask),
                reverse=True
            )

            # Выбираем лучшего
            best_agent = ranked[0]
            subtask.assigned_agent = best_agent.id
            subtask.estimated_cost = (subtask.estimated_time / 3600) * best_agent.hourly_rate

    def _calculate_fitness_score(self, agent: AgentInfo, subtask: SubTask) -> float:
        """
        Вычисляет score соответствия агента задаче

        Формула учитывает:
        - Success rate (40%)
        - Скорость ответа (30%)
        - Текущая нагрузка (20%)
        - Стоимость (10%)
        """
        # Нормализованные метрики (0-1)
        success_score = agent.success_rate
        speed_score = 1.0 - min(agent.avg_response_time / 1000, 1.0)
        load_score = 1.0 - min(agent.current_load / 5, 1.0)
        cost_score = 1.0 - min(agent.hourly_rate / 50, 1.0)

        # Взвешенная сумма
        fitness = (
            success_score * 0.4 +
            speed_score * 0.3 +
            load_score * 0.2 +
            cost_score * 0.1
        )

        return fitness

    def _build_execution_graph(self, subtasks: List[SubTask]) -> List[List[SubTask]]:
        """
        Строит граф выполнения с учетом зависимостей

        Возвращает список уровней, где задачи на одном уровне
        могут выполняться параллельно
        """
        levels = []
        completed = set()

        while len(completed) < len(subtasks):
            # Найти задачи, которые можно выполнить на этом уровне
            current_level = [
                task for task in subtasks
                if task.id not in completed and
                   all(dep in completed for dep in task.dependencies)
            ]

            if not current_level:
                raise ValueError("Циклические зависимости в графе задач!")

            levels.append(current_level)
            completed.update(task.id for task in current_level)

        return levels

    async def _execute_subtask(self, subtask: SubTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет подзадачу с использованием назначенного агента"""
        agent = next(a for a in self.available_agents if a.id == subtask.assigned_agent)

        print(f"   ⚙️  [{subtask.id}] {subtask.description}")
        print(f"      Агент: {agent.name} (${agent.hourly_rate}/ч)")

        subtask.status = TaskStatus.RUNNING

        # Симуляция выполнения (в реальности - вызов агента)
        execution_time = subtask.estimated_time / 10  # Ускоряем для примера
        await asyncio.sleep(execution_time)

        # Симуляция результата
        result = {
            "subtask_id": subtask.id,
            "status": "success",
            "data": f"Результат выполнения задачи: {subtask.description}",
            "agent": agent.name,
            "execution_time": execution_time
        }

        print(f"      ✅ Завершено за {execution_time:.1f}с")

        return result

    async def _aggregate_results(self, subtasks: List[SubTask], results: Dict[str, Any]) -> Dict[str, Any]:
        """Агрегирует результаты всех подзадач"""
        total_cost = sum(task.estimated_cost for task in subtasks)
        total_time = sum(task.estimated_time for task in subtasks)

        return {
            "status": "completed",
            "subtasks_completed": len(subtasks),
            "total_cost": total_cost,
            "total_time_seconds": total_time,
            "results": results
        }

    def _print_task_plan(self, subtasks: List[SubTask], task_request: TaskRequest):
        """Выводит план выполнения задачи"""
        print("📊 План выполнения:\n")

        total_cost = sum(task.estimated_cost for task in subtasks)
        total_time = sum(task.estimated_time for task in subtasks)

        for i, task in enumerate(subtasks, 1):
            agent = next(a for a in self.available_agents if a.id == task.assigned_agent)
            deps = f" (зависит от: {', '.join(task.dependencies)})" if task.dependencies else ""

            print(f"   {i}. {task.description}{deps}")
            print(f"      Агент: {agent.name}")
            print(f"      Время: {task.estimated_time // 60} мин")
            print(f"      Стоимость: ${task.estimated_cost:.2f}")
            print()

        print(f"   📈 Итого:")
        print(f"      Подзадач: {len(subtasks)}")
        print(f"      Время: ~{total_time // 3600}ч {(total_time % 3600) // 60}м")
        print(f"      Стоимость: ${total_cost:.2f}")

        if task_request.budget:
            if total_cost <= task_request.budget:
                print(f"      ✅ В рамках бюджета (${task_request.budget:.2f})")
            else:
                print(f"      ⚠️  Превышает бюджет на ${total_cost - task_request.budget:.2f}")


# ============================================================================
# Пример использования
# ============================================================================

async def example_scientific_paper():
    """Пример: Создание научной статьи"""

    orchestrator = TaskOrchestrator(
        platform_url="https://agent-platform.example.com",
        api_key="your_api_key"
    )

    # Создаем задачу
    task_request = TaskRequest(
        title="Научная статья об изменении климата",
        description="Создать научную статью о влиянии изменения климата на биоразнообразие океанов (2020-2026)",
        required_capabilities=[
            "research",
            "data_analysis",
            "scientific_writing",
            "fact_verification",
            "editing"
        ],
        budget=300.0,
        deadline=datetime.now() + timedelta(days=7),
        priority=Priority.HIGH
    )

    # Создаем и планируем задачу
    task_id = await orchestrator.create_task(task_request)

    # Получаем подзадачи для выполнения
    subtasks = await orchestrator._decompose_task(task_request)
    await orchestrator._fetch_available_agents()
    await orchestrator._allocate_agents(subtasks, task_request.budget)

    # Выполняем задачу
    result = await orchestrator.execute_task(task_id, subtasks)

    # Выводим результат
    print(f"\n{'='*70}")
    print(f"  РЕЗУЛЬТАТЫ")
    print(f"{'='*70}\n")
    print(f"   Статус: {result['status']}")
    print(f"   Выполнено подзадач: {result['subtasks_completed']}")
    print(f"   Общая стоимость: ${result['total_cost']:.2f}")
    print(f"   Общее время: {result['total_time_seconds'] // 3600}ч")


async def example_web_app():
    """Пример: Разработка веб-приложения"""

    orchestrator = TaskOrchestrator(
        platform_url="https://agent-platform.example.com",
        api_key="your_api_key"
    )

    task_request = TaskRequest(
        title="E-commerce веб-приложение",
        description="Разработать веб-приложение для онлайн-магазина с каталогом товаров и корзиной",
        required_capabilities=[
            "architecture",
            "backend_development",
            "frontend_development",
            "full_stack",
            "testing"
        ],
        budget=1200.0,
        priority=Priority.NORMAL
    )

    task_id = await orchestrator.create_task(task_request)

    subtasks = await orchestrator._decompose_task(task_request)
    await orchestrator._fetch_available_agents()
    await orchestrator._allocate_agents(subtasks, task_request.budget)

    result = await orchestrator.execute_task(task_id, subtasks)

    print(f"\n{'='*70}")
    print(f"  РЕЗУЛЬТАТЫ")
    print(f"{'='*70}\n")
    print(f"   ✅ Веб-приложение готово!")
    print(f"   Стоимость: ${result['total_cost']:.2f}")


async def main():
    """Главная функция"""

    print("\n" + "="*70)
    print("  ПРИМЕРЫ ОРКЕСТРАЦИИ МУЛЬТИАГЕНТНЫХ ЗАДАЧ")
    print("="*70)

    # Пример 1: Научная статья
    print("\n\n📚 ПРИМЕР 1: СОЗДАНИЕ НАУЧНОЙ СТАТЬИ\n")
    await example_scientific_paper()

    print("\n\n" + "="*70 + "\n")

    # Пример 2: Веб-приложение
    print("\n\n💻 ПРИМЕР 2: РАЗРАБОТКА ВЕБ-ПРИЛОЖЕНИЯ\n")
    await example_web_app()


if __name__ == "__main__":
    asyncio.run(main())
