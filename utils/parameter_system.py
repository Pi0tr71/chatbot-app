from enum import StrEnum
from typing import List, Optional, Union, Dict, Any, Tuple
from pydantic import BaseModel, Field


class ParameterType(StrEnum):
    """Parameter type of the model."""

    RANGE = "range"
    MIN_ONLY = "min_only"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"


class ModelParameter(BaseModel):
    """Model parameter configuration."""

    name: str
    display_name: str
    type: ParameterType
    default_value: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    values: Optional[List[str]] = None
    always_send: bool = False
    description: Optional[str] = None
    visible_for_models: Optional[List[str]] = None
    def validate_value(self, value: Any) -> Tuple[bool, Any]:
        """Validates and converts the value according to the parameter type."""
        
        if value is None:
            return True, self.default_value

        if self.type == ParameterType.RANGE:
            try:
                value = float(value)
                if (self.min_value is not None and value < self.min_value) or (
                    self.max_value is not None and value > self.max_value
                ):
                    return False, None
                return True, value
            except (ValueError, TypeError):
                return False, None

        elif self.type == ParameterType.MIN_ONLY:
            try:
                value = float(value)
                if self.min_value is not None and value < self.min_value:
                    return False, None
                return True, value
            except (ValueError, TypeError):
                return False, None

        elif self.type == ParameterType.CATEGORICAL:
            if self.values and value in self.values:
                return True, value
            return False, None

        elif self.type == ParameterType.BOOLEAN:
            try:
                value = bool(value)
                return True, value
            except (ValueError, TypeError):
                return False, None

        return False, None

class ProviderParameters(BaseModel):
    """Konfiguracja parametrów providera."""
    parameters: Dict[str, ModelParameter] = Field(default_factory=dict)
    current_values: Dict[str, Any] = Field(default_factory=dict)
    
    def add_parameter(self, parameter: ModelParameter) -> None:
        """Dodaje parametr do tego providera."""
        self.parameters[parameter.name] = parameter
        # Inicjalizacja wartością domyślną
        self.current_values[parameter.name] = parameter.default_value
        
    def set_parameter_value(self, name: str, value: Any) -> bool:
        """Ustawia wartość parametru z walidacją."""
        if name not in self.parameters:
            return False
            
        valid, converted_value = self.parameters[name].validate_value(value)
        if valid:
            self.current_values[name] = converted_value
            return True
        return False
        
    def get_parameter_value(self, name: str) -> Any:
        """Pobiera aktualną wartość parametru."""
        return self.current_values.get(name)
        
    def reset_parameters(self) -> None:
        """Resetuje wszystkie parametry do wartości domyślnych."""
        for name, param in self.parameters.items():
            self.current_values[name] = param.default_value
            
    def get_api_parameters(self, model_id: str = None) -> Dict[str, Any]:
        """Pobiera parametry do wysłania do API, respektując 'always_send' i filtrując wg modelu."""
        result = {}
        for name, param in self.parameters.items():
            # Pomija parametr jeśli nie ma zastosowania do tego modelu
            if model_id and param.visible_for_models and model_id not in param.visible_for_models:
                continue
                
            value = self.current_values.get(name)
            # Dołącza, jeśli ma wartość i (jest oznaczony jako always_send lub ma wartość inną niż domyślna)
            if value is not None and (param.always_send or value != param.default_value):
                result[name] = value
                
        return result
    


    # Zaprojektowanie Lepszej Obsługi Parametrów dla Providerów

Bazując na Twoich wymaganiach, stworzę system parametrów, który będzie obsługiwał różne typy (przedziały min/max, samo min, kategoryczne low/medium/high) z domyślnymi wartościami oraz możliwością kontrolowania, które parametry są zawsze wysyłane.

## 1. Definicje Podstawowych Typów Parametrów

Zacznijmy od stworzenia klas, które będą reprezentować różne typy parametrów:

