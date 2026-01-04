"""
Utils for handling errors, especially from C++ code with potential encoding issues.
"""

class InvalidMoveError(Exception):
    """Exception for invalid moves detected in the game."""
    pass

def safe_get_error_message(exception):
        """Tries to extract a readable error message from an exception,
        handling potential encoding issues from C++ exceptions."""
        # 1. Try to read raw arguments (sometimes stored as bytes)
        if hasattr(exception, 'args') and exception.args:
            raw_msg = exception.args[0]
            if isinstance(raw_msg, bytes):
                try:
                    # Attempt Windows (CP1252) decoding which accepts all characters
                    return raw_msg.decode('cp1252')
                except:
                    pass # Continue if it fails

        # 2. Try standard conversion
        try:
            msg = str(exception)
            # If the message looks like garbage (strange characters like oXŮ)
            # We can do a basic filter (optional)
            if any(ord(c) > 127 for c in msg) and len(msg) < 10:
                return "Unknown C++ Error (Garbage output)"
            return msg
        except UnicodeDecodeError:
            return "Encoding Error in C++ Message"
        except Exception:
            return "Unreadable Exception"