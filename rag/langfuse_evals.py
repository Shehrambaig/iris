"""
Langfuse LLM-as-a-Judge Evaluator
Runs LLM-based evaluations on Langfuse traces
"""

import os
from langfuse import Langfuse
from openai import OpenAI
from typing import Dict, List, Any
import json

# Initialize Langfuse client with your local instance
langfuse = Langfuse(
    secret_key="sk-lf-a877ea43-e01e-4d3e-a021-af767ea125d4",
    public_key="pk-lf-7398fb40-51c4-41f2-a70d-9fea5f0048a0",
    host="http://localhost:3000"
)

# Initialize OpenAI client (or use any LLM provider)
client = OpenAI('add key')

# ============================================
# LLM JUDGE PROMPTS
# ============================================

EVAL_PROMPTS = {
    "conciseness": """
Evaluate the conciseness of this AI response on a scale of 0.0 to 1.0.
- 1.0: Response is perfectly concise, no unnecessary information
- 0.5: Response has some redundancy but acceptable
- 0.0: Response is very verbose or repetitive

Input: {input}
Output: {output}

Respond with ONLY a JSON object in this format:
{{"score": 0.8, "reasoning": "Brief explanation"}}
""",

    "correctness": """
Evaluate the correctness of this AI response on a scale of 0.0 to 1.0.
- 1.0: Response is completely correct and accurate
- 0.5: Response is partially correct with some errors
- 0.0: Response is incorrect or misleading

Input: {input}
Output: {output}

Respond with ONLY a JSON object in this format:
{{"score": 0.9, "reasoning": "Brief explanation"}}
""",

    "helpfulness": """
Evaluate the helpfulness of this AI response on a scale of 0.0 to 1.0.
- 1.0: Response fully addresses the query and is very helpful
- 0.5: Response partially addresses the query
- 0.0: Response does not address the query or is unhelpful

Input: {input}
Output: {output}

Respond with ONLY a JSON object in this format:
{{"score": 0.85, "reasoning": "Brief explanation"}}
""",

    "relevance": """
Evaluate the relevance of this AI response on a scale of 0.0 to 1.0.
- 1.0: Response is highly relevant to the input
- 0.5: Response is somewhat relevant
- 0.0: Response is off-topic or irrelevant

Input: {input}
Output: {output}

Respond with ONLY a JSON object in this format:
{{"score": 0.95, "reasoning": "Brief explanation"}}
""",

    "hallucination": """
Evaluate if this AI response contains hallucinations on a scale of 0.0 to 1.0.
- 1.0: No hallucinations, all information appears accurate
- 0.5: Minor unverifiable claims
- 0.0: Contains clear hallucinations or false information

Input: {input}
Output: {output}

Respond with ONLY a JSON object in this format:
{{"score": 1.0, "reasoning": "Brief explanation"}}
""",

    "context_relevance": """
Evaluate if the AI's response is contextually relevant on a scale of 0.0 to 1.0.
- 1.0: Response perfectly fits the context
- 0.5: Response somewhat fits the context
- 0.0: Response ignores important context

Input: {input}
Output: {output}

Respond with ONLY a JSON object in this format:
{{"score": 0.9, "reasoning": "Brief explanation"}}
""",
}

# ============================================
# LLM JUDGE EVALUATOR
# ============================================

class LLMJudge:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model

    def evaluate(self, criterion: str, input_text: str, output_text: str) -> Dict[str, Any]:
        """Run LLM evaluation for a specific criterion"""

        if criterion not in EVAL_PROMPTS:
            raise ValueError(f"Unknown criterion: {criterion}")

        prompt = EVAL_PROMPTS[criterion].format(
            input=input_text,
            output=output_text
        )

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert evaluator. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=500
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            result = json.loads(result_text)

            return {
                "name": criterion,
                "value": float(result["score"]),
                "comment": result["reasoning"]
            }

        except Exception as e:
            print(f"Error evaluating {criterion}: {str(e)}")
            return {
                "name": criterion,
                "value": 0.5,
                "comment": f"Evaluation failed: {str(e)}"
            }

# ============================================
# EVAL RUNNER
# ============================================