```python
# utils/parameter_system.py
from enum import StrEnum
from typing import List, Optional, Union, Dict, Any, Tuple
from pydantic import BaseModel, Field

class ParameterType(StrEnum):
    """Typ parametru modelu."""
    RANGE = "range"  # Parametry z wartościami min i max
    MIN_ONLY = "min_only"  # Parametry tylko z wartością minimalną
    CATEGORICAL = "categorical"  # Parametry z predefiniowanymi wartościami (np. low/medium/high)
    BOOLEAN = "boolean"  # Parametry typu prawda/fałsz

class ModelParameter(BaseModel):
    """Konfiguracja parametru modelu."""
    name: str
    display_name: str
    type: ParameterType
    default_value: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    values: Optional[List[str]] = None
    always_send: bool = False  # Czy parametr zawsze jest wysyłany do API
    description: Optional[str] = None
    visible_for_models: Optional[List[str]] = None  # Dla których modeli parametr jest widoczny
    
    def validate_value(self, value: Any) -> Tuple[bool, Any]:
        """Waliduje i konwertuje wartość zgodnie z typem parametru."""
        if value is None:
            return True, self.default_value
            
        if self.type == ParameterType.RANGE:
            try:
                value = float(value)
                if (self.min_value is not None and value < self.min_value) or \
                   (self.max_value is not None and value > self.max_value):
                    return False, None
                return True, value
            except (ValueError, TypeError):
                return False, None
                
        elif self.type == ParameterType.MIN_ONLY:
            try:
                value = float(value)
                if self.min_value is not None and value < self.min_value:
                    return False, None
                return True, value
            except (ValueError, TypeError):
                return False, None
                
        elif self.type == ParameterType.CATEGORICAL:
            if self.values and value in self.values:
                return True, value
            return False, None
            
        elif self.type == ParameterType.BOOLEAN:
            try:
                value = bool(value)
                return True, value
            except (ValueError, TypeError):
                return False, None
                
        return False, None

class ProviderParameters(BaseModel):
    """Konfiguracja parametrów providera."""
    parameters: Dict[str, ModelParameter] = Field(default_factory=dict)
    current_values: Dict[str, Any] = Field(default_factory=dict)
    
    def add_parameter(self, parameter: ModelParameter) -> None:
        """Dodaje parametr do tego providera."""
        self.parameters[parameter.name] = parameter
        # Inicjalizacja wartością domyślną
        self.current_values[parameter.name] = parameter.default_value
        
    def set_parameter_value(self, name: str, value: Any) -> bool:
        """Ustawia wartość parametru z walidacją."""
        if name not in self.parameters:
            return False
            
        valid, converted_value = self.parameters[name].validate_value(value)
        if valid:
            self.current_values[name] = converted_value
            return True
        return False
        
    def get_parameter_value(self, name: str) -> Any:
        """Pobiera aktualną wartość parametru."""
        return self.current_values.get(name)
        
    def reset_parameters(self) -> None:
        """Resetuje wszystkie parametry do wartości domyślnych."""
        for name, param in self.parameters.items():
            self.current_values[name] = param.default_value
            
    def get_api_parameters(self, model_id: str = None) -> Dict[str, Any]:
        """Pobiera parametry do wysłania do API, respektując 'always_send' i filtrując wg modelu."""
        result = {}
        for name, param in self.parameters.items():
            # Pomija parametr jeśli nie ma zastosowania do tego modelu
            if model_id and param.visible_for_models and model_id not in param.visible_for_models:
                continue
                
            value = self.current_values.get(name)
            # Dołącza, jeśli ma wartość i (jest oznaczony jako always_send lub ma wartość inną niż domyślna)
            if value is not None and (param.always_send or value != param.default_value):
                result[name] = value
                
        return result
```

## 2. Aktualizacja Klas Providerów

Zaktualizujmy klasy OpenAIProvider i AnthropicProvider, aby korzystały z nowego systemu parametrów:

