"""
Utils for handling errors, especially from C++ code with potential encoding issues.
"""

class InvalidMoveError(Exception):
    """Exception for invalid moves detected in the game."""
    pass

def safe_get_error_message(exception):
        """Tente de récupérer un message d'erreur propre, même si l'encodage est cassé."""
        # 1. Essayer de lire les arguments bruts (parfois stockés en bytes)
        if hasattr(exception, 'args') and exception.args:
            raw_msg = exception.args[0]
            if isinstance(raw_msg, bytes):
                try:
                    # On tente le décodage Windows (CP1252) qui accepte tout
                    return raw_msg.decode('cp1252')
                except:
                    pass # On continue si ça échoue

        # 2. Essayer la conversion standard
        try:
            msg = str(exception)
            # Si le message ressemble à du garbage (caractères étranges comme oXŮ)
            # On peut faire un filtre basique (optionnel)
            if any(ord(c) > 127 for c in msg) and len(msg) < 10:
                return "Unknown C++ Error (Garbage output)"
            return msg
        except UnicodeDecodeError:
            return "Encoding Error in C++ Message"
        except Exception:
            return "Unreadable Exception"