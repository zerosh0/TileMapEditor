import pygame

# Evite OSError: [Errno 24] Too many open files
# Notamment sur MacOs


class FontManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cache = {}
        return cls._instance

    def get(self, name=None, size=24):
        key = (name, size)
        if key not in self.cache:
            if name is None:
                font = pygame.font.Font(None, size)
            else:
                font = pygame.font.Font(name, size)
            self.cache[key] = font
        return self.cache[key]
