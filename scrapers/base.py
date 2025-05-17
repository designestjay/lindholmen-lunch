from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class MenuItem:
    def __init__(self, name: str, category: Optional[str] = None, description: Optional[str] = None):
        self.name = name.strip()
        self.category = category.strip() if category else None
        self.description = description.strip() if description else None

    def __repr__(self):
        return f"MenuItem(name={self.name!r}, category={self.category!r}, description={self.description!r})"

    def __str__(self):
        if self.description:
            return f"{self.name} - {self.description}"
        return self.name
    
    def to_dict(self):
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description
        }


class DailyMenu:
    def __init__(self, day: str, items: List[MenuItem]):
        self.day = day.lower()  # e.g. "monday", "tuesday"
        self.items = items

    def __repr__(self):
        return f"DailyMenu(day={self.day!r}, items={self.items!r})"

class LunchScraper(ABC):
    @abstractmethod
    def fetch(self) -> None:
        """Fetch and parse the menu data. Must be called before accessing menu."""
        pass

    @abstractmethod
    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        """Return the menu for the given day (e.g., 'monday')."""
        pass

    @abstractmethod
    def get_all_menus(self) -> Dict[str, DailyMenu]:
        """Return a dictionary of all parsed menus by day."""
        pass
