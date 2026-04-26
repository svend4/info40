"""
Пример 3: Работа с Marketplace агентов

Этот скрипт демонстрирует:
1. Поиск агентов в marketplace
2. Аренда агентов (коммерческая и волонтерская)
3. Система рейтингов и отзывов
4. Биллинг и оплата
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import random


class RentalMode(Enum):
    """Режим аренды агента"""
    COMMERCIAL = "commercial"  # Коммерческая аренда
    VOLUNTEER = "volunteer"    # Волонтерский проект
    TRIAL = "trial"            # Пробный период


class BillingModel(Enum):
    """Модель биллинга"""
    HOURLY = "hourly"          # Почасовая оплата
    PER_TASK = "per_task"      # За задачу
    SUBSCRIPTION = "subscription"  # Подписка
    OUTCOME_BASED = "outcome_based"  # По результату


@dataclass
class AgentListing:
    """Объявление об агенте в marketplace"""
    id: str
    owner_id: str
    name: str
    description: str
    capabilities: List[str]
    model: str

    # Ценообразование
    billing_model: BillingModel
    hourly_rate: Optional[float] = None
    task_rate: Optional[float] = None
    subscription_monthly: Optional[float] = None

    # Метрики производительности
    total_tasks_completed: int = 0
    success_rate: float = 0.0
    avg_response_time: int = 0  # секунды
    avg_quality_score: float = 0.0  # 0-5

    # Рейтинг
    rating: float = 0.0  # 0-5
    reviews_count: int = 0

    # Доступность
    available: bool = True
    max_concurrent_tasks: int = 1
    current_load: int = 0

    # Волонтерство
    volunteer_enabled: bool = False
    volunteer_projects: List[str] = field(default_factory=list)


@dataclass
class Review:
    """Отзыв об агенте"""
    agent_id: str
    user_id: str
    rating: float  # 1-5
    comment: str
    task_type: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RentalContract:
    """Контракт аренды агента"""
    contract_id: str
    agent_id: str
    customer_id: str
    rental_mode: RentalMode
    billing_model: BillingModel

    start_time: datetime
    end_time: Optional[datetime] = None

    # Биллинг
    rate: float = 0.0
    total_time_seconds: int = 0
    total_cost: float = 0.0
    paid: bool = False

    # Метаданные
    task_description: str = ""
    project_name: str = ""


class MarketplaceClient:
    """Клиент для работы с marketplace агентов"""

    def __init__(self, platform_url: str, api_key: str):
        self.platform_url = platform_url
        self.api_key = api_key
        self.agents: List[AgentListing] = []

    async def search_agents(
        self,
        capabilities: Optional[List[str]] = None,
        max_hourly_rate: Optional[float] = None,
        min_rating: float = 0.0,
        min_success_rate: float = 0.0,
        volunteer_only: bool = False
    ) -> List[AgentListing]:
        """
        Поиск агентов в marketplace по критериям

        Args:
            capabilities: Требуемые возможности
            max_hourly_rate: Максимальная ставка
            min_rating: Минимальный рейтинг
            min_success_rate: Минимальный % успешных задач
            volunteer_only: Только волонтерские агенты

        Returns:
            Список подходящих агентов
        """
        print(f"🔍 Поиск агентов в marketplace...")
        print(f"   Критерии:")

        if capabilities:
            print(f"   - Capabilities: {', '.join(capabilities)}")
        if max_hourly_rate:
            print(f"   - Макс. ставка: ${max_hourly_rate}/ч")
        if min_rating:
            print(f"   - Мин. рейтинг: {min_rating}/5")
        if min_success_rate:
            print(f"   - Мин. success rate: {min_success_rate*100}%")
        if volunteer_only:
            print(f"   - Только волонтерские")

        # Симуляция API запроса
        await asyncio.sleep(0.5)

        # Загружаем всех агентов (в реале - фильтрация на сервере)
        await self._load_agents()

        # Фильтрация
        results = self.agents

        if capabilities:
            results = [
                a for a in results
                if any(cap in a.capabilities for cap in capabilities)
            ]

        if max_hourly_rate:
            results = [
                a for a in results
                if a.hourly_rate and a.hourly_rate <= max_hourly_rate
            ]

        if min_rating:
            results = [a for a in results if a.rating >= min_rating]

        if min_success_rate:
            results = [a for a in results if a.success_rate >= min_success_rate]

        if volunteer_only:
            results = [a for a in results if a.volunteer_enabled]

        # Сортировка по рейтингу и цене
        results.sort(
            key=lambda a: (-a.rating, a.hourly_rate or 999),
        )

        print(f"\n   ✅ Найдено {len(results)} агентов\n")

        return results

    async def rent_agent(
        self,
        agent_id: str,
        rental_mode: RentalMode,
        task_description: str,
        project_name: str = ""
    ) -> RentalContract:
        """
        Арендует агента для выполнения задач

        Args:
            agent_id: ID агента
            rental_mode: Режим аренды
            task_description: Описание задачи
            project_name: Название проекта (для волонтерства)

        Returns:
            Контракт аренды
        """
        agent = next((a for a in self.agents if a.id == agent_id), None)
        if not agent:
            raise ValueError(f"Агент {agent_id} не найден")

        print(f"\n📝 Аренда агента: {agent.name}")
        print(f"   Режим: {rental_mode.value}")

        # Проверка доступности для волонтерства
        if rental_mode == RentalMode.VOLUNTEER:
            if not agent.volunteer_enabled:
                raise ValueError(f"Агент {agent.name} не поддерживает волонтерские проекты")
            print(f"   ✅ Волонтерский проект: {project_name}")
            rate = 0.0
        else:
            rate = agent.hourly_rate or 0.0
            print(f"   Ставка: ${rate}/час")

        # Создание контракта
        contract = RentalContract(
            contract_id=f"contract-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            agent_id=agent_id,
            customer_id="user-123",  # В реале - из auth
            rental_mode=rental_mode,
            billing_model=agent.billing_model,
            start_time=datetime.now(),
            rate=rate,
            task_description=task_description,
            project_name=project_name
        )

        # Симуляция создания контракта
        await asyncio.sleep(0.3)

        print(f"   ✅ Контракт создан: {contract.contract_id}\n")

        return contract

    async def end_rental(self, contract: RentalContract) -> float:
        """
        Завершает аренду и вычисляет стоимость

        Args:
            contract: Контракт аренды

        Returns:
            Итоговая стоимость
        """
        contract.end_time = datetime.now()
        duration = contract.end_time - contract.start_time
        contract.total_time_seconds = int(duration.total_seconds())

        # Вычисление стоимости
        if contract.rental_mode == RentalMode.VOLUNTEER:
            contract.total_cost = 0.0
        elif contract.billing_model == BillingModel.HOURLY:
            hours = contract.total_time_seconds / 3600
            contract.total_cost = hours * contract.rate
        elif contract.billing_model == BillingModel.PER_TASK:
            contract.total_cost = contract.rate

        print(f"\n💰 Завершение аренды: {contract.contract_id}")
        print(f"   Длительность: {contract.total_time_seconds // 60} минут")
        print(f"   Стоимость: ${contract.total_cost:.2f}")

        return contract.total_cost

    async def submit_review(
        self,
        agent_id: str,
        rating: float,
        comment: str,
        task_type: str
    ):
        """
        Оставляет отзыв об агенте

        Args:
            agent_id: ID агента
            rating: Оценка 1-5
            comment: Комментарий
            task_type: Тип задачи
        """
        review = Review(
            agent_id=agent_id,
            user_id="user-123",
            rating=rating,
            comment=comment,
            task_type=task_type
        )

        print(f"\n⭐ Отзыв отправлен:")
        print(f"   Агент: {agent_id}")
        print(f"   Оценка: {rating}/5")
        print(f"   Комментарий: {comment}")

        # Симуляция отправки
        await asyncio.sleep(0.3)

        # Обновление рейтинга агента
        agent = next(a for a in self.agents if a.id == agent_id)
        total_rating = agent.rating * agent.reviews_count + rating
        agent.reviews_count += 1
        agent.rating = total_rating / agent.reviews_count

        print(f"   ✅ Новый рейтинг агента: {agent.rating:.2f}/5")

    async def get_agent_reviews(self, agent_id: str, limit: int = 5) -> List[Review]:
        """Получает отзывы об агенте"""
        # Симуляция загрузки отзывов
        await asyncio.sleep(0.2)

        # Генерируем примеры отзывов
        reviews = [
            Review(
                agent_id=agent_id,
                user_id=f"user-{i}",
                rating=random.uniform(3.5, 5.0),
                comment=random.choice([
                    "Отличная работа, рекомендую!",
                    "Быстро и качественно",
                    "Хороший результат, но долго",
                    "Превосходное качество кода",
                    "Агент справился на отлично"
                ]),
                task_type=random.choice(["coding", "research", "writing"]),
                created_at=datetime.now() - timedelta(days=random.randint(1, 30))
            )
            for i in range(limit)
        ]

        return reviews

    async def _load_agents(self):
        """Загружает список агентов из marketplace"""
        # Симуляция загрузки
        await asyncio.sleep(0.3)

        self.agents = [
            AgentListing(
                id="agent-001",
                owner_id="owner-1",
                name="PythonMaster",
                description="Эксперт в Python разработке",
                capabilities=["python_coding", "code_review", "debugging"],
                model="claude-sonnet-4.5",
                billing_model=BillingModel.HOURLY,
                hourly_rate=30.0,
                total_tasks_completed=156,
                success_rate=0.95,
                avg_response_time=420,
                rating=4.8,
                reviews_count=42,
                volunteer_enabled=True,
                volunteer_projects=["opensource", "education"]
            ),
            AgentListing(
                id="agent-002",
                owner_id="owner-2",
                name="DataSciencePro",
                description="Анализ данных и машинное обучение",
                capabilities=["data_analysis", "machine_learning", "visualization"],
                model="claude-opus-4.5",
                billing_model=BillingModel.HOURLY,
                hourly_rate=45.0,
                total_tasks_completed=89,
                success_rate=0.92,
                avg_response_time=600,
                rating=4.6,
                reviews_count=28,
                volunteer_enabled=True,
                volunteer_projects=["science", "research"]
            ),
            AgentListing(
                id="agent-003",
                owner_id="owner-3",
                name="ContentWriter",
                description="Копирайтинг и редактирование",
                capabilities=["writing", "editing", "copywriting"],
                model="claude-sonnet-4.5",
                billing_model=BillingModel.PER_TASK,
                task_rate=50.0,
                total_tasks_completed=234,
                success_rate=0.88,
                avg_response_time=300,
                rating=4.5,
                reviews_count=67,
                volunteer_enabled=False
            ),
            AgentListing(
                id="agent-004",
                owner_id="owner-4",
                name="ResearchBot",
                description="Научные исследования и литературный обзор",
                capabilities=["research", "fact_verification", "scientific_writing"],
                model="claude-opus-4.5",
                billing_model=BillingModel.HOURLY,
                hourly_rate=35.0,
                total_tasks_completed=112,
                success_rate=0.97,
                avg_response_time=900,
                rating=4.9,
                reviews_count=31,
                volunteer_enabled=True,
                volunteer_projects=["science", "education", "opensource"]
            ),
            AgentListing(
                id="agent-005",
                owner_id="owner-1",
                name="BudgetCoder",
                description="Доступная разработка для стартапов",
                capabilities=["python_coding", "web_development"],
                model="claude-haiku-4",
                billing_model=BillingModel.HOURLY,
                hourly_rate=15.0,
                total_tasks_completed=45,
                success_rate=0.82,
                avg_response_time=500,
                rating=4.1,
                reviews_count=15,
                volunteer_enabled=True,
                volunteer_projects=["opensource", "education"]
            ),
        ]

    def display_agent(self, agent: AgentListing):
        """Красиво выводит информацию об агенте"""
        print(f"\n┌{'─'*68}┐")
        print(f"│ {agent.name:<66} │")
        print(f"├{'─'*68}┤")
        print(f"│ ID: {agent.id:<62} │")
        print(f"│ Модель: {agent.model:<58} │")
        print(f"│                                                                    │")
        print(f"│ 📋 Capabilities: {', '.join(agent.capabilities[:2]):<48} │")
        if len(agent.capabilities) > 2:
            print(f"│    {', '.join(agent.capabilities[2:]):<65} │")
        print(f"│                                                                    │")
        print(f"│ ⭐ Рейтинг: {agent.rating:.1f}/5  ({agent.reviews_count} отзывов){'':>37} │")
        print(f"│ ✅ Success rate: {agent.success_rate*100:.0f}%{'':>49} │")
        print(f"│ ⚡ Ср. время ответа: {agent.avg_response_time}с{'':>43} │")
        print(f"│ 📊 Выполнено задач: {agent.total_tasks_completed:<46} │")
        print(f"│                                                                    │")

        if agent.billing_model == BillingModel.HOURLY:
            print(f"│ 💰 Стоимость: ${agent.hourly_rate}/час{'':>45} │")
        elif agent.billing_model == BillingModel.PER_TASK:
            print(f"│ 💰 Стоимость: ${agent.task_rate}/задача{'':>41} │")

        if agent.volunteer_enabled:
            print(f"│ 🤝 Волонтерство: Да  (проекты: {', '.join(agent.volunteer_projects[:2])}){'':>10} │")
        else:
            print(f"│ 🤝 Волонтерство: Нет{'':>49} │")

        print(f"│                                                                    │")
        print(f"│ {agent.description:<66} │")
        print(f"└{'─'*68}┘")


# ============================================================================
# Примеры использования
# ============================================================================

async def example_commercial_rental():
    """Пример: Коммерческая аренда агента"""

    print(f"\n{'='*70}")
    print(f"  ПРИМЕР 1: КОММЕРЧЕСКАЯ АРЕНДА АГЕНТА")
    print(f"{'='*70}\n")

    client = MarketplaceClient(
        platform_url="https://marketplace.example.com",
        api_key="your_api_key"
    )

    # Поиск агентов для Python разработки
    agents = await client.search_agents(
        capabilities=["python_coding"],
        max_hourly_rate=35.0,
        min_rating=4.5
    )

    # Показываем первого найденного
    if agents:
        client.display_agent(agents[0])

        # Арендуем агента
        contract = await client.rent_agent(
            agent_id=agents[0].id,
            rental_mode=RentalMode.COMMERCIAL,
            task_description="Разработка REST API для e-commerce платформы"
        )

        # Симуляция работы
        print(f"   ⚙️  Агент работает над задачей...")
        await asyncio.sleep(2)

        # Завершаем аренду
        cost = await client.end_rental(contract)

        # Оставляем отзыв
        await client.submit_review(
            agent_id=agents[0].id,
            rating=5.0,
            comment="Отличная работа! API работает идеально.",
            task_type="backend_development"
        )


async def example_volunteer_project():
    """Пример: Волонтерский научный проект"""

    print(f"\n\n{'='*70}")
    print(f"  ПРИМЕР 2: ВОЛОНТЕРСКИЙ НАУЧНЫЙ ПРОЕКТ")
    print(f"{'='*70}\n")

    client = MarketplaceClient(
        platform_url="https://marketplace.example.com",
        api_key="your_api_key"
    )

    # Поиск агентов для научных исследований (только волонтеры)
    agents = await client.search_agents(
        capabilities=["research", "scientific_writing"],
        volunteer_only=True,
        min_success_rate=0.90
    )

    print(f"📚 Волонтерские агенты для научного проекта:\n")

    for i, agent in enumerate(agents[:3], 1):
        print(f"{i}. {agent.name} - рейтинг {agent.rating}/5, {agent.total_tasks_completed} задач")

    if agents:
        # Арендуем лучшего
        contract = await client.rent_agent(
            agent_id=agents[0].id,
            rental_mode=RentalMode.VOLUNTEER,
            task_description="Литературный обзор для исследования изменения климата",
            project_name="Climate Change Impact Study 2026"
        )

        # Работа
        print(f"   ⚙️  Агент проводит исследование...")
        await asyncio.sleep(2)

        # Завершение (бесплатно!)
        cost = await client.end_rental(contract)

        print(f"   ✅ Проект завершен бесплатно!")

        # Благодарственный отзыв
        await client.submit_review(
            agent_id=agents[0].id,
            rating=5.0,
            comment="Огромная благодарность за помощь в научном проекте! Результат превзошел ожидания.",
            task_type="scientific_research"
        )


async def example_compare_agents():
    """Пример: Сравнение агентов"""

    print(f"\n\n{'='*70}")
    print(f"  ПРИМЕР 3: СРАВНЕНИЕ АГЕНТОВ")
    print(f"{'='*70}\n")

    client = MarketplaceClient(
        platform_url="https://marketplace.example.com",
        api_key="your_api_key"
    )

    # Поиск агентов для разработки
    agents = await client.search_agents(
        capabilities=["python_coding"]
    )

    print(f"🔍 Сравнение агентов для Python разработки:\n")

    # Таблица сравнения
    print(f"{'Агент':<20} {'Рейтинг':<10} {'Ставка':<12} {'Success':<10} {'Задач':<10}")
    print(f"{'-'*70}")

    for agent in agents[:5]:
        rate = f"${agent.hourly_rate}/ч" if agent.hourly_rate else f"${agent.task_rate}/task"
        print(
            f"{agent.name:<20} "
            f"{agent.rating:.1f}/5{'':>4} "
            f"{rate:<12} "
            f"{agent.success_rate*100:.0f}%{'':>6} "
            f"{agent.total_tasks_completed:<10}"
        )

    # Показываем отзывы о лучшем агенте
    if agents:
        best_agent = agents[0]
        print(f"\n📝 Отзывы о {best_agent.name}:\n")

        reviews = await client.get_agent_reviews(best_agent.id, limit=3)

        for i, review in enumerate(reviews, 1):
            print(f"{i}. ⭐ {review.rating:.1f}/5 - {review.comment}")
            print(f"   Задача: {review.task_type}, {review.created_at.strftime('%d.%m.%Y')}\n")


async def main():
    """Главная функция"""

    print("\n" + "="*70)
    print("  РАБОТА С MARKETPLACE АГЕНТОВ")
    print("="*70)

    # Пример 1: Коммерческая аренда
    await example_commercial_rental()

    # Пример 2: Волонтерский проект
    await example_volunteer_project()

    # Пример 3: Сравнение агентов
    await example_compare_agents()

    print("\n" + "="*70)
    print("  Примеры завершены")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
