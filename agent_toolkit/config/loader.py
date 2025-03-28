import os
import yaml
from typing import Dict, Any
from pathlib import Path

class ConfigLoader:
    _configs: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def load_config(cls, module_name: str) -> Dict[str, Any]:
        """Load configuration for a specific module from its YAML file."""
        if module_name not in cls._configs:
            config_path = Path(__file__).parent / f"{module_name}.yaml"
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found for module: {module_name}")
            
            with open(config_path, 'r') as f:
                cls._configs[module_name] = yaml.safe_load(f)
        
        return cls._configs[module_name]
    
    @classmethod
    def get_config(cls, module_name: str, key: str, default: Any = None) -> Any:
        """Get a specific configuration value for a module."""
        config = cls.load_config(module_name)
        return config.get(key, default) 