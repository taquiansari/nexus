"""
NEXUS Data Processor Worker — pandas-based data operations.
"""
from __future__ import annotations
import json
import logging
import pandas as pd
import io
import os
from workers.base_worker import BaseWorker, WorkerResult
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

CODE_GEN_PROMPT = """You are a Python data processing expert. Generate pandas code to fulfill the instruction.

RULES:
1. The input DataFrame is already loaded as `df`. Do NOT load from file.
2. Store the final result in a variable called `result_df` (if DataFrame) or `result_value` (if a scalar/string).
3. Also create a string variable called `summary` that describes what the code did and key findings.
4. Use only pandas, numpy, and standard library. No other imports.
5. Handle errors gracefully — check if columns exist before using them.
6. Output ONLY the Python code, no markdown fences, no explanations.
7. If dates are involved, try multiple formats with `pd.to_datetime(col, dayfirst=True, errors='coerce')`.

Example good response:
import numpy as np
result_df = df.dropna(subset=['revenue'])
result_df = result_df.drop_duplicates()
summary = f"Cleaned data: {len(result_df)} rows remaining after removing {len(df) - len(result_df)} rows with nulls/duplicates"
"""


class DataProcessor(BaseWorker):
    name = "DataProcessor"

    async def _execute(
        self,
        instruction: str,
        context: dict,
        uploaded_files: list[str],
    ) -> WorkerResult:
        # Load DataFrame from context (previous step output) or file
        df = None

        # Check if previous step provided a DataFrame
        prev_data = context.get("previous_data")
        if prev_data is not None:
            if isinstance(prev_data, pd.DataFrame):
                df = prev_data
            elif isinstance(prev_data, str):
                try:
                    df = pd.read_csv(io.StringIO(prev_data))
                except Exception:
                    pass

        # If no previous data, try uploaded files
        if df is None and uploaded_files:
            for fpath in uploaded_files:
                if fpath.endswith(".csv") and os.path.exists(fpath):
                    try:
                        df = pd.read_csv(fpath)
                        logger.info(f"DataProcessor: Loaded CSV from {fpath}: {df.shape}")
                        break
                    except Exception as e:
                        logger.warning(f"DataProcessor: Failed to load {fpath}: {e}")

        if df is None:
            return WorkerResult(
                success=False,
                error="No data available. Ensure a CSV file is uploaded or data comes from a previous step."
            )

        # Generate pandas code via LLM
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.0,
            max_tokens=2048,
        )

        df_info = io.StringIO()
        df.info(buf=df_info)
        df_info_str = df_info.getvalue()

        user_content = (
            f"Instruction: {instruction}\n\n"
            f"DataFrame info:\n{df_info_str}\n\n"
            f"First 5 rows:\n{df.head().to_string()}\n\n"
            f"Null counts:\n{df.isnull().sum().to_string()}\n\n"
            f"Generate pandas code to fulfill the instruction."
        )

        messages = [
            SystemMessage(content=CODE_GEN_PROMPT),
            HumanMessage(content=user_content),
        ]

        response = await llm.ainvoke(messages)
        code = response.content.strip()

        # Clean code fences
        if code.startswith("```"):
            code = code.split("\n", 1)[-1]
            if code.endswith("```"):
                code = code[:-3]
            code = code.strip()

        logger.info(f"DataProcessor: Generated code:\n{code[:300]}")

        # Execute the generated code
        try:
            local_vars = {"df": df.copy(), "pd": pd}

            # Add numpy since it's commonly used
            import numpy as np
            local_vars["np"] = np

            exec(code, {}, local_vars)

            result_df = local_vars.get("result_df")
            result_value = local_vars.get("result_value")
            summary = local_vars.get("summary", "Code executed successfully")

            artifacts = []
            output_data = None

            if result_df is not None and isinstance(result_df, pd.DataFrame):
                output_data = result_df
                summary += f"\nResult shape: {result_df.shape}"
                # Store CSV string for context passing
                csv_preview = result_df.head(20).to_string()
                summary += f"\nPreview:\n{csv_preview}"
            elif result_value is not None:
                output_data = str(result_value)
                summary += f"\nResult: {str(result_value)[:500]}"

            return WorkerResult(
                success=True,
                output=summary,
                data=output_data,
                artifacts=artifacts,
            )

        except Exception as e:
            return WorkerResult(
                success=False,
                output=f"Code execution failed: {str(e)}",
                error=f"Python execution error: {str(e)}\nCode:\n{code[:500]}",
            )
