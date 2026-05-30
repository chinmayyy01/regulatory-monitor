from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
# from langchain_openai import OpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

MAX_IMPACT_TEXT = 3000

class ImpactScore(BaseModel):
    impact_level: str = Field(
        description='HIGH, MEDIUM, or LOW'
    )
    affected_entities: str = Field(
        description='Who is affected'
    )
    deadline: str = Field(
        description='Compliance deadline or Not specified'
    )
    reason: str = Field(
        description='Why this impact level was assigned'
    )
    action_required: str = Field(
        description='Action compliance team must take'
    )
    
parser = PydanticOutputParser(pydantic_object=ImpactScore)

llm = ChatGroq(model='llama-3.1-8b-instant', temperature=0)
# llm = OpenAI(model='gpt-4o-mini', temperature=0)

SCORING_PROMPT = ChatPromptTemplate.from_messages([
    ('system', '''You are a senior compliance officer. Score the business impact of this regulatory circular.
        HIGH = Immediate action required; major operational change.
        MEDIUM = Moderate change; affects specific business lines.
        LOW = Informational; no immediate action needed.
        {format_instructions}
    '''),
    ('human','''
        Circular title: {title}
        Plain English summary: {summary}
        Full text excerpt: {text}
    ''')
])

scoring_chain = SCORING_PROMPT | llm | parser

def score_impact(title: str, summary: str, text: str) -> dict:
    try:
        result = scoring_chain.invoke({
            'title': title,
            'summary': summary,
            'text': text[:MAX_IMPACT_TEXT],
            'format_instructions':
                parser.get_format_instructions(),
        })
        return result.model_dump()
    
    except Exception as e:
        print(f'[IMPACT SCORER ERROR] {e}')
        return {
            'impact_level': 'UNKNOWN',
            'affected_entities': 'UNKNOWN',
            'deadline': 'UNKNOWN',
            'reason': 'Parsing failed',
            'action_required': 'Manual review required',
        }