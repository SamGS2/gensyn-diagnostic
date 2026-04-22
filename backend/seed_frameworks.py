"""
Seed Gensyn framework documents into Supabase with vector embeddings.
Run from the backend directory with venv activated:
    python seed_frameworks.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
BASE_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.services.rag import store_framework_document

# ============================================================
# FRAMEWORK DOCUMENTS
# Edit these to update what the diagnostic draws from.
# Each document should be a self-contained piece of framework content.
# Keep them focused — shorter documents retrieve more precisely.
# ============================================================

DOCUMENTS = [
    # --- CHALLENGE TYPE DEFINITIONS ---
    {
        "title": "Challenge Type: Connection",
        "category": "challenge_type",
        "content": """Connection challenges are about working together as a team. 
The team experiences silos, disengagement, or lack of trust. People may not know 
each other's work, don't communicate effectively, or have lost the sense of being 
on the same side. Connection is the most upstream challenge — if the team can't 
work together, nothing else functions.
Signs: low participation in meetings, information hoarding, us-vs-them dynamics, 
people working in isolation, lack of informal communication.""",
    },
    {
        "title": "Challenge Type: Clarity",
        "category": "challenge_type",
        "content": """Clarity challenges are about uniting multiple perspectives. 
People see the problem differently and there is no shared understanding of what's 
actually going on. Multiple valid viewpoints exist but they haven't been 
synthesized. The team may be talking past each other or solving different 
problems without realizing it.
Signs: circular discussions, people agreeing in meetings but acting differently 
afterward, repeated "I thought we decided..." conversations, different teams 
describing the same situation in different terms.""",
    },
    {
        "title": "Challenge Type: Coherence",
        "category": "challenge_type",
        "content": """Coherence challenges are about aligning to a shared purpose. 
The team understands the problem but isn't aligned on direction. Different 
priorities compete, there's no shared sense of what matters most, or the 
purpose has become unclear. People may be working hard but pulling in 
different directions.
Signs: competing priorities with no clear hierarchy, "everything is a priority" 
culture, strategic initiatives that contradict each other, people unable to 
explain why their work matters to the bigger picture.""",
    },
    {
        "title": "Challenge Type: Insight",
        "category": "challenge_type",
        "content": """Insight challenges are about surfacing new information. 
The team needs information they don't currently have. There are blind spots 
about customers, the market, their own operations, or emerging trends. 
Decisions are being made on assumptions rather than evidence.
Signs: surprises from customer feedback, competitors making moves the team 
didn't anticipate, internal processes that nobody has examined recently, 
"we've always done it this way" as a default response.""",
    },
    {
        "title": "Challenge Type: Experimentation",
        "category": "challenge_type",
        "content": """Experimentation challenges are about trying new ideas. 
The team has ideas or hypotheses but hasn't tested them. They may be stuck 
in analysis paralysis, afraid of failure, or lack a framework for running 
small tests. The culture may punish mistakes rather than learning from them.
Signs: lengthy planning cycles with no action, ideas discussed repeatedly 
without pilot testing, risk aversion, "perfect is the enemy of good" dynamics, 
innovation talked about but not practiced.""",
    },
    {
        "title": "Challenge Type: Execution",
        "category": "challenge_type",
        "content": """Execution challenges are about moving forward productively. 