```python
# models/openai_provider.py

class OpenAIProvider:
    def __init__(self, api_key: str, base_url: str, models: Dict[str, ModelConfig]):
        self.models = models
        self.usage_logger = ModelUsageLogger()
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.parameters = self._initialize_parameters()
        self.stats = Stats()
        
    def _initialize_parameters(self) -> ProviderParameters:
        """Inicjalizuje parametry dla tego providera."""
        params = ProviderParameters()
        
        # Parametr temperature
        params.add_parameter(ModelParameter(
            name="temperature",
            display_name="Temperatura",
            type=ParameterType.RANGE,
            default_value=0.7,
            min_value=0.0,
            max_value=2.0,
            description="Kontroluje losowość. Niższe wartości są bardziej deterministyczne, wyższe bardziej kreatywne."
        ))
        
        # Parametr max_tokens
        params.add_parameter(ModelParameter(
            name="max_tokens",
            display_name="Maksymalna liczba tokenów",
            type=ParameterType.MIN_ONLY,
            default_value=1024,
            min_value=1,
            description="Maksymalna liczba tokenów do wygenerowania."
        ))
        
        # Parametr top_p
        params.add_parameter(ModelParameter(
            name="top_p",
            display_name="Top P",
            type=ParameterType.RANGE,
            default_value=1.0,
            min_value=0.0,
            max_value=1.0,
            description="Kontroluje różnorodność poprzez próbkowanie jądrowe."
        ))
        
        # Parametr frequency_penalty
        params.add_parameter(ModelParameter(
            name="frequency_penalty",
            display_name="Kara za częstotliwość",
            type=ParameterType.RANGE,
            default_value=0.0,
            min_value=-2.0,
            max_value=2.0,
            description="Zmniejsza powtarzanie się sekwencji tokenów."
        ))
        
        # Parametr presence_penalty
        params.add_parameter(ModelParameter(
            name="presence_penalty",
            display_name="Kara za obecność",
            type=ParameterType.RANGE,
            default_value=0.0,
            min_value=-2.0,
            max_value=2.0,
            description="Zmniejsza powtarzanie się tematów."
        ))
        
        # Parametr reasoning_effort (kategoryczny)
        params.add_parameter(ModelParameter(
            name="reasoning_effort",
            display_name="Wysiłek rozumowania",
            type=ParameterType.CATEGORICAL,
            default_value="medium",
            values=["low", "medium", "high"],
            description="Ilość wysiłku wkładanego w rozumowanie.",
            visible_for_models=["gpt-4", "gpt-4-1106-preview"]  # Dostępny tylko dla wybranych modeli
        ))
        
        return params
        
    def get_request(self, messages: List[Message], model_id: str) -> str:
        # Istniejący kod...
        
        try:
            start_time = time.time()

            request_params = {
                "model": model_id,
                "messages": openai_messages,
                "stream": False,
                **self.parameters.get_api_parameters(model_id)  # Używamy nowego systemu parametrów
            }

            # Pozostała część metody...
```

Podobnie dla AnthropicProvider:

```python
# models/anthropic_provider.py

class AnthropicProvider:
    def __init__(self, api_key: str, base_url: str, models: Dict[str, ModelConfig]):
        self.models = models
        self.usage_logger = ModelUsageLogger()
        self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        self.parameters = self._initialize_parameters()
        self.stats = Stats()
        
    def _initialize_parameters(self) -> ProviderParameters:
        """Inicjalizuje parametry dla tego providera."""
        params = ProviderParameters()
        
        # Parametr temperature
        params.add_parameter(ModelParameter(
            name="temperature",
            display_name="Temperatura",
            type=ParameterType.RANGE,
            default_value=0.7,
            min_value=0.0,
            max_value=1.0,
            description="Kontroluje losowość. Niższe wartości są bardziej deterministyczne, wyższe bardziej kreatywne."
        ))
        
        # Parametr max_tokens
        params.add_parameter(ModelParameter(
            name="max_tokens",
            display_name="Maksymalna liczba tokenów",
            type=ParameterType.MIN_ONLY,
            default_value=1024,
            min_value=1,
            description="Maksymalna liczba tokenów do wygenerowania."
        ))
        
        # Parametr top_p
        params.add_parameter(ModelParameter(
            name="top_p",
            display_name="Top P",
            type=ParameterType.RANGE,
            default_value=0.7,
            min_value=0.0,
            max_value=1.0,
            description="Kontroluje różnorodność poprzez próbkowanie jądrowe."
        ))
        
        # Parametr top_k
        params.add_parameter(ModelParameter(
            name="top_k",
            display_name="Top K",
            type=ParameterType.MIN_ONLY,
            default_value=None,
            min_value=0,
            description="Ogranicza wybór tokenów do top K opcji."
        ))
        
        return params
    
    # Aktualizacja metod żądań aby używały nowego systemu parametrów...
```

## 3. Aktualizacja ChatManager

Zaktualizujmy klasę ChatManager, aby obsługiwała nowy system parametrów:

