
import datetime
import logging
import re
from collections.abc import AsyncGenerator
from typing import Literal

from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.planners import BuiltInPlanner
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.genai import types as genai_types
from pydantic import BaseModel, Field
from .tools import save_report_to_redis, get_live_news_streams
from .config import config
from google.adk.agents import Agent
from google.adk.agents import SequentialAgent




class PlanEvaluation(BaseModel):
    """Structured output for the plan critic agent."""
    decision: Literal["approved", "revise"] = Field(
        description="'approved' if the plan is satisfactory, 'revise' if it needs changes."
    )
    feedback: str = Field(
        description="Detailed feedback for revision if the decision is 'revise'. State 'Plan looks good.' if approved."
    )

class SearchQuery(BaseModel):
    """Model representing a specific search query for web search."""

    search_query: str = Field(
        description="A highly specific and targeted query for web search."
    )


class Feedback(BaseModel):
    """Model for providing evaluation feedback on research quality."""

    grade: Literal["pass", "fail"] = Field(
        description="Evaluation result. 'pass' if the research is sufficient, 'fail' if it needs revision."
    )
    comment: str = Field(
        description="Detailed explanation of the evaluation, highlighting strengths and/or weaknesses of the research."
    )
    follow_up_queries: list[SearchQuery] | None = Field(
        default=None,
        description="A list of specific, targeted follow-up search queries needed to fix research gaps. This should be null or empty if the grade is 'pass'.",
    )


def collect_research_sources_callback(callback_context: CallbackContext) -> None:
    """Collects and organizes web-based research sources and their supported claims from agent events.

    This function processes the agent's `session.events` to extract web source details (URLs,
    titles, domains from `grounding_chunks`) and associated text segments with confidence scores
    (from `grounding_supports`). The aggregated source information and a mapping of URLs to short
    IDs are cumulatively stored in `callback_context.state`.

    Args:
        callback_context (CallbackContext): The context object providing access to the agent's
            session events and persistent state.
    """
    session = callback_context._invocation_context.session
    url_to_short_id = callback_context.state.get("url_to_short_id", {})
    sources = callback_context.state.get("sources", {})
    id_counter = len(url_to_short_id) + 1
    for event in session.events:
        if not (event.grounding_metadata and event.grounding_metadata.grounding_chunks):
            continue
        chunks_info = {}
        for idx, chunk in enumerate(event.grounding_metadata.grounding_chunks):
            if not chunk.web:
                continue
            url = chunk.web.uri
            title = (
                chunk.web.title
                if chunk.web.title != chunk.web.domain
                else chunk.web.domain
            )
            if url not in url_to_short_id:
                short_id = f"src-{id_counter}"
                url_to_short_id[url] = short_id
                sources[short_id] = {
                    "short_id": short_id,
                    "title": title,
                    "url": url,
                    "domain": chunk.web.domain,
                    "supported_claims": [],
                }
                id_counter += 1
            chunks_info[idx] = url_to_short_id[url]
        if event.grounding_metadata.grounding_supports:
            for support in event.grounding_metadata.grounding_supports:
                confidence_scores = support.confidence_scores or []
                chunk_indices = support.grounding_chunk_indices or []
                for i, chunk_idx in enumerate(chunk_indices):
                    if chunk_idx in chunks_info:
                        short_id = chunks_info[chunk_idx]
                        confidence = (
                            confidence_scores[i] if i < len(confidence_scores) else 0.5
                        )
                        text_segment = support.segment.text if support.segment else ""
                        sources[short_id]["supported_claims"].append(
                            {
                                "text_segment": text_segment,
                                "confidence": confidence,
                            }
                        )
    callback_context.state["url_to_short_id"] = url_to_short_id
    callback_context.state["sources"] = sources


