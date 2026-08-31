# agents/chart_editor.py
from langchain_ollama import ChatOllama
from state import AnalysisState

class ChartEditorNode:
    def __init__(self, model_name: str = "gemma4:31b-cloud"):
        self.llm = ChatOllama(model=model_name)

    def execute(self, state: AnalysisState) -> AnalysisState:
        print("âœï¸ [Chart Editor]: Applying executive tweaks to the chart code...")
        
        # Get the specific code the user wants to edit and their request
        existing_code = state.get("current_code")
        user_request = state.get("user_edit_request")
        
        prompt = f"""
        You are a Senior Python Visualization Expert. 
        Modify the following Plotly Express script exactly as requested by the user.
        
        USER REQUEST: "{user_request}"
        
        EXISTING CODE:
        ```python
        {existing_code}
        ```
        
        RULES:
        1. Return ONLY the fully updated Python code.
        2. Do not change the data loading or saving boilerplate. 
        3. Do not add markdown or explanations outside the python block.
        """
        
        raw_response = self.llm.invoke(prompt)
        
        # Clean the output (using your existing regex from Chart Architect)
        clean_code = self._clean_llm_code_output(raw_response.content)
        
        state["current_code"] = clean_code
        state["execution_error"] = None
        
        return state