class LangfuseLLMEvalRunner:
    def __init__(self, criteria: List[str] = None):
        self.judge = LLMJudge()

        # Default to all criteria if none specified
        self.criteria = criteria or [
            "conciseness",
            "correctness",
            "helpfulness",
            "relevance",
            "hallucination",
            "context_relevance"
        ]

    def run_evals_on_trace(self, trace_id: str):
        """Run LLM evals on a specific trace"""
        print(f"\n📊 Running LLM evals on trace: {trace_id}")

        try:
            # Fetch trace data using get_trace
            trace = langfuse.get_trace(trace_id)

            input_text = str(trace.input) if trace.input else ""
            output_text = str(trace.output) if trace.output else ""

            if not output_text:
                print("  ⚠️  No output found, skipping trace")
                return []

            results = []
            for criterion in self.criteria:
                print(f"  🤖 Evaluating {criterion}...")

                result = self.judge.evaluate(criterion, input_text, output_text)

                # Score the trace in Langfuse
                langfuse.score(
                    trace_id=trace_id,
                    name=result["name"],
                    value=result["value"],
                    comment=result["comment"]
                )

                results.append(result)
                print(f"    ✓ Score: {result['value']:.2f} - {result['comment']}")

            return results

        except Exception as e:
            print(f"  ❌ Error processing trace: {str(e)}")
            return []

    def run_evals_on_recent_traces(self, limit: int = 10, project_name: str = "iris"):
        """Run evals on recent traces from iris project"""
        print(f"\n🔍 Fetching {limit} most recent traces from '{project_name}' project...")

        try:
            # Use HTTP API directly to get traces
            import requests
            from base64 import b64encode

            url = f"http://localhost:3000/api/public/traces"

            # Create basic auth header with public:secret keys
            auth_string = f"pk-lf-9f6ed26f-9ae0-427e-96f1-0f1e2983776e:sk-lf-4087f44f-b41b-45fe-980c-66522b90445e"
            auth_bytes = auth_string.encode('ascii')
            base64_bytes = b64encode(auth_bytes)
            base64_string = base64_bytes.decode('ascii')

            headers = {
                "Authorization": f"Basic {base64_string}",
                "Content-Type": "application/json"
            }
            params = {"limit": limit}

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            traces = data.get("data", [])

            if len(traces) == 0:
                print("\n⚠️  No traces found in Langfuse!")
                print("\n💡 To create traces, make sure your application is:")
                print("   1. Importing Langfuse SDK")
                print("   2. Creating traces with langfuse.trace()")
                print("   3. Running and generating some outputs")
                print("\n   Once you have traces, run this script again.")
                return {}

            print(f"Found {len(traces)} traces\n")

            all_results = {}
            for i, trace in enumerate(traces, 1):
                trace_id = trace.get("id")
                if not trace_id:
                    continue

                print(f"\n{'='*60}")
                print(f"Trace {i}/{len(traces)}: {trace_id[:16]}...")
                print(f"{'='*60}")

                results = self.run_evals_on_trace(trace_id)
                all_results[trace_id] = results

            # Print summary
            print("\n" + "="*60)
            print("📈 EVALUATION SUMMARY")
            print("="*60)

            # Calculate averages per criterion
            criterion_scores = {}
            for results in all_results.values():
                for result in results:
                    if result["name"] not in criterion_scores:
                        criterion_scores[result["name"]] = []
                    criterion_scores[result["name"]].append(result["value"])

            print("\nAverage Scores by Criterion:")
            for criterion, scores in criterion_scores.items():
                if scores:
                    avg = sum(scores) / len(scores)
                    print(f"  {criterion}: {avg:.2f}")

            print("\nPer-Trace Summary:")
            for trace_id, results in all_results.items():
                if results:
                    avg_score = sum(r["value"] for r in results) / len(results)
                    print(f"  {trace_id[:16]}... - Avg: {avg_score:.2f}")

            return all_results

        except Exception as e:
            print(f"❌ Error fetching traces: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return {}

# ============================================
# USAGE EXAMPLES
# ============================================

if __name__ == "__main__":
    # Example 1: Run all evals on recent traces
    runner = LangfuseLLMEvalRunner()
    runner.run_evals_on_recent_traces(limit=5)

    # Example 2: Run specific evals only
    # runner = LangfuseLLMEvalRunner(criteria=["helpfulness", "correctness"])
    # runner.run_evals_on_recent_traces(limit=5)

    # Example 3: Run evals on a specific trace
    # runner.run_evals_on_trace("your-trace-id-here")

    print("\n✅ All evaluations completed!")