def citation_replacement_callback(
    callback_context: CallbackContext,
) -> genai_types.Content:
    """Replaces citation tags in a report with Markdown-formatted links.

    Processes 'final_cited_report' from context state, converting tags like
    `<cite source="src-N"/>` into hyperlinks using source information from
    `callback_context.state["sources"]`. Also fixes spacing around punctuation.

    Args:
        callback_context (CallbackContext): Contains the report and source information.

    Returns:
        genai_types.Content: The processed report with Markdown citation links.
    """
    final_report = callback_context.state.get("final_cited_report", "")
    sources = callback_context.state.get("sources", {})

    def tag_replacer(match: re.Match) -> str:
        short_id = match.group(1)
        if not (source_info := sources.get(short_id)):
            logging.warning(f"Invalid citation tag found and removed: {match.group(0)}")
            return ""
        display_text = source_info.get("title", source_info.get("domain", short_id))
        return f" [{display_text}]({source_info['url']})"

    processed_report = re.sub(
        r'<cite\s+source\s*=\s*["\']?\s*(src-\d+)\s*["\']?\s*/>',
        tag_replacer,
        final_report,
    )
    processed_report = re.sub(r"\s+([.,;:])", r"\1", processed_report)
    callback_context.state["final_report_with_citations"] = processed_report
    return genai_types.Content(parts=[genai_types.Part(text=processed_report)])


class EscalationChecker(BaseAgent):
    """Checks research evaluation and escalates to stop the loop if grade is 'pass'."""

    def __init__(self, name: str):
        super().__init__(name=name)

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        evaluation_result = ctx.session.state.get("research_evaluation")
        if evaluation_result and evaluation_result.get("grade") == "pass":
            logging.info(
                f"[{self.name}] Research evaluation passed. Escalating to stop loop."
            )
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            logging.info(
                f"[{self.name}] Research evaluation failed or not found. Loop will continue."
            )
            # Yielding an event without content or actions just lets the flow continue.
            yield Event(author=self.name)


plan_generator = LlmAgent(
    model=config.worker_model,
    name="plan_generator",
    description="Generates or refine the existing 5 line action-oriented research plan, using minimal search only for topic clarification.",
    instruction=f"""
    You are a research strategist. Your job is to create a high-level RESEARCH PLAN, not a summary. If there is already a RESEARCH PLAN in the session state,
    improve upon it based on the user feedback.#add agent feedback

    RESEARCH PLAN(SO FAR):
    {{ research_plan? }}

    **GENERAL INSTRUCTION: CLASSIFY TASK TYPES**
    Your plan must clearly classify each goal for downstream execution. Each bullet point should start with a task type prefix:
    - **`[RESEARCH]`**: For goals that primarily involve information gathering, investigation, analysis, or data collection (these require search tool usage by a researcher).
    - **`[DELIVERABLE]`**: For goals that involve synthesizing collected information, creating structured outputs (e.g., tables, charts, summaries, reports), or compiling final output artifacts (these are executed AFTER research tasks, often without further search).

    **INITIAL RULE: Your initial output MUST start with a bulleted list of 5 action-oriented research goals or key questions, followed by any *inherently implied* deliverables.**
    - All initial 5 goals will be classified as `[RESEARCH]` tasks.
    - A good goal for `[RESEARCH]` starts with a verb like "Analyze," "Identify," "Investigate."
    - A bad output is a statement of fact like "The event was in April 2024."
    - **Proactive Implied Deliverables (Initial):** If any of your initial 5 `[RESEARCH]` goals inherently imply a standard output or deliverable (e.g., a comparative analysis suggesting a comparison table, or a comprehensive review suggesting a summary document), you MUST add these as additional, distinct goals immediately after the initial 5. Phrase these as *synthesis or output creation actions* (e.g., "Create a summary," "Develop a comparison," "Compile a report") and prefix them with `[DELIVERABLE][IMPLIED]`.

    **REFINEMENT RULE**:
    - **Integrate Feedback & Mark Changes:** When incorporating user feedback, make targeted modifications to existing bullet points. Add `[MODIFIED]` to the existing task type and status prefix (e.g., `[RESEARCH][MODIFIED]`). If the feedback introduces new goals:
        - If it's an information gathering task, prefix it with `[RESEARCH][NEW]`.
        - If it's a synthesis or output creation task, prefix it with `[DELIVERABLE][NEW]`.
    - **Proactive Implied Deliverables (Refinement):** Beyond explicit user feedback, if the nature of an existing `[RESEARCH]` goal (e.g., requiring a structured comparison, deep dive analysis, or broad synthesis) or a `[DELIVERABLE]` goal inherently implies an additional, standard output or synthesis step (e.g., a detailed report following a summary, or a visual representation of complex data), proactively add this as a new goal. Phrase these as *synthesis or output creation actions* and prefix them with `[DELIVERABLE][IMPLIED]`.
    - **Maintain Order:** Strictly maintain the original sequential order of existing bullet points. New bullets, whether `[NEW]` or `[IMPLIED]`, should generally be appended to the list, unless the user explicitly instructs a specific insertion point.
    - **Flexible Length:** The refined plan is no longer constrained by the initial 5-bullet limit and may comprise more goals as needed to fully address the feedback and implied deliverables.

    **TOOL USE IS STRICTLY LIMITED:**
    Your goal is to create a generic, high-quality plan *without searching*.
    Only use `google_search` if a topic is ambiguous or time-sensitive and you absolutely cannot create a plan without a key piece of identifying information.
    You are explicitly forbidden from researching the *content* or *themes* of the topic. That is the next agent's job. Your search is only to identify the subject, not to investigate it.
    Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}
    """,
    tools=[google_search],
)


