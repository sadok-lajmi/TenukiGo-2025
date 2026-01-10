from api.services.MoveCompletionService import MoveCompletionService
from api.services.SGFGeneratorService import SGFGeneratorService

class DependencyContainer:
    def __init__(self):
        self.image_processor = None
        self.completion_service = MoveCompletionService()
        self.sgf_generator = SGFGeneratorService()

# Création d'une instance unique qui sera partagée par toute l'app
global_dependencies = DependencyContainer()