The team knows what to do but can't make it happen. This may be due to resource 
constraints, capability gaps, structural blockers, or process inefficiencies. 
The plan exists but implementation stalls.
Signs: projects that start strong but stall, repeated missed deadlines, 
bottlenecks at specific people or approvals, good strategy with poor follow-through, 
people spending time on work that doesn't move priorities forward.""",
    },
    {
        "title": "Challenge Type: Momentum",
        "category": "challenge_type",
        "content": """Momentum challenges are about getting unstuck. The team was 
moving but has stalled. Energy is gone, progress has stopped, and people may 
feel defeated or disengaged. This often follows a failed initiative, a leadership 
change, or sustained overwork. The team needs a reset.
Signs: fatigue and cynicism, "we've tried that before" responses to new ideas, 
declining meeting attendance, good people leaving, a sense that things won't 
change no matter what.""",
    },
    
    # --- DYNAMIC DEFINITIONS ---
    {
        "title": "Dynamic: Internal",
        "category": "dynamic",
        "content": """Internal dynamics involve challenges rooted in the team, 
culture, or internal processes. The problem lives inside the organization — 
how people work together, how decisions get made, how information flows, 
or how the culture enables or blocks progress. External factors may exist 
but the primary lever for change is internal.
Signals: the challenge is described in terms of "we" and "our team", 
references to meetings, processes, reporting structures, team dynamics, 
leadership, or organizational culture.""",
    },
    {
        "title": "Dynamic: External",
        "category": "dynamic",
        "content": """External dynamics involve challenges driven by forces 
outside the organization — market shifts, customer behavior, competitive 
pressure, regulatory changes, or partner/supplier dynamics. The team needs 
to respond to or understand something outside their walls.
Signals: the challenge references customers, competitors, market trends, 
regulations, partnerships, supply chains, or external stakeholders.""",
    },
    {
        "title": "Dynamic: Transitional",
        "category": "dynamic",
        "content": """Transitional dynamics involve challenges arising from 
change, growth, or disruption. The organization is going through a shift — 
scaling, restructuring, entering new markets, adopting new technology, 
merging, or responding to a crisis. The challenge isn't the steady state 
but the transition itself.
Signals: references to change management, growth pains, "things used to 
work but don't anymore", new leadership, mergers, pivots, digital 
transformation, or "we're in a different phase now".""",
    },

    # --- WORKSHOP DESCRIPTIONS ---
    {
        "title": "Workshop: Lightning Decision Jam",
        "category": "workshop",
        "content": """The Lightning Decision Jam (LDJ) is a facilitated workshop 
in which a team quickly cuts through noise and competing perspectives to make 
a clear, confident decision on a specific topic or challenge. Clients leave 
with a decision that is made together, understood by all, and ready to act upon. 
Duration: half day (2-3 hours). Best fit for Clarity and Coherence challenges 
where the team needs to converge on a shared understanding or direction.""",
    },
    {
        "title": "Workshop: Gensyn Jumpstart",
        "category": "workshop",
        "content": """The Gensyn Jumpstart is a facilitated workshop in which a 
team builds shared clarity around a business issue — a strategic priority, 
stalled initiative, or persistent problem — and works together to define, 
create, and test a clear path forward. Clients leave aligned on their issue 
and energized around a path forward they created together. Duration: 4-6 hours. 
Best fit for Insight and Experimentation challenges where the team needs to 
surface new understanding or test new approaches.""",
    },
    {
        "title": "Workshop: Scenario Planning",
        "category": "workshop",
        "content": """Scenario Planning is a facilitated workshop in which a team 
examines plausible futures the organization might face, stress-testing current 
thinking to build foresight and flexibility for leading through uncertainty. 
Clients leave better equipped to make decisions today that hold up across 
tomorrow's possibilities. Duration: 4-6 hours. Best fit for Execution 
challenges in transitional contexts where the team needs to plan for 
multiple possible outcomes.""",
    },
    {
        "title": "Workshop: Customer Insights",
        "category": "workshop",
        "content": """Customer Insights is a facilitated workshop in which a team 
develops a more accurate understanding of the customers they serve by examining 
experiences, priorities, and needs, and testing assumptions. Clients leave with 
a clearer, more grounded picture of their customer they can act upon with 
confidence. Duration: 4-6 hours. Best fit for Insight challenges in external 
contexts where the team has blind spots about their customers or market.""",
    },
    {
        "title": "Workshop: Interactive Process Simulation",
        "category": "workshop",
        "content": """Interactive Process Simulation is a facilitated workshop in 
which a team physically builds and runs a model of a process or service that 
isn't meeting expectations, creating a shared picture of what actually happens 
and where opportunities reside. Clients leave with a team-owned understanding 
of what's needed and an agreed-upon solution. Duration: 4-6 hours. Best fit for 
Experimentation challenges in internal contexts where the team needs to 
prototype and test process improvements.""",
    },
    {
        "title": "Workshop: Games Event",
        "category": "workshop",
        "content": """Games Events use modified strategy and collaboration games 
(like Strategy Yahtzee, Wits & Bits & Wagers) to build team connection and 
develop strategic and critical thinking in a fun, low-pressure environment. 
Best fit for Connection challenges where the team needs to rebuild trust 
and rapport, or Execution challenges where the team needs to re-energize 
around working together productively. Duration: 90-120 minutes.""",
    },

    # --- UPSTREAM PRINCIPLE ---
    {
        "title": "The Upstream Principle",
        "category": "framework",
        "content": """Gensyn's upstream principle: challenges follow an order. 
Connection → Clarity → Coherence → Insight → Experimentation → Execution → Momentum. 
If a team has a Clarity problem, addressing Execution won't help — Clarity 
is upstream and must be resolved first. The diagnostic identifies the FIRST 
(most upstream) challenge that's broken. This is the primary recommendation. 
Downstream challenges may also exist but they often resolve or become clearer 
once the upstream challenge is addressed.""",
    },

    # --- SERVICE MATCHING RULES ---
    {
        "title": "Service Matching Rules",
        "category": "framework",
        "content": """Related services (primary recommendation based on challenge type):
- Connection → Games Event Workshop
- Clarity → Lightning Decision Jam
- Coherence → Lightning Decision Jam  
- Insight → Gensyn Jumpstart
- Experimentation → Gensyn Jumpstart
- Execution → Games Event Workshop or Scenario Planning
- Momentum → Gensyn Jumpstart

Special services (when challenge type + dynamic align specifically):
- Insight + External → Customer Insights Workshop
- Experimentation + Internal → Interactive Process Simulation
- Execution + Transitional → Scenario Planning

Special services are complementary — shown alongside the related service recommendation, not instead of it.""",
    },
]


def seed_all():
    """Seed all framework documents."""
    print(f"Seeding {len(DOCUMENTS)} framework documents...")
    
    for i, doc in enumerate(DOCUMENTS):
        print(f"  [{i+1}/{len(DOCUMENTS)}] {doc['title']}...")
        try:
            result = store_framework_document(
                title=doc["title"],
                category=doc["category"],
                content=doc["content"],
                metadata=doc.get("metadata"),
            )
            print(f"    ✓ Stored (id: {result['id'][:8]}...)")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    print("\nDone!")


def clear_all():
    """Clear all framework documents (use before re-seeding)."""
    from app.services.supabase_client import get_supabase
    supabase = get_supabase()
    supabase.table("framework_documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    print("Cleared all framework documents.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear", action="store_true", help="Clear all documents before seeding")
    args = parser.parse_args()
    
    if args.clear:
        clear_all()
    seed_all()
    