```python
# Metody w klasie ChatManager:

def get_current_model_parameters(self) -> Dict[str, Dict]:
    """Pobiera informacje o parametrach dla aktualnego providera."""
    if self.current_provider is None or self.current_provider not in self.providers:
        return {"error": "Nie wybrano providera"}
        
    provider = self.providers[self.current_provider]
    
    if not hasattr(provider, "parameters"):
        return {"error": "Provider nie obsługuje konfiguracji parametrów"}
        
    # Pobiera parametry, które mają zastosowanie do aktualnego modelu
    result = {}
    for name, param in provider.parameters.parameters.items():
        # Pomija parametr jeśli nie ma zastosowania do aktualnego modelu
        if param.visible_for_models and self.current_model_id not in param.visible_for_models:
            continue
            
        param_info = {
            "display_name": param.display_name,
            "type": param.type,
            "current_value": provider.parameters.get_parameter_value(name),
            "default_value": param.default_value,
            "always_send": param.always_send,
            "description": param.description
        }
        
        # Dodaje informacje specyficzne dla typu
        if param.type in [ParameterType.RANGE, ParameterType.MIN_ONLY]:
            param_info["min"] = param.min_value
            param_info["max"] = param.max_value
        elif param.type == ParameterType.CATEGORICAL:
            param_info["values"] = param.values
            
        result[name] = param_info
        
    return result
    
def set_model_parameter(self, param_name: str, value: Any) -> bool:
    """Ustawia parametr dla aktualnego providera."""
    if self.current_provider is None or self.current_provider not in self.providers:
        logging.error("Nie można ustawić parametru: Nie wybrano providera")
        return False
        
    provider = self.providers[self.current_provider]
    
    if not hasattr(provider, "parameters"):
        logging.error(f"Provider {self.current_provider} nie obsługuje konfiguracji parametrów")
        return False
        
    success = provider.parameters.set_parameter_value(param_name, value)
    if success:
        logging.info(f"Ustawiono {param_name}={value} dla providera {self.current_provider}")
    else:
        logging.error(f"Nie udało się ustawić {param_name}={value} dla providera {self.current_provider}")
    return success
    
def reset_model_parameters(self) -> bool:
    """Resetuje wszystkie parametry dla aktualnego providera do wartości domyślnych."""
    if self.current_provider is None or self.current_provider not in self.providers:
        logging.error("Nie można zresetować parametrów: Nie wybrano providera")
        return False
        
    provider = self.providers[self.current_provider]
    
    if not hasattr(provider, "parameters"):
        logging.error(f"Provider {self.current_provider} nie obsługuje konfiguracji parametrów")
        return False
        
    provider.parameters.reset_parameters()
    logging.info(f"Zresetowano wszystkie parametry dla providera {self.current_provider}")
    return True
```

## 4. Aktualizacja Interfejsu Użytkownika

Na koniec, zaktualizujmy funkcję `render_chat_sidebar` w celu obsługi nowego systemu parametrów:

```python
# Część funkcji render_chat_sidebar do obsługi parametrów modelu

# Model parameters settings
with st.sidebar.expander("Parametry modelu"):
    # Pobierz informacje o parametrach dla aktualnego providera i modelu
    param_info = chat_manager.get_current_model_parameters()
    
    if isinstance(param_info, dict) and not param_info.get("error"):
        # Dodaj przycisk resetowania na górze
        if st.button("Przywróć domyślne", key="reset_params"):
            chat_manager.reset_model_parameters()
            st.success("Parametry zresetowane do wartości domyślnych")
            st.rerun()

        # Śledź, które parametry wysyłać
        if "selected_params" not in st.session_state:
            st.session_state.selected_params = {}
        
        # Wyświetl i umożliw edycję każdego parametru
        for param_name, param_data in param_info.items():
            current_value = param_data.get("current_value")
            default_value = param_data.get("default_value")
            param_label = param_data.get("display_name", param_name.replace("_", " ").title())
            always_send = param_data.get("always_send", False)
            description = param_data.get("description", "")
            
            # Inicjalizuj stan wyboru dla tego parametru
            if param_name not in st.session_state.selected_params:
                st.session_state.selected_params[param_name] = always_send or current_value is not None

            # Obsługa różnych typów parametrów z checkboxem po prawej
            param_type = param_data.get("type", "range")
            
            if param_type == "categorical" and "values" in param_data:  # Parametr typu enum
                values = param_data["values"]
                col1, col2 = st.columns([4, 1])

                with col1:
                    tooltip = st.empty()
                    with tooltip.container():
                        new_value = st.selectbox(
                            f"{param_label}",
                            options=values,
                            index=values.index(current_value) if current_value in values else 0,
                            key=f"param_{param_name}",
                            help=description
                        )

                with col2:
                    include_param = st.checkbox(
                        "Wyślij",
                        value=st.session_state.selected_params[param_name],
                        key=f"include_{param_name}",
                        disabled=always_send,
                        label_visibility="collapsed",
                    )
            
            elif param_type == "min_only" or (param_type == "range" and param_name in ["max_tokens"]):
                # Parametry całkowitoliczbowe z informacją o zakresie
                min_val = param_data.get("min", 1)
                max_val = param_data.get("max", 32000)
                col1, col2 = st.columns([4, 1])

                with col1:
                    new_value = st.number_input(
                        f"{param_label}",
                        min_value=min_val,
                        max_value=max_val if max_val else None,
                        value=current_value if current_value is not None else min_val,
                        step=1,
                        key=f"param_{param_name}",
                        help=description
                    )

                with col2:
                    include_param = st.checkbox(
                        "Wyślij",
                        value=st.session_state.selected_params[param_name],
                        key=f"include_{param_name}",
                        disabled=always_send,
                        label_visibility="collapsed",
                    )
            
            elif param_type == "range":
                # Parametry zmiennoprzecinkowe (temperature, top_p, itp.)
                min_val = float(param_data.get("min", 0.0))
                max_val = float(param_data.get("max", 1.0))
                col1, col2 = st.columns([4, 1])

                with col1:
                    new_value = st.slider(
                        f"{param_label}",
                        min_value=min_val,
                        max_value=max_val,
                        value=float(current_value) if current_value is not None else float(default_value or min_val),
                        step=0.01,
                        key=f"param_{param_name}",
                        help=description
                    )

                with col2:
                    include_param = st.checkbox(
                        "Wyślij",
                        value=st.session_state.selected_params[param_name],
                        key=f"include_{param_name}",
                        disabled=always_send,
                        label_visibility="collapsed",
                    )
            
            elif param_type == "boolean":
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    new_value = st.checkbox(
                        f"{param_label}",
                        value=current_value if current_value is not None else default_value,
                        key=f"param_{param_name}",
                        help=description
                    )
                
                with col2:
                    include_param = st.checkbox(
                        "Wyślij",
                        value=st.session_state.selected_params[param_name],
                        key=f"include_{param_name}",
                        disabled=always_send,
                        label_visibility="collapsed",
                    )

            # Aktualizuj stan wyboru
            st.session_state.selected_params[param_name] = include_param or always_send

            # Tylko aktualizuj, jeśli wartość się zmieniła i checkbox jest zaznaczony
            if include_param or always_send:
                if new_value != current_value:
                    chat_manager.set_model_parameter(param_name, new_value)
            else:
                # Jeśli checkbox jest odznaczony, ustaw parametr na None
                if current_value is not None:
                    chat_manager.set_model_parameter(param_name, None)
    else:
        # Wyświetl komunikat o błędzie, jeśli provider nie obsługuje parametrów
        error_msg = param_info.get("error", "Aktualny provider nie obsługuje konfiguracji parametrów")
        st.warning(error_msg)
```