section_planner = LlmAgent(
    model=config.worker_model,
    name="section_planner",
    description="Breaks down the research plan into a structured markdown outline of report sections.",
    instruction="""
    You are an expert report architect. Using the research topic and the plan from the 'research_plan' state key, design a logical structure for the final report.
    Note: Ignore all the tag nanes ([MODIFIED], [NEW], [RESEARCH], [DELIVERABLE]) in the research plan.
    Your task is to create a markdown outline with 4-6 distinct sections that cover the topic comprehensively without overlap.
    You can use any markdown format you prefer, but here's a suggested structure:
    # Section Name
    A brief overview of what this section covers
    Feel free to add subsections or bullet points if needed to better organize the content.
    Make sure your outline is clear and easy to follow.
    Do not include a "References" or "Sources" section in your outline. Citations will be handled in-line.
    """,
    output_key="report_sections",
)


section_researcher = LlmAgent(
    model=config.worker_model,
    name="section_researcher",
    description="Performs the crucial first pass of web research for latest and relevant news",
    planner=BuiltInPlanner(
        thinking_config=genai_types.ThinkingConfig(include_thoughts=True)
    ),
    instruction="""
    You are a specialist news research agent. Your task is to execute a research plan to find **ONLY the most recent news updates.**

    **CRITICAL INSTRUCTION: TIME SENSITIVITY**
    - You **MUST** filter all information to events and reports from the **recent updates**.
    - The goal is a snapshot of *today's* news.

    **Phase 1: Information Gathering (`[RESEARCH]` Tasks)**
    *   For each `[RESEARCH]` goal:
        *   **Query Generation:** Formulate 4-5 targeted search queries.
            *   **GOOD EXAMPLE:** `"Maharashtra political developments today site:thehindu.com OR site:timesofindia.indiatimes.com"`
            *   **GOOD EXAMPLE:** `"LATEST news on Eknath Shinde site:indianexpress.com"`
            *   **BAD EXAMPLE:** `"History of Maharashtra politics"`
        *   **Execution:** Use the `google_search` tool to execute all queries.
            **Output : ** It should be a detailed report about the key updates in the topic.
        *   **Internal Storage:** Store the time-filtered summary for use in Phase 2.

    **Phase 2: Synthesis and Output Creation (`[DELIVERABLE]` Tasks)**
    *   Use the **filtered summaries** you created in Phase 1 to build the deliverables.
    *   Ensure the final output reflects only the recent events and news.
    """,
    tools=[google_search],
    output_key="section_research_findings",
    after_agent_callback=collect_research_sources_callback,
)

research_evaluator = LlmAgent(
    model=config.critic_model,
    name="research_evaluator",
    description="Critically evaluates research and generates follow-up queries.",
    instruction=f"""
    You are a meticulous quality assurance analyst evaluating the research findings in 'section_research_findings'.

    **CRITICAL RULES:**
    1. Assume the given research topic is correct. Do not question or try to verify the subject itself.
    2. Your ONLY job i
    omprehensiveness of coverage, logical flow and organization, use of credible sources, depth of analysis, and clarity of explanations.
    4. Do NOT fact-check or question the fundamental premise or timeline of the topic.
    5. If suggesting follow-up queries, they should dive deeper into the existing topic, not question its validity.

    Be very critical about the QUALITY of research. If you find significant gaps in depth or coverage, assign a grade of "fail",
    write a detailed comment about what's missing, and generate 5-7 specific follow-up queries to fill those gaps.
    If the research thoroughly covers the topic, grade "pass".

    Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}
    Your response must be a single, raw JSON object validating against the 'Feedback' schema.
    """,
    output_schema=Feedback,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_key="research_evaluation",
)

