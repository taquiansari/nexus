"""
NEXUS Chart Generator Worker — Creates visualizations from data.
"""
from __future__ import annotations
import io
import base64
import logging
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from workers.base_worker import BaseWorker, WorkerResult
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

CHART_CODE_PROMPT = """You are a data visualization expert. Generate matplotlib code to create a chart.

RULES:
1. The DataFrame is available as `df`. Do NOT load from a file.
2. Use matplotlib (imported as `plt`). 
3. Create a professional-looking chart with:
   - A clear title
   - Labeled axes
   - A good color scheme (use colors like #4F46E5, #06B6D4, #10B981, #F59E0B, #EF4444)
   - Legend if multiple series
   - Tight layout: `plt.tight_layout()`
4. Save the figure to `fig` variable: `fig = plt.gcf()`
5. Set figure size: `plt.figure(figsize=(12, 7))`
6. Use dark style: `plt.style.use('dark_background')`
7. Output ONLY Python code, no markdown fences, no explanations.
8. If the DataFrame has date columns, convert them and handle them properly.
9. Create a `summary` string variable describing the chart.
"""


class ChartGenerator(BaseWorker):
    name = "ChartGenerator"

    async def _execute(
        self,
        instruction: str,
        context: dict,
        uploaded_files: list[str],
    ) -> WorkerResult:
        # Get DataFrame from context
        df = context.get("previous_data")
        if df is None:
            return WorkerResult(
                success=False,
                error="No data available for chart generation. A DataProcessor step must run first."
            )

        if isinstance(df, str):
            try:
                df = pd.read_csv(io.StringIO(df))
            except Exception:
                return WorkerResult(success=False, error="Could not parse data for chart generation.")

        if not isinstance(df, pd.DataFrame):
            return WorkerResult(success=False, error=f"Expected DataFrame, got {type(df).__name__}")

        # Generate chart code via LLM
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.0,
            max_tokens=2048,
        )

        user_content = (
            f"Instruction: {instruction}\n\n"
            f"DataFrame columns: {list(df.columns)}\n"
            f"DataFrame shape: {df.shape}\n"
            f"Data types:\n{df.dtypes.to_string()}\n\n"
            f"First 5 rows:\n{df.head().to_string()}\n\n"
            f"Generate matplotlib code to create this chart."
        )

        messages = [
            SystemMessage(content=CHART_CODE_PROMPT),
            HumanMessage(content=user_content),
        ]

        response = await llm.ainvoke(messages)
        code = response.content.strip()

        if code.startswith("```"):
            code = code.split("\n", 1)[-1]
            if code.endswith("```"):
                code = code[:-3]
            code = code.strip()

        logger.info(f"ChartGenerator: Generated code:\n{code[:300]}")

        # Execute chart code
        try:
            plt.close("all")

            import numpy as np
            local_vars = {"df": df.copy(), "plt": plt, "pd": pd, "np": np, "mdates": mdates}
            exec(code, {}, local_vars)

            fig = local_vars.get("fig", plt.gcf())
            summary = local_vars.get("summary", "Chart generated successfully")

            # Save to bytes
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                       facecolor="#0a0e27", edgecolor="none")
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode("utf-8")
            plt.close("all")

            return WorkerResult(
                success=True,
                output=summary,
                data=img_base64,
                artifacts=[{
                    "name": "chart.png",
                    "type": "image/png",
                    "base64": img_base64,
                }],
            )

        except Exception as e:
            plt.close("all")
            return WorkerResult(
                success=False,
                output=f"Chart generation failed: {str(e)}",
                error=f"Matplotlib error: {str(e)}\nCode:\n{code[:500]}",
            )