## 5. Dodanie Parametrów do Ekranu Konfiguracji Modeli

Można również dodać sekcję konfiguracji parametrów w interfejsie konfiguracji modeli:

```python
# W funkcji render_config_models_interface
# Dodaj możliwość konfigurowania parametrów dla konkretnego modelu

# Po dodaniu modelu, pozwól na konfigurację jego parametrów
with st.expander(f"Konfiguracja parametrów dla {model_id}"):
    st.subheader("Parametry widoczne dla tego modelu")
    
    if provider == Provider.OPENAI:
        # Lista wszystkich możliwych parametrów dla OpenAI
        all_params = ["temperature", "max_tokens", "top_p", "frequency_penalty", 
                     "presence_penalty", "reasoning_effort"]
    elif provider == Provider.ANTHROPIC:
        # Lista wszystkich możliwych parametrów dla Anthropic
        all_params = ["temperature", "max_tokens", "top_p", "top_k"]
    else:
        all_params = []
    
    # Pozwól użytkownikowi wybrać, które parametry są widoczne dla tego modelu
    visible_params = st.multiselect(
        "Wybierz parametry widoczne dla tego modelu",
        options=all_params,
        default=model_config.additional_params.get("visible_parameters", all_params),
        key=f"visible_params_{model_id}"
    )
    
    # Zapisz wybrane parametry w konfiguracji modelu
    if st.button("Zapisz konfigurację parametrów"):
        model_config.additional_params["visible_parameters"] = visible_params
        config.save_to_file()
        st.success(f"Zapisano konfigurację parametrów dla modelu {model_id}")
```

## Podsumowanie

Ten system obsługi parametrów zapewnia:

1. Różne typy parametrów (przedział min/max, samo min, kategoryczne, logiczne)
2. Wartości domyślne dla każdego parametru
3. Parametry, które są zawsze wysyłane do API (always_send)
4. Możliwość konfigurowania, które modele mają widoczne konkretne parametry
5. Czytelny interfejs z odpowiednimi kontrolkami dla każdego typu parametru
6. Możliwość włączania/wyłączania wysyłania parametrów do API

Dzięki temu rozwiązaniu użytkownicy będą mieli większą kontrolę nad parametrami wysyłanymi do API, a administrator systemu będzie mógł skonfigurować, które parametry są dostępne dla których modeli.