enhanced_search_executor = LlmAgent(
    model=config.worker_model,
    name="enhanced_search_executor",
    description="Executes follow-up searches and integrates new findings.",
    planner=BuiltInPlanner(
        thinking_config=genai_types.ThinkingConfig(include_thoughts=True)
    ),
    instruction="""
    You are a specialist researcher executing a refinement pass.
    You have been activated because the previous research was graded as 'fail'.

    1.  Review the 'research_evaluation' state key to understand the feedback and required fixes.
    2.  Execute EVERY query listed in 'follow_up_queries' using the 'google_search' tool.
    3.  Synthesize the new findings and COMBINE them with the existing information in 'section_research_findings'.
    4.  Your output MUST be the new, complete, and improved set of research findings.
    """,
    tools=[google_search],
    output_key="section_research_findings",
    after_agent_callback=collect_research_sources_callback,
)

report_composer = LlmAgent(
    model=config.critic_model,
    name="report_composer_with_citations",
    include_contents="none",
    description="Transforms research data and a markdown outline into a final, cited report.",
    instruction="""
    You are a breaking news editor. Your task is to compile a **detailed news article**

    ---
    ### INPUT DATA
    *   Research Findings: `{section_research_findings}`
    *   Report Structure: `{report_sections}`

    ---
    ### CRITICAL INSTRUCTIONS
    1.  **Elaborate, do not summarize.** Provide as much detail as the recent sources allow.
    2.  **Citation System:** To cite a source, you MUST insert the tag `<cite source="src-ID_NUMBER" />` immediately after the claim it supports.
    3.  **Structure:** Strictly follow the markdown outline from the **Report Structure**.
    4.  Maintain a neutral, journalistic tone suitable for breaking news.
    5.  Do not include a "References" or "Sources" section.
    """,
    output_key="final_cited_report",
    after_agent_callback=citation_replacement_callback,
)

research_pipeline = SequentialAgent(
    name="research_pipeline",
    description="Executes a pre-approved research plan. It performs iterative research, evaluation, and composes a final, cited report.",
    sub_agents=[
        section_planner,
        section_researcher,
        LoopAgent(
            name="iterative_refinement_loop",
            max_iterations=config.max_search_iterations,
            sub_agents=[
                research_evaluator,
                EscalationChecker(name="escalation_checker"),
                enhanced_search_executor,
            ],
        ),
        report_composer,
    ],
)



youtube_trends_extractor = Agent(
    name = "Youtube_trends_extractor",
    model = "gemini-2.0-flash",
    description="Extracts topics from the description of the Youtube stream metadata",
    instruction="""
            You will be doing a tool call which extracts YouTube livestream metadata in JSON format.
            Your task is to extract the key topics being discussed in the livestream.
            Focus only on the main subjects from the title and description, and ignore repetitive 
            or irrelevant words like "LIVE," "watching," "channel," or formatting artifacts.
            EXAMPLE INPUT:
            {
            "title": "NDTV 24x7 LIVE TV: PM Modi Birthday Today News | BMW Car Accident | PM Modi In MP | PM Modi LIVE",
            "channel": "NDTV",
            "is_live": true,
            "view_count": "426 watching",
            "duration": "",
            "published_time": "",
            "url": "https://www.youtube.com/watch?v=viQwbrjRIj4",
            "description": "Amid trade tensions, negotiations and a thaw, Trump wishes PM Modi on birthday.Prime Minister Narendra Modi thanked US ...",
            "thumbnail": "https://i.ytimg.com/vi/viQwbrjRIj4/hq720.jpg?v=68ca0a58&sqp=-oaymwEcCNAFEJQDSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLBgqop6kZhW3jt1v_HY7jQLXxXk7Q"
            "description": "TV9Kannada #DharmasthalaCase #MaskedmanChinnayya #Chinnayya #bbk12 #biggboss12 #DharmasthalaSITProbe ...",
            "thumbnail": "https://i.ytimg.com/vi/jdJoOhqCipA/hq720.jpg?v=689f220f&sqp=-oaymwEcCNAFEJQDSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLCuZ1yMJ-lSn7OXqgZN86PrhANj3g"
        }
        EXPECTED OUTPUT: 
            {
            "topics": [
                "PM Modi Birthday",
                "BMW Car Accident",
                "PM Modi Visit to Madhya Pradesh",
                "US-India Trade Tensions",
                "Donald Trump Birthday Wishes to PM Modi"
                ]
            }


        """,
    tools=[get_live_news_streams],
    output_key="yt_trends"
)


