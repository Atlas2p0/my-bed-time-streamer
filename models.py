"""State management for the streaming application."""

class StreamState:
    """Holds the global state for the streaming process."""
    
    def __init__(self):
        self.current_process = None

# Global instance - imported where needed
stream_state = StreamState()