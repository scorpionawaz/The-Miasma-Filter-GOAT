# 🌀 Miasma Filter Agents
Agentic pipeline which constantly accumulates facts and updates the cache with recent information. It verifies the credibility of the incoming claim against the recently fetched information using a multi-agent system.
This system combines planning, research, evaluation, and storage agents to ensure only verified data is streamed to the user.

**📌 Process Flow**

Broadcaster sends stream → Supervisor checks if content is harmful or ambiguous.

If ambiguous → the fact checker pipeline validates the claim using external trend sources.

A Planning Loop creates and critiques a research plan until approved.

An Iterative Refinement Loop gathers evidence and builds a structured report.

Finalized report is stored in Redis and returned as a confidence-scored notification to viewers.


**🧩 Agents Breakdown**
*🔹 Planning & Approval Pipeline*

plan_creator_agent → drafts a research plan based on the claim.

plan_critic_agent → evaluates weaknesses in the plan and suggests improvements.

approval_checker → Stops the planning loop if the critic agent approves the plan

finalise_plan_agent → locks the approved plan for execution.

*🔹 Research & Iterative Refinement*

section_planner → breaks the plan into smaller researchable sections.

section_researcher → collects evidence for each section.

research_evaluator → validates collected evidence, ensures credibility.

escalation_checker → decides if more iterations are needed.

enhanced_search_executor → pulls deeper insights from the web using Google search.

report_composer → compiles all validated sections into a coherent research report.

*🔹 Storage & Reporting*

redis_storage_agent → stores the final structured report in Redis with metadata (content, created_at).

Reporter module → fetches Redis data and generates real-time notifications with a confidence score.

**⚙️ Tech Stack**

Python 3.10+

FastAPI (for APIs)

Redis (for storage)

Docker (containerized deployment)

Agent Development Kit (ADK)



**🐳 Running the Agent with Docker**
### 1️⃣ Clone the repo
```bash
git clone https://github.com/scorpionawaz/The-Miasma-Filter-GOAT.git
cd miasma_filter_agents
```
### 2️⃣ Build the Docker image
```bash
docker build -t miasma-filter .
```
### 3️⃣ Run the container
```bash
docker run -p 8000:8000 --env-file .env miasma-filter
```

👉 Note:

The container will look for .env in the repo root. Make sure you create one with required environment variables.

Example .env:
```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
API_KEY=your_api_key_here
```
Once the container is running, the API will be available at:
`http://localhost:8000`






