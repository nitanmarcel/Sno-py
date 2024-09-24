from sansio_lsp_client import Diagnostic


class Diagnostic:
    def __init__(self):
        self._diagnostics = []
        self._ready = False
        
    def append(self, diagnostic: Diagnostic):
        self._diagnostics.append(diagnostic)
    
    def get_diagnostics(self) -> list:
        if not self._ready:
            return []
        diagnostics = self._diagnostics
        return diagnostics
     
    def __enter__(self):
        self._ready = False
        self._diagnostics.clear()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ready = True