plan_critic_agent = LlmAgent(
    name="plan_critic_agent",
    model=config.critic_model, 
    description="Evaluates a draft research plan and decides whether to approve it or send it for revision.",
    instruction="""
    You are a meticulous Research Manager. Your sole task is to evaluate the provided DRAFT RESEARCH PLAN.
    
    DRAFT RESEARCH PLAN:
    {draft_research_plan}
    CRITICAL POINT : Use each and every topic from {yt_trends} and analyse whether {draft_research_plan} covers these topics strictly
    Your evaluation criteria are:
    1.  **Completeness:** Does the plan address all the topics provided in the initial request?
    2.  **Actionability:** Do all [RESEARCH] tasks start with a strong action verb (e.g., "Investigate," "Analyze," "Compare")?
    3.  **Clarity:** Is the plan clear, concise, and logically structured?
    4.  **Format:** Are all research goals correctly prefixed with `[RESEARCH]`?

    Based on these criteria, you must make a decision.
    - If the plan is excellent and meets all criteria, set `decision` to "approved".
    - If the plan has any flaws (e.g., it is a statement of fact, not a plan; it is too vague; it misses a topic), set `decision` to "revise" and provide specific, actionable feedback on how to fix it.

    Your output MUST be a single JSON object that validates against the `PlanEvaluation` schema.

    
    """,
    output_schema=PlanEvaluation,
    output_key="plan_evaluation",
)

plan_creator_agent = LlmAgent(
    name="plan_creator_agent",
    model=config.worker_model,
    description="Creates or revises a research plan based on topics and critic feedback.",
    instruction="""
    You are a research planner. Your task is to generate a research plan.

    TOPICS TO COVER:
    {yt_trends}

    CRITIC FEEDBACK (revise if provided):
    {plan_evaluation.feedback?}

    Based on the topics and any feedback, use the `plan_generator` tool to create a research plan.
    If there is feedback, you MUST incorporate it to improve the plan.
    """,
    tools=[AgentTool(plan_generator)],
    output_key="draft_research_plan",
    
)

finalize_plan_agent = LlmAgent(
    name="finalize_plan_agent",
    model="gemini-1.5-flash", 
    instruction="""
    The content of the approved DRAFT RESEARCH PLAN is provided below.
    Your only task is to copy this content exactly as it is. Do not change anything.

    DRAFT RESEARCH PLAN:
    {draft_research_plan}
    """,
    output_key="research_plan"
)

class ApprovalChecker(BaseAgent):
    """Stops the planning loop if the critic agent approves the plan."""
    def __init__(self, name: str):
        super().__init__(name=name)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        evaluation = ctx.session.state.get("plan_evaluation")
        if evaluation and evaluation.get("decision") == "approved":
            logging.info(f"[{self.name}] Plan approved by critic. Escalating to stop loop.")
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            logging.info(f"[{self.name}] Plan needs revision. Loop will continue.")
            yield Event(author=self.name)



redis_storage_agent = LlmAgent(
    name="redis_storage_agent",
    model=config.worker_model,
    description="Saves the final research report and metadata to a Redis database.",
    instruction="""
    Your sole purpose is to archive the completed research report by calling the `save_report_to_redis` tool.

    You MUST use the exact data provided below to call the tool. Do not modify or summarize it.

    --- DATA BLOCK ---
    REPORT CONTENT:
    {final_cited_report}

    RESEARCH PLAN:
    {research_plan}

    SOURCES:
    {sources}
    --- END DATA BLOCK ---

    Now, call the `save_report_to_redis` tool with the three pieces of data from the DATA BLOCK above as arguments.
    """,
    tools=[save_report_to_redis],
   
   
)

root_agent = SequentialAgent(
    name="AutomatedResearchPipeline",
    description="A fully automated pipeline that extracts topics, iteratively creates and approves a plan, executes research, and saves the result.",
    sub_agents=[
       
        youtube_trends_extractor,
        LoopAgent(
            name="planning_and_approval_loop",
            max_iterations=3, 
            sub_agents=[
                plan_creator_agent,
                plan_critic_agent,
                ApprovalChecker(name="approval_checker"),
            ],
        ),
        finalize_plan_agent,
        research_pipeline,
        redis_storage_agent,